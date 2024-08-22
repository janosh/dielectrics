"""Exploratory data analysis of this work's high-throughput DFPT data."""

# %% from https://colab.research.google.com/drive/131MZKKeOhoseoVTJmPuOXVJvDoNes1ge
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pymatviz as pmv
from pymatgen.core import Composition

from dielectrics import DATA_DIR, PAPER_FIGS, Key
from dielectrics.db.fetch_data import df_diel_from_task_coll


os.makedirs(f"{PAPER_FIGS}/ptable/", exist_ok=True)


def rgb_color(val: float, max: float) -> str:  # noqa: A002
    """Convert a value between 0 and max to a color between red and blue."""
    return f"rgb({255 * val / max:.1f}, 0, {255 * (max - val) / max:.1f})"


# %%
df_us = df_diel_from_task_coll({}, cache=False)
assert len(df_us) == 2552, f"Expected 2532 materials, got {len(df_us)}"
df_us = df_us.rename(columns={"spacegroup.crystal_system": Key.crystal_sys})


# filter out rows with diel_elec > 100 since those seem untrustworthy
# in particular wbm-4-26188 with eps_elec = 515 and mp-865145 with eps_elec = 809
# (see table-fom-pbe-gt-350.pdf)
df_us = df_us.query(f"{Key.diel_elec_pbe} < 100")
assert len(df_us) == 2542, f"Expected 2522 materials, got {len(df_us)}"

# load MP data
df_mp = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-train.json.bz2")


# %% get DFPT counts by structure origin (MP, WBM, element substitution)
n_dfpt_total = len(df_us)
print(f"{n_dfpt_total=:,}")

n_dfpt_elem_sub = df_us.index.str.contains("->").sum()
print(f"{n_dfpt_elem_sub=:,}")

n_dfpt_mp = (
    df_us.index.str.startswith(("mp-", "mvc-")) & ~df_us.index.str.contains("->")
).sum()
print(f"{n_dfpt_mp=:,}")

n_dfpt_wbm = (
    df_us.index.str.startswith("wbm-") & ~df_us.index.str.contains("->")
).sum()
print(f"{n_dfpt_wbm=:,}")

assert n_dfpt_total == n_dfpt_elem_sub + n_dfpt_mp + n_dfpt_wbm, (
    f"Expected {n_dfpt_total} total DFPT materials, got "
    f"{n_dfpt_elem_sub + n_dfpt_mp + n_dfpt_wbm}."
)


# %% recreate figure 3 from Atomate Dielectric paper https://rdcu.be/clY2X with MP
# dielectric data
df_melted = df_us.query("0 < diel_total_pbe < 1000").melt(
    id_vars=[Key.crystal_sys, Key.mat_id, Key.formula],
    value_vars=[Key.diel_elec_pbe, Key.diel_ionic_pbe],
    var_name="component",
    value_name="dielectric constant",
    ignore_index=False,
)

df_melted["component"] = df_melted.component.map(
    {Key.diel_elec_pbe: "electronic", Key.diel_ionic_pbe: "ionic"}
)
cry_sys_order = (
    "cubic hexagonal trigonal tetragonal orthorhombic monoclinic triclinic".split()
)


# %%
fig = px.violin(
    df_melted,
    x=Key.crystal_sys,
    y="dielectric constant",
    color="component",
    color_discrete_map={"electronic": "blue", "ionic": "green"},
    labels={Key.crystal_sys: "crystal system"},
    hover_data=dict(material_id=True, formula=True),
    template=pmv.pmv_white_template,
    # sort strips from high to low spacegroup number
    category_orders={Key.crystal_sys: cry_sys_order},
    height=500,
    width=1200,
).update_traces(jitter=1)

fig.layout.margin.update(l=30, r=30, t=30, b=30)
fig.layout.legend.update(x=1, y=1, xanchor="right")

df_us = df_us.sort_values(Key.crystal_sys, key=lambda col: col.map(cry_sys_order.index))

n_top, x_ticks = 30, dict.fromkeys(cry_sys_order, "")
for cry_sys, df_group in df_us.groupby(Key.crystal_sys):
    ionic_top = df_group[Key.diel_ionic_pbe].nlargest(n_top).mean()
    elec_top = df_group[Key.diel_elec_pbe].nlargest(n_top).mean()
    ionic_clr = rgb_color(ionic_top, 261)
    elec_clr = rgb_color(elec_top, 102)
    x_ticks[cry_sys] = (
        f"<b>{cry_sys}</b><br>{len(df_group):,} = {len(df_group) / len(df_us):.0%}"
        f"<br><span style='color:{elec_clr}'><b>{elec_top:.0f}</b></span>      "
        f"<span style='color:{ionic_clr}'><b>{ionic_top:.0f}</b></span>"
    )

fig.layout.xaxis.update(tickvals=list(range(7)), ticktext=list(x_ticks.values()))

fig.show()
# img_path = f"{PAPER_FIGS}/our-diel-elec-vs-ionic-violin-alternate.pdf"
# pmv.io.save_fig(fig, img_path, width=900, height=400)


# %%
fig = go.Figure()

common_kwds = dict(points=False, spanmode="hard", meanline_visible=True, width=0.9)
for crystal_sys, df_group in df_us.groupby(Key.crystal_sys):
    common_kwds["x"] = df_group[Key.crystal_sys]
    common_kwds["legendgroup"] = crystal_sys
    common_kwds["showlegend"] = crystal_sys == "cubic"

    fig.add_violin(  # ionic dielectric distribution
        y=df_group[Key.diel_ionic_pbe],
        scalegroup="ionic",
        name="ionic",
        side="positive",
        line_color="orange",
        **common_kwds,
    )
    fig.add_violin(  # electronic dielectric distribution
        y=df_group[Key.diel_elec_pbe],
        scalegroup="electronic",
        name="electronic",
        side="negative",
        line_color="blue",
        **common_kwds,
    )


n_top, x_ticks = 30, dict.fromkeys(cry_sys_order, "")
for cry_sys, df_group in df_us.groupby(Key.crystal_sys):
    ionic_top = df_group[Key.diel_ionic_pbe].nlargest(n_top).mean()
    elec_top = df_group[Key.diel_elec_pbe].nlargest(n_top).mean()
    ionic_clr = rgb_color(ionic_top, 261)
    elec_clr = rgb_color(elec_top, 102)
    x_ticks[cry_sys] = (
        f"<b>{cry_sys}</b><br>{len(df_group):,} = {len(df_group) / len(df_us):.0%}"
        f"<br><span style='color:{elec_clr}'><b>{elec_top:.0f}</b></span>      "
        f"<span style='color:{ionic_clr}'><b>{ionic_top:.0f}</b></span>"
    )
fig.layout.xaxis.update(
    tickvals=list(range(7)),
    ticktext=list(x_ticks.values()),
    # increase tick font size
    tickfont=dict(size=14),
)
fig.layout.legend.update(
    x=0.5,
    y=1.12,
    xanchor="center",
    bgcolor="rgba(0,0,0,0)",
    font_size=16,
    orientation="h",
    traceorder="reversed",
)

fig.layout.update(violingap=0, violinmode="overlay", width=900, height=400)
fig.layout.margin.update(l=0, r=0, t=0, b=0)
fig.layout.xaxis.title.update(text="crystal system", font_size=18)
fig.layout.yaxis.update(range=[0, 80])
fig.layout.yaxis.title.update(text="ε<sub>elec / ionic</sub>", font_size=18)

fig.show()

pmv.io.save_fig(fig, f"{PAPER_FIGS}/our-diel-elec-vs-ionic-violin.pdf")


# %%
df_us.attrs.update(name="us", label="This Work")
df_mp.attrs.update(name="mp", label="MP Data")

for df in (df_us, df_mp):
    ax = pmv.ptable_heatmap(
        df[Key.formula],
        exclude_elements=("O", "F"),
        colorscale="viridis",
        zero_color="white",
        count_mode="occurrence",
        cbar_title=f"Element Occurrence (total={len(df):,})",
        label_font_size=18,
        value_font_size=18,
        fmt=".0f",
    )

    pmv.io.save_fig(
        ax, f"{PAPER_FIGS}/ptable/ptable-elem-counts-{df.attrs['name']}.pdf"
    )


# %%
us_elem_counts = pmv.count_elements(df_us[Key.formula])
mp_elem_counts = pmv.count_elements(df_mp[Key.formula])
# normalize by number of materials
us_elem_counts /= len(df_us)
mp_elem_counts /= len(df_mp)
ax = pmv.ptable_heatmap_ratio(
    us_elem_counts,
    mp_elem_counts,
    not_in_numerator=("white", ""),
    not_in_denominator=("white", ""),
    not_in_either=("#eff", ""),
    colorscale="viridis",
    label_font_size=18,
    value_font_size=16,
)
pmv.io.save_fig(ax, f"{PAPER_FIGS}/ptable/ptable-elem-ratio-us-vs-mp.pdf")


# %% project FoM onto periodic table
frac_comp_col = "fractional composition"
df_us[frac_comp_col] = [Composition(comp).as_dict() for comp in df_us[Key.formula]]

df_frac_comp = pd.DataFrame(df_us[frac_comp_col].tolist())
# ignore compositions amounts, count only element occurrence
df_frac_comp = df_frac_comp.where(df_frac_comp.isna(), 1)

for col, title in (
    (Key.fom_pbe, r"$\mathbf{\Phi_M}$"),
    (Key.diel_ionic_pbe, r"$\mathbf{\epsilon}_\text{ionic}$"),
    (Key.diel_elec_pbe, r"$\mathbf{\epsilon}_\text{electronic}$"),
    (Key.bandgap_pbe, r"$\mathbf{E}_\text{gap}$ (eV)"),
):
    df_per_elem = df_frac_comp * df_us[col].to_numpy()[:, None]
    srs_per_elem = df_per_elem.mean(axis=0)
    srs_per_elem.index.name = f"Element-projected {title}"

    ax = pmv.ptable_heatmap(
        srs_per_elem.dropna(),
        colorscale="viridis",
        cbar_title=srs_per_elem.index.name,
        label_font_size=18,
        value_font_size=18,
        fmt=".0f",
    )
    pmv.io.save_fig(
        ax, f"{PAPER_FIGS}/ptable/ptable-per-elem-{col.replace('_', '-')}.pdf"
    )


# %% export LaTeX table of all data points with FoM > fom_tresh for SI
col_name_map = {
    Key.mat_id: "Material ID",
    Key.formula: "Formula",
    "spacegroup.number": "Spacegroup",
}
fom_tresh = 350
tex_col_names = {
    Key.diel_elec_pbe: r"$\epsilon_\text{elec}$",
    Key.diel_ionic_pbe: r"$\epsilon_\text{ionic}$",
    Key.diel_total_pbe: r"$\epsilon_\text{total}$",
    Key.bandgap_pbe: "Band Gap (eV)",
    Key.fom_pbe: r"$\fom$ (eV)",
    "nsites": "atoms",
    "nelements": "elements",
}
keep_cols = [*col_name_map, *tex_col_names]
df_high_fom = df_us[df_us[Key.fom_pbe] > fom_tresh][keep_cols]
df_high_fom[Key.bandgap_pbe] = df_us[Key.bandgap_pbe].fillna(df_us[Key.bandgap_us])

df_high_fom = df_high_fom.sort_values(Key.fom_pbe, ascending=False).reset_index(
    drop=True
)
df_high_fom.index += 1  # start index at 1, must come after reset_index

print(f"Number of materials with FoM > {fom_tresh} eV: {len(df_high_fom)}")

# Export to LaTeX table (unused, hence commented out)
latex_table = df_high_fom.rename(columns=tex_col_names | col_name_map).to_latex(
    index=False, escape=False, float_format="%.2f"
)
# with open(f"{PAPER_FIGS}/table-fom-pbe-gt-{fom_tresh}.tex", "w") as file:
#     file.write(latex_table)


# %% export same table as pandas Styler with background gradient highlighting
# high values of FoM, bandgap and dielectric constant
float_cols = {
    Key.diel_elec_pbe: "ε<sub>elec</sub>",
    Key.bandgap_pbe: "E<sub>gap</sub> (eV)",
}
int_cols = {
    Key.diel_ionic_pbe: "ε<sub>ionic</sub>",
    Key.diel_total_pbe: "ε<sub>total</sub>",
    Key.fom_pbe: "𝚽<sub>M</sub> (eV)",
    "nsites": "n<sub>sites</sub>",
    "nelements": "n<sub>elems</sub>",
}
styler = (
    df_high_fom.rename(columns=float_cols | int_cols | col_name_map)
    .style.background_gradient(
        subset=list((float_cols | int_cols).values()), cmap="viridis"
    )
    .format(
        # render some cols without decimal places
        dict.fromkeys(int_cols.values(), "{:,.0f}"),
        precision=2,  # render floats with 2 decimals
        na_rep="",  # render NaNs as empty string
    )
)

pmv.io.df_to_pdf(styler, f"{PAPER_FIGS}/table-fom-pbe-gt-{fom_tresh}.pdf", size="100cm")
df_high_fom.to_csv(f"{DATA_DIR}/our-data-with-fom-pbe-gt-{fom_tresh}.csv", index=False)
styler.set_caption(f"Table of materials with 𝚽<sub>M</sub> > {fom_tresh} eV")


# %% inspect non-oxides
styler.data.query("~Formula.str.contains('O')")


# %%
pmv.ptable_heatmap_plotly(df_high_fom[Key.formula], exclude_elements="O")
