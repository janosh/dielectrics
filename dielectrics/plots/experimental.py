# %%
import os


# ensure mcsqs and str2cif are in the path
os.environ["PATH"] += f":{(module_dir := os.path.dirname(__file__))}/atat_bin:"
import pandas as pd
import plotly.express as px
from pymatgen.core import Structure
from pymatgen.transformations.advanced_transformations import (
    OrderDisorderedStructureTransformation,
    SQSTransformation,
)
from pymatgen.util.string import htmlify
from pymatviz import plot_xrd_pattern, set_plotly_template
from pymatviz.io import save_fig

from dielectrics import DATA_DIR, PAPER_FIGS, Key


set_plotly_template("pymatviz_white")
px.defaults.labels |= {
    Key.freq: "Frequency (Hz)",
    Key.fr_min_e: r"$\sqrt{F(R)-E}$",
}
materials = {
    "Bi2Zr2O7-Fm3m": "mp-756175",
    "CsTaTeO6-Fd3m": "mp-1225854:W->Te",
}
formulas_plain = [x.split("-")[0] for x in materials]
formulas = tuple(map(htmlify, formulas_plain))


# %% Impedance plot
bzo_impedance_csv = f"{DATA_DIR}/experiment/Bi2Zr2O7-impedance.csv"
df_impedance = pd.read_csv(bzo_impedance_csv).set_index(Key.freq)

fig_impedance = px.line(
    df_impedance, y=list(df_impedance), log_y=True, width=360, height=240
)
fig_impedance.layout.margin.update(l=0, r=0, b=0, t=0)
fig_impedance.layout.legend.update(title=None, x=1, y=1, xanchor="right", yanchor="top")
fig_impedance.show()


# %% Tauc Plot
df_tauc = pd.read_csv(
    f"{DATA_DIR}/experiment/both-tauc-bandgaps.csv", header=[0, 1], index_col=0
)
e_gap_exp = dict(Bi2Zr2O7=2.27, CsTaTeO6=1.05)
df_tauc = df_tauc.rename(
    columns=lambda col: f"{htmlify(col)}<br>E<sub>gap</sub> = {e_gap_exp[col]} eV",
    level=0,
)

df_tauc = df_tauc.filter(like=Key.fr_min_e).droplevel(1, axis=1)
df_tauc.index.name = Key.energy

fig_tauc = px.line(df_tauc, width=380, height=250)

y_max = 4.5  # df_tauc.max().max()
if auto_slopes := False:
    # add slope lines to figure for each material
    for formula, (y_low, y_high) in zip(
        df_tauc.columns.get_level_values(0).unique(),
        ((1.65, 1.95), (1, 1.55)),
        strict=True,
    ):
        srs = df_tauc[formula]
        # get first y value larger than y_low
        y1 = srs.loc[srs > y_low].iloc[0]
        # get last y value less than y_high
        y2 = srs.loc[srs < y_high].iloc[-1]
        # get corresponding x values
        x1 = df_tauc.index[srs == y1][0]
        x2 = df_tauc.index[srs == y2][0]
        # compute intersection with y=0
        x0 = x1 - y1 * (x2 - x1) / (y2 - y1)
        # extend line to y=y_max
        x2 = x2 + (y_max - y2) * (x2 - x1) / (y2 - y1)
        fig_tauc.add_shape(
            x0=x0, y0=0, x1=x2, y1=y_max, type="line", line=dict(width=1)
        )
        # add annotation at intersection
        fig_tauc.add_annotation(
            **dict(x=x0, y=0, ax=50, ay=-25),
            text=f"{x0:.2f} eV",
            arrowhead=4,
            # shorten arrow to avoid overlap with line
            standoff=6,
            # showarrow=False,
            # # y shift to avoid overlap with line
            # yshift=-10,
        )
else:
    # received from Wesley Surta on 2023-12-01
    # Bi2Zr2O7 line y = 2.96491 x - 6.72905
    # CsTaTeO6 line y = 2.50844 x - 2.65018
    for slope, intercept in ((2.96491, -6.72905), (2.50844, -2.65018)):
        y0, y1 = 0, y_max
        x1 = (y0 - intercept) / slope
        x2 = (y1 - intercept) / slope
        fig_tauc.add_shape(x0=x1, y0=y0, x1=x2, y1=y1, type="line", line=dict(width=1))
        fig_tauc.add_annotation(
            **dict(x=x1, y=y0, ax=50, ay=-30),
            text=f"{x1:.2f} eV",
            arrowhead=4,
            standoff=6,
        )

fig_tauc.update_xaxes(dtick=1)  # increase x-axis tick density
fig_tauc.update_yaxes(range=[0, y_max])
fig_tauc.layout.margin.update(l=5, r=5, b=5, t=5)
fig_tauc.layout.legend.update(title=None, x=1, y=0, xanchor="right")
fig_tauc.layout.yaxis.title.update(text=r"$\sqrt{F(R) - E}$", standoff=9)
fig_tauc.layout.xaxis.title.update(standoff=8)
fig_tauc.show()
save_fig(fig_tauc, f"{PAPER_FIGS}/exp-tauc-bandgaps.pdf")


# %% Diffuse Reflectance Plot
df_refl = pd.read_csv(f"{DATA_DIR}/experiment/both-diffuse-reflectance.csv", header=[1])
wave_len_col = "Wavelength (nm)"
df_refl = df_refl.set_index(wave_len_col).drop(columns=f"{wave_len_col}.1")
df_refl.columns = formulas

fig_refl = px.line(df_refl, width=380, height=250)
# fig_refl = px.line(df_refl, width=360, height=240, range_x=[None, 1200])
fig_refl.layout.margin.update(l=0, r=0, b=0, t=0)
fig_refl.layout.legend.update(title=None, x=1, y=0, xanchor="right")
fig_refl.layout.yaxis.title = "Reflectance (%)"
fig_refl.show()
save_fig(fig_refl, f"{PAPER_FIGS}/exp-diffuse-reflectance.pdf")


# %% DE-data Plot
# similar data as in https://doi.org/10.1021/acs.inorgchem.8b02258 fig. 5d and 6e except
# only at room temperature since the material is unstable at higher temperatures
# Also, the permittivity e' values in fig 6e dont make any sense for that publications
for formula in formulas_plain:
    csv_path = f"{DATA_DIR}/experiment/{formula}-diel-vs-freq.csv"
    df_diel = pd.read_csv(csv_path).set_index(Key.freq)

    blue, red, *_ = px.colors.qualitative.Plotly
    fig_diel = px.line(
        df_diel.filter(like="Permittivity"),
        log_x=True,
        width=380,
        height=220,
        color_discrete_sequence=(blue, "darkblue")
        if formula == "Bi2Zr2O7"
        else (red, "darkred"),
    )
    loss_col = "Dielectric Loss tan(δ)"
    # add loss tangent column on secondary y-axis
    fig_diel.add_scatter(
        x=df_diel.index,
        y=df_diel[loss_col],
        name=loss_col,
        yaxis="y2",
        line=dict(color="darkorange", dash="dot"),
        showlegend=False,
    )
    x_title = "Dielectric Constant ε<sub>rel</sub>"
    fig_diel.layout.yaxis1.update(title=x_title, tickformat="1s")
    fig_diel.layout.yaxis2 = dict(
        title=loss_col,
        overlaying="y",
        side="right",
        rangemode="tozero",
        showgrid=False,
        color="darkorange",
        # range=[0, 0.4] if formula == "Bi2Zr2O7" else None,
        title_standoff=9,
    )

    fig_diel.add_annotation(
        x=0.5,
        y=0.4,
        text=htmlify(formula),
        showarrow=False,
        font=dict(size=15),
        xref="paper",
        yref="paper",
    )

    fig_diel.layout.margin.update(l=0, r=0, b=0, t=0)
    fig_diel.layout.legend.update(
        title=None, x=1, y=1, xanchor="right", bgcolor="rgba(0,0,0,0)"
    )

    fig_diel.show()
    # hide legend since figures will be shown side-by-side
    # fig_diel.update_layout(showlegend=formula == "Bi2Zr2O7")
    img_name = f"exp-{formula}-diel-real-imag-loss-vs-freq"
    save_fig(fig_diel, f"{PAPER_FIGS}/{img_name}.pdf")

    # save inset for CsTaTeO6 plot at 1MHz
    if formula == "CsTaTeO6":
        y1_max = df_diel.filter(like="Permittivity").loc[1e6].max().max()
        fig_diel.layout.xaxis.update(  # hide title, only 3 x-axis tick labels
            range=(5.88, 6.1), title="", tickvals=(0.8e6, 1e6, 1.2e6)
        )
        fig_diel.layout.yaxis1.update(range=(0, 1.4 * y1_max), title="")
        fig_diel.update_layout(showlegend=False, font_size=22)
        fig_diel.layout.annotations = []  # remove formula annotation
        fig_diel.update_traces(line=dict(width=6))  # increase line width
        fig_diel.layout.paper_bgcolor = "rgba(0,0,0,0)"  # has no effect on pdf
        fig_diel.data = fig_diel.data[:-1]  # remove diel loss tangent from inset

        fig_diel.show()
        save_fig(fig_diel, f"{PAPER_FIGS}/{img_name}-inset.png")


# %% Rietveld XRD fits for Zr2Bi2O7 Fm3m (227) and CsTaTeO6 Fd3m
for material in materials:
    x_col = "Q (Å⁻¹)"
    header_cols = [x_col, "Observed", "Fit", "Difference"]

    kwds = dict(sep=r"\s+", header=None, names=header_cols)
    df_rietveld = pd.read_csv(
        f"{DATA_DIR}/experiment/{material}-rietveld-plot.txt", **kwds
    )
    rietveld_ticks = pd.read_csv(
        f"{DATA_DIR}/experiment/{material}-rietveld-ticks.txt", **kwds
    )

    fig_xrd = px.line(df_rietveld, x=x_col, y=header_cols[1:], width=360, height=240)

    # start x-axis at 0
    # fig_xrd.update_xaxes(range=[0, df_rietveld[theta_col].max()])

    # Add the ticks for hkl reflections
    fig_xrd.add_scatter(
        x=rietveld_ticks[x_col],
        y=[-400] * len(rietveld_ticks),
        mode="markers",
        name=htmlify(material),
        marker=dict(line_color="black", symbol="line-ns", line_width=2, size=5),
    )

    arrow_kwds = dict(arrowhead=4, arrowsize=0.6, arrowwidth=1.5)
    if material == "CsTaTeO6-Fd3m":
        df_Ta2O5 = pd.read_csv(  # noqa: N816
            f"{DATA_DIR}/experiment/CsTaTeO6-Ta2O5-xrd-ticks.txt", **kwds
        )
        fig_xrd.add_scatter(  # Ta2O5 peaks
            x=df_Ta2O5[x_col],
            y=[-800] * len(df_Ta2O5),
            mode="markers",
            name=htmlify("Ta2O5"),
            marker=dict(line_color="orange", symbol="line-ns", line_width=1, size=5),
        )
        # label Ta2O5 peak at (1.7, 700)
        fig_xrd.add_annotation(
            **dict(x=1.6, y=500, ax=-20, ay=-50),
            text=htmlify("Ta2O5"),
            font=dict(color="orange"),
            arrowcolor="orange",
            **arrow_kwds,
        )
    elif material == "Bi2Zr2O7-Fm3m":
        # label missing (111) peak
        # TODO get precise location for would-be (111) peak if Bi2Zr2O7 were pyrochlore
        fig_xrd.add_annotation(
            **dict(x=1.2, y=800, ax=0, ay=-50),
            text="no (111)<br>peak",
            font=dict(color="black"),
            arrowcolor="black",
            **arrow_kwds,
        )

    fig_xrd.layout.margin.update(l=10, r=10, b=10, t=10)
    fig_xrd.layout.legend.update(title=None, x=1, y=1, xanchor="right", yanchor="top")
    fig_xrd.layout.yaxis.update(
        title="Intensity (a.u.)", title_standoff=2, showticklabels=False
    )
    fig_xrd.layout.xaxis.update(title_standoff=0)
    fig_xrd.show()
    save_fig(fig_xrd, f"{PAPER_FIGS}/exp-rietveld-{material}.pdf")


# %%
for material in materials:
    exp_struct = Structure.from_file(f"{DATA_DIR}/experiment/{material}.cif")
    print(f"--- {material} ---\n\n{exp_struct.get_space_group_info()=}")
    sqs_struct: Structure = SQSTransformation(scaling=(1, 1, 2)).apply_transformation(
        exp_struct
    )
    sqs_struct.to(f"{DATA_DIR}/experiment/{material}-sqs.cif")
    print(f"{sqs_struct.get_space_group_info()=}")

    # CsTaTeO6-Fd3m ran for one hour with sqs_method='mcsqs' on an M3 MacBook Pro
    # without finishing. tried scaling 2, 4, 6 and (2, 1, 1), (1, 2, 1), (1, 1, 2)
    # only the Ta/Te (0, 0, 0) in CsTaTeO6 is disordered so unclear why it takes so long
    n_sqs_sites = {"Bi2Zr2O7-Fm3m": 48, "CsTaTeO6-Fd3m": None}
    if len(sqs_struct) != n_sqs_sites[material]:
        raise ValueError(
            f"Unexpected number of sites in SQS structure "
            f"{len(sqs_struct)=} != {material=}"
        )
    exp_struct.add_oxidation_state_by_guess()
    ordered_struct = OrderDisorderedStructureTransformation().apply_transformation(
        exp_struct
    )
    ordered_struct.get_space_group_info()


# %% compare experimental and DFT XRD for Bi2Zr2O7
exp_zbo = Structure.from_file(f"{DATA_DIR}/experiment/Bi2Zr2O7-Fm3m.cif")
pbe_zbo = Structure.from_file(f"{DATA_DIR}/experiment/mp-756175-Zr2Bi2O7-dft-pbe.cif")

fig = plot_xrd_pattern(
    {
        f"Exp {exp_zbo.formula} ({exp_zbo.get_space_group_info()[1]})": exp_zbo,
        f"PBE {pbe_zbo.formula} ({pbe_zbo.get_space_group_info()[1]})": pbe_zbo,
    }
)
save_fig(fig, f"{PAPER_FIGS}/xrd-Bi2Zr2O7-exp-vs-dft.pdf")


# %% compare experimental and DFT XRD for CsTaTeO6
exp_cto = Structure.from_file(f"{DATA_DIR}/experiment/CsTaTeO6-Fd3m.cif")
pbe_cto = Structure.from_file(
    f"{DATA_DIR}/experiment/mp-1225854-W->Te-CsTaTeO6-dft-pbe.cif"
)

fig = plot_xrd_pattern(
    {
        f"Exp {exp_cto.formula} ({exp_cto.get_space_group_info()[1]})": exp_cto,
        f"PBE {pbe_cto.formula} ({pbe_cto.get_space_group_info()[1]})": pbe_cto,
    }
)
fig.show()
save_fig(fig, f"{PAPER_FIGS}/xrd-CsTaTeO6-exp-vs-dft.pdf")
