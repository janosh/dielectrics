"""Exploratory data analysis of this work's high-throughput DFPT data."""


# %% from https://colab.research.google.com/drive/131MZKKeOhoseoVTJmPuOXVJvDoNes1ge
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymatgen.core import Composition
from pymatviz import (
    count_elements,
    ptable_heatmap,
    ptable_heatmap_plotly,
    ptable_heatmap_ratio,
)
from pymatviz.io import df_to_pdf, save_fig

from dielectrics import (
    DATA_DIR,
    PAPER_FIGS,
    bandgap_pbe_col,
    crystal_sys_col,
    diel_elec_pbe_col,
    diel_ionic_pbe_col,
    diel_total_pbe_col,
    fom_pbe_col,
    id_col,
)
from dielectrics.db.fetch_data import df_diel_from_task_coll


def rgb_color(val: float, max: float) -> str:  # noqa: A002
    """Convert a value between 0 and max to a color between red and blue."""
    return f"rgb({255 * val / max:.1f}, 0, {255 * (max - val) / max:.1f})"


# %%
df_us = df_diel_from_task_coll({})
df_us = df_us.rename(columns={"spacegroup.crystal_system": crystal_sys_col})


# filter out rows with diel_elec > 100 since those seem untrustworthy
# in particular wbm-4-26188 with eps_elec = 515 and mp-865145 with eps_elec = 809
# (see table-fom-pbe-gt-350.pdf)
df_us = df_us.query(f"{diel_elec_pbe_col} < 100")
df_us = df_us[~df_us.index.duplicated()]

# load MP data
df_mp = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-train.json.bz2")


# %% recreate figure 3 from Atomate Dielectric paper https://rdcu.be/clY2X with MP
# dielectric data
df_melted = df_us.query("0 < diel_total_pbe < 1000").melt(
    id_vars=[crystal_sys_col, id_col, "formula"],
    value_vars=[diel_elec_pbe_col, diel_ionic_pbe_col],
    var_name="component",
    value_name="dielectric constant",
    ignore_index=False,
)

df_melted["component"] = df_melted.component.map(
    {diel_elec_pbe_col: "electronic", diel_ionic_pbe_col: "ionic"}
)
cry_sys_order = (
    "cubic hexagonal trigonal tetragonal orthorhombic monoclinic triclinic".split()
)


# %%
fig = px.violin(
    df_melted,
    x=crystal_sys_col,
    y="dielectric constant",
    color="component",
    color_discrete_map={"electronic": "blue", "ionic": "green"},
    labels={crystal_sys_col: "crystal system"},
    hover_data=dict(material_id=True, formula=True),
    template="plotly_white",
    # sort strips from high to low spacegroup number
    category_orders={crystal_sys_col: cry_sys_order},
    height=500,
    width=1200,
).update_traces(jitter=1)

fig.layout.margin.update(l=30, r=30, t=30, b=30)
fig.layout.legend.update(x=1, y=1, xanchor="right")

df_us = df_us.sort_values(crystal_sys_col, key=lambda col: col.map(cry_sys_order.index))

n_top, x_ticks = 30, {x: "" for x in cry_sys_order}
for cry_sys, df_group in df_us.groupby(crystal_sys_col):
    ionic_top = df_group[diel_ionic_pbe_col].nlargest(n_top).mean()
    elec_top = df_group[diel_elec_pbe_col].nlargest(n_top).mean()
    ionic_clr = rgb_color(ionic_top, 261)
    elec_clr = rgb_color(elec_top, 102)
    x_ticks[cry_sys] = (
        f"<b>{cry_sys}</b><br>{len(df_group):,} = {len(df_group)/len(df_us):.0%}"
        f"<br><span style='color:{elec_clr}'><b>{elec_top:.0f}</b></span>      "
        f"<span style='color:{ionic_clr}'><b>{ionic_top:.0f}</b></span>"
    )

fig.layout.xaxis.update(tickvals=list(range(7)), ticktext=list(x_ticks.values()))

fig.show()
img_path = f"{PAPER_FIGS}/our-diel-elec-vs-ionic-violin.pdf"
# save_fig(fig, img_path, width=900, height=400)


# %%
fig = go.Figure()

common_kwds = dict(points=False, spanmode="hard", meanline_visible=True, width=0.9)
for crystal_sys, df_group in df_us.groupby(crystal_sys_col):
    common_kwds["x"] = df_group[crystal_sys_col]
    common_kwds["legendgroup"] = crystal_sys
    common_kwds["showlegend"] = crystal_sys == "cubic"

    fig.add_violin(  # ionic dielectric distribution
        y=df_group[diel_ionic_pbe_col],
        scalegroup="ionic",
        name="ionic",
        side="positive",
        line_color="orange",
        **common_kwds,
    )
    fig.add_violin(  # electronic dielectric distribution
        y=df_group[diel_elec_pbe_col],
        scalegroup="electronic",
        name="electronic",
        side="negative",
        line_color="blue",
        **common_kwds,
    )


n_top, x_ticks = 30, {x: "" for x in cry_sys_order}
for cry_sys, df_group in df_us.groupby(crystal_sys_col):
    ionic_top = df_group[diel_ionic_pbe_col].nlargest(n_top).mean()
    elec_top = df_group[diel_elec_pbe_col].nlargest(n_top).mean()
    ionic_clr = rgb_color(ionic_top, 261)
    elec_clr = rgb_color(elec_top, 102)
    x_ticks[cry_sys] = (
        f"<b>{cry_sys}</b><br>{len(df_group):,} = {len(df_group)/len(df_us):.0%}"
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

save_fig(fig, f"{PAPER_FIGS}/our-diel-elec-vs-ionic-violin.pdf")


# %%
df_us.attrs.update(name="us", label="This Work")
df_mp.attrs.update(name="mp", label="MP Data")

for df in (df_us, df_mp):
    ax = ptable_heatmap(
        df.formula,
        exclude_elements=("O", "F"),
        colorscale="viridis",
        zero_color="white",
        count_mode="occurrence",
        cbar_title=f"Element Occurrence (total={len(df):,})",
        label_font_size=18,
        value_font_size=18,
        fmt=".0f",
    )

    save_fig(ax, f"{PAPER_FIGS}/ptable-elem-counts-{df.attrs['name']}.pdf")


# %%
us_elem_counts = count_elements(df_us.formula)
mp_elem_counts = count_elements(df_mp.formula)
# normalize by number of materials
us_elem_counts /= len(df_us)
mp_elem_counts /= len(df_mp)
ax = ptable_heatmap_ratio(
    us_elem_counts,
    mp_elem_counts,
    not_in_numerator=("white", ""),
    not_in_denominator=("white", ""),
    not_in_either=("#eff", ""),
    colorscale="viridis",
    label_font_size=18,
    value_font_size=16,
)
save_fig(ax, f"{PAPER_FIGS}/ptable-elem-ratio-us-vs-mp.pdf")


# %% project FoM onto periodic table
frac_comp_col = "fractional composition"
df_us[frac_comp_col] = [Composition(comp).as_dict() for comp in df_us.formula]

df_frac_comp = pd.DataFrame(df_us[frac_comp_col].tolist())
# ignore compositions amounts, count only element occurrence
df_frac_comp = df_frac_comp.where(df_frac_comp.isna(), 1)

for col, title in (
    (fom_pbe_col, r"$\mathbf{\Phi_M}$"),
    (diel_ionic_pbe_col, r"$\mathbf{\epsilon}_\text{ionic}$"),
    (diel_elec_pbe_col, r"$\mathbf{\epsilon}_\text{electronic}$"),
    (bandgap_pbe_col, r"$\mathbf{E}_\text{gap}$"),
):
    df_per_elem = df_frac_comp * df_us[col].to_numpy()[:, None]
    srs_per_elem = df_per_elem.mean(axis=0)
    srs_per_elem.index.name = f"Element-projected {title}"

    ax = ptable_heatmap(
        srs_per_elem.dropna(),
        colorscale="viridis",
        cbar_title=srs_per_elem.index.name,
        label_font_size=18,
        value_font_size=18,
        fmt=".0f",
    )
    save_fig(ax, f"{PAPER_FIGS}/ptable-per-elem-{col.replace('_', '-')}.pdf")


# %% export LaTeX table of all data points with FoM > fom_tresh for SI
col_name_map = {
    id_col: "Material ID",
    "formula": "Formula",
    "spacegroup.number": "Spacegroup",
}
fom_tresh = 350
tex_col_names = {
    "diel_elec_pbe": r"$\epsilon_\text{elec}$",
    "diel_ionic_pbe": r"$\epsilon_\text{ionic}$",
    diel_total_pbe_col: r"$\epsilon_\text{total}$",
    bandgap_pbe_col: "Band Gap (eV)",
    fom_pbe_col: r"$\fom$ (eV)",
    "nsites": "atoms",
    "nelements": "elements",
}
keep_cols = [*col_name_map, *tex_col_names]
df_high_fom = df_us[df_us[fom_pbe_col] > fom_tresh][keep_cols]
df_high_fom[bandgap_pbe_col] = df_us.bandgap_pbe.fillna(df_us.bandgap_us)

df_high_fom = df_high_fom.sort_values(fom_pbe_col, ascending=False).reset_index(
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
    "diel_elec_pbe": "ε<sub>elec</sub>",
    bandgap_pbe_col: "E<sub>gap</sub> (eV)",
}
int_cols = {
    "diel_ionic_pbe": "ε<sub>ionic</sub>",
    diel_total_pbe_col: "ε<sub>total</sub>",
    fom_pbe_col: "𝚽<sub>M</sub> (eV)",
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
        {key: "{:,.0f}" for key in int_cols.values()},
        precision=2,  # render floats with 2 decimals
        na_rep="",  # render NaNs as empty string
    )
)

df_to_pdf(styler, f"{PAPER_FIGS}/table-fom-pbe-gt-{fom_tresh}.pdf", size="100cm")
df_high_fom.to_csv(f"{DATA_DIR}/our-data-with-fom-pbe-gt-{fom_tresh}.csv", index=False)
styler.set_caption(f"Table of materials with 𝚽<sub>M</sub> > {fom_tresh} eV")


# %% inspect non-oxides
styler.data.query("~Formula.str.contains('O')")


# %%
ptable_heatmap_plotly(df_high_fom.formula, exclude_elements="O")
