# %%
import pandas as pd
import plotly.express as px
from pymatgen.util.string import htmlify
from pymatviz.io import save_fig

from dielectrics import (
    DATA_DIR,
    PAPER_FIGS,
    energy_col,
    fr_min_e_col,
    freq_col,
    imped_col,
)


px.defaults.labels = {freq_col: "Frequency (Hz)", fr_min_e_col: r"$\sqrt{F(R)-E}$"}
px.defaults.template = "plotly_white"
materials = ("Bi2Zr2O7-Fm3m", "CsTaTeO6-Fd3m")
formulas_plain = [x.split("-")[0] for x in materials]
formulas = tuple(map(htmlify, formulas_plain))


# %% Impedance plot
df_impedance = pd.read_csv(f"{DATA_DIR}/experiment/Bi2Zr2O7-impedance.csv", header=1)

fig_impedance = px.line(
    df_impedance,
    x=freq_col,
    y=["real impedance", "imaginary impedance"],
    labels={"value": imped_col},
    log_y=True,
)
fig_impedance.layout.margin.update(l=0, r=0, b=0, t=0)
fig_impedance.layout.legend.update(title=None, x=1, y=1, xanchor="right", yanchor="top")
fig_impedance.show()


# %% Tauc Plot
df_tauc = pd.read_csv(
    f"{DATA_DIR}/experiment/dielectrics-tauc.csv", header=[0, 1], index_col=0
)

df = df_tauc.filter(like=fr_min_e_col).droplevel(1, axis=1)
df.index.name = energy_col
fig = px.line(df, width=600, height=400)
fig.layout.margin.update(l=5, r=5, b=5, t=5)
fig.layout.legend.update(title=None, x=1, y=0, xanchor="right")
fig.layout.yaxis.title = fr_min_e_col
fig.show()


# %% Diffuse Reflectance Plot
df_refl = pd.read_csv(
    f"{DATA_DIR}/experiment/dielectrics-diffuse-reflectance.csv", header=[1]
)
wave_len_col = "Wavelength (nm)"
df_refl = df_refl.set_index(wave_len_col).drop(columns=f"{wave_len_col}.1")
df_refl.columns = formulas

fig = px.line(1 / df_refl, width=600, height=400, range_x=[df_refl.index.min(), 1200])
# fig = px.line(df_refl, width=600, height=400, range_x=[None, 1200])
fig.layout.margin.update(l=0, r=0, b=0, t=0)
fig.layout.legend.update(title=None, x=1, y=1, xanchor="right")
fig.layout.yaxis.title = "Reflectance (%)"
fig.show()
# save_fig(fig, f"{PAPER_FIGS}/exp-diffuse-reflectance.pdf")


# %% DE-data Plot
# similar data as in https://doi.org/10.1021/acs.inorgchem.8b02258 fig. 5d and 6e except
# only at room temperature since the material is unstable at higher temperatures
# Also, the permittivity e' values in fig 6e dont make any sense for that publications
formula = "Bi2Zr2O7"
df_de = pd.read_csv(f"{DATA_DIR}/experiment/{formula}-DE-data.csv").set_index(freq_col)
df_de.columns = df_de.columns.str.title()
fig_diel = px.line(df_de.filter(like="Permittivity"), log_x=True, width=600, height=400)
loss_col = "Loss Tangent"
# add loss tangent column on secondary y-axis
fig_diel.add_scatter(
    x=df_de.index,
    y=df_de[loss_col],
    name=loss_col,
    yaxis="y2",
    line=dict(color="darkorange", dash="dot"),
)
fig_diel.layout.yaxis1 = dict(title="Permittivity")
fig_diel.layout.yaxis2 = dict(
    title=loss_col,
    overlaying="y",
    side="right",
    rangemode="tozero",
    showgrid=False,
    color="darkorange",
    range=[0, 0.4],
)

fig_diel.layout.margin.update(l=0, r=0, b=0, t=0)
fig_diel.layout.legend.update(title=None, x=1, y=1, xanchor="right")
fig_diel.show()
save_fig(fig_diel, f"{PAPER_FIGS}/exp-{formula}-dielectric-real-imaginary-loss.pdf")


# %% Rietveld XRD fits for Zr2Bi2O7 Fm3m (227) and CsTaTeO6 Fd3m
for material in materials:
    rietveld_ticks_data_path = "{DATA_DIR}/experiment/Bi2Zr2O7-Fm3m-rietveld-ticks.txt"

    theta_col = r"$2 \theta$"
    header_cols = [theta_col, "Observed", "Fit", "Difference"]

    kwds = dict(sep=r"\s+", header=None, names=header_cols)
    df_rietveld = pd.read_csv(
        f"{DATA_DIR}/experiment/{material}-rietveld-plot.txt", **kwds
    )
    rietveld_ticks = pd.read_csv(
        f"{DATA_DIR}/experiment/{material}-rietveld-ticks.txt", **kwds
    )

    fig = px.line(df_rietveld, x=theta_col, y=header_cols[1:], width=500, height=300)

    # Add the ticks for hkl reflections
    fig.add_scatter(
        x=rietveld_ticks[theta_col],
        y=[-400] * len(rietveld_ticks),
        mode="markers",
        name=material,
        marker=dict(line_color="black", symbol="line-ns", line_width=2, size=5),
    )

    arrow_kwds = dict(arrowhead=4, arrowsize=0.6, arrowwidth=1.5)
    if material == "CsTaTeO6-Fd3m":
        df_Ta2O5 = pd.read_csv(
            f"{DATA_DIR}/experiment/CsTaTeO6-Ta2O5-xrd-ticks.txt", **kwds
        )
        fig.add_scatter(  # Ta2O5 peaks
            x=df_Ta2O5[theta_col],
            y=[-800] * len(df_Ta2O5),
            mode="markers",
            name="Ta2O5",
            marker=dict(line_color="orange", symbol="line-ns", line_width=1, size=5),
        )
        # label Ta2O5 peak at (1.7, 700)
        fig.add_annotation(
            **dict(x=1.6, y=500, ax=-20, ay=-50),
            text=htmlify("Ta2O5"),
            font=dict(color="orange"),
            arrowcolor="orange",
            **arrow_kwds,
        )
    elif material == "Bi2Zr2O7-Fm3m":
        # label missing (111) peak
        # TODO get precise location for would-be (111) peak if Bi2Zr2O7 were pyrochlore
        fig.add_annotation(
            **dict(x=1.2, y=800, ax=0, ay=-50),
            text="no (111)<br>peak",
            font=dict(color="black"),
            arrowcolor="black",
            **arrow_kwds,
        )

    fig.layout.margin.update(l=10, r=10, b=10, t=10)
    fig.layout.legend.update(title=None, x=1, y=1, xanchor="right", yanchor="top")
    fig.layout.yaxis.update(title="Intensity (a.u.)", tickformat="~s")
    fig.show()
    # save_fig(fig, f"{PAPER_FIGS}/exp-rietveld-{material}.pdf")
