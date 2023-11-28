# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
from pymatviz import ptable_heatmap
from pymatviz.io import save_fig
from sklearn.metrics import r2_score

from dielectrics import (
    DATA_DIR,
    PAPER_FIGS,
    bandgap_mp_col,
    bandgap_us_col,
    bandgap_wren_col,
    diel_total_pbe_col,
    diel_total_wren_col,
    id_col,
)
from dielectrics.db.fetch_data import df_diel_from_task_coll


expt = "enrich-big"  # one of enrich-small|enrich-big or train/screen
# enrich-small:
# enrich-big:
# train:
# screen:


# %%
df_diel_train = pd.read_json(
    f"{DATA_DIR}/mp-exploration/mp-diel-{expt}-train.json.bz2"
).rename(columns={"band_gap": bandgap_mp_col})

df_diel_screen = pd.read_json(
    f"{DATA_DIR}/mp-exploration/mp-diel-{expt}-test.json.bz2"
).rename(columns={"band_gap": bandgap_mp_col})

df_vasp = df_diel_from_task_coll({})

train_top_fom = df_diel_screen.query("n > 0")
n_top = 100
assert len(train_top_fom) == n_top

train_plus_screen_index = df_diel_screen.index.append(df_diel_train.index)


# %%
df_wren = pd.read_csv(
    f"{DATA_DIR}/wren/enrich/wren-diel-{expt}-total.csv", index_col=id_col
)
df_wren.columns = df_wren.columns.str.replace("_pred_n0", "_wren")
df_cgcnn = pd.read_csv(f"{DATA_DIR}/cgcnn/cgcnn-refract-{expt}.csv", index_col=id_col)

df_ml = df_wren[df_wren.index.isin(train_plus_screen_index)]

df_ml["n_cgcnn"] = df_cgcnn.n_pred_n0
df_ml[bandgap_mp_col] = df_diel_screen[bandgap_mp_col]


# %%
df_ml["fom_wren"] = df_ml.diel_total_wren * df_ml.bandgap_mp
df_ml["fom_cgcnn"] = df_ml.n_cgcnn**2 * df_ml.bandgap_mp

wren_top_fom = df_ml.nlargest(n_top, "fom_wren")
cgcnn_top_fom = df_ml.nlargest(n_top, "fom_cgcnn")

n_wren_matches = train_top_fom.index.isin(wren_top_fom.index).sum()
n_cgcnn_matches = train_top_fom.index.isin(cgcnn_top_fom.index).sum()
# n_cgcnn_matches = "n/a"

print(
    match_msg
    := f"top {n_top} FoM materials predicted by Wren (CGCNN) had {n_wren_matches} "
    f"({n_cgcnn_matches})\nof the top {n_top} FoM training set materials"
)


# %%
plt.figure(figsize=(10, 8))
plt.hexbin(
    # squared refractive index n^2 = dielectric constant epsilon_r
    df_diel_train.query("n < 5").n ** 2,
    df_diel_train.query("n < 5")[bandgap_mp_col],
    mincnt=1,
)

wren_top_not_in_train = wren_top_fom.loc[
    wren_top_fom.index.difference(train_top_fom.index)
]
cgcnn_top_not_in_train = cgcnn_top_fom.loc[
    cgcnn_top_fom.index.difference(train_top_fom.index)
]

top_train_not_found_wren = train_top_fom.loc[
    train_top_fom.index.difference(wren_top_fom.index)
]
top_train_not_found_cgcnn = train_top_fom.loc[
    train_top_fom.index.difference(cgcnn_top_fom.index)
]

assert (n_missed_wren := len(wren_top_not_in_train)) == len(top_train_not_found_wren)
assert (n_missed_cgcnn := len(cgcnn_top_not_in_train)) == len(top_train_not_found_cgcnn)

plt.scatter(
    wren_top_fom[diel_total_wren_col],
    wren_top_fom[bandgap_mp_col],
    color="orange",
    label=f"Wren-predicted top {n_top} FoM materials",
    s=75,
    alpha=0.8,
)
plt.scatter(
    cgcnn_top_fom.n_cgcnn**2,
    cgcnn_top_fom[bandgap_mp_col],
    color="green",
    label=f"CGCNN-predicted top {n_top} FoM materials",
    s=75,
    alpha=0.8,
)
plt.scatter(
    wren_top_not_in_train[diel_total_wren_col],
    wren_top_not_in_train[bandgap_mp_col],
    color="orange",
    label=f"{n_missed_wren} new candidates from Wren",
    s=75,
    edgecolor="black",
    alpha=0.8,
)
plt.scatter(
    cgcnn_top_not_in_train.n_cgcnn**2,
    cgcnn_top_not_in_train[bandgap_mp_col],
    color="green",
    label=f"{n_missed_cgcnn} new candidates from CGCNN",
    s=75,
    edgecolor="black",
    alpha=0.8,
)
# plt.scatter(
#     df_ml.loc[top_train_not_found_wren.index][diel_total_wren_col] ** 2,
#     df_ml.loc[top_train_not_found_wren.index].bandgap_ml,
#     color="red",
#     label=f"Wren missed {n_missed_wren}/{n_top} top FoM training materials",
#     s=75,
#     marker=",",
#     alpha=0.8,
# )
# plt.scatter(
#     df_ml.loc[top_train_not_found_cgcnn.index].n_cgcnn ** 2,
#     df_ml.loc[top_train_not_found_cgcnn.index].bandgap_ml,
#     color="cyan",
#     label=f"CGCNN missed {n_missed_cgcnn}/{n_top} top FoM training materials",
#     s=75,
#     marker="D",
#     alpha=0.8,
# )
plt.title(match_msg)
plt.legend()

xmax = 25
epsilon = np.linspace(0.1, xmax, 50)
for num in [1, 4, 9, 16]:
    plt.plot(epsilon, num / epsilon, "r--")

plt.colorbar(label="Density")
plt.xlabel(r"Dielectric Constant $\epsilon_\text{total}$")
plt.ylabel("PBE Bandgap / eV")

plt.xlim((0, xmax))
plt.ylim((0, 9))
# plt.savefig("plots/pareto-wren-vs-cgcnn.pdf")


# %%
ax = ptable_heatmap(
    wren_top_fom.reset_index().formula, count_mode="occurrence", fmt=".0f"
)
ax.set_title(f"Elemental prevalence among Wren-predicted top {n_top} FoM materials")
ax = ptable_heatmap(
    cgcnn_top_fom.reset_index().formula, count_mode="occurrence", fmt=".0f"
)
ax.set_title(f"Elemental prevalence among CGCNN-predicted top {n_top} FoM materials")


# %% refractive index n_pbe is computed by diel_tensor_to_const() same way as they do in
# Materials Project
# https://docs.materialsproject.org/methodology/dielectricity/#formalism
# tested on 2021-06-02 to give identical results to atomate's DielectricBuilder across
# 31 diverse materials
df_vasp = df_vasp.query("0 <= n_pbe <= 10")
df_vasp["n_wren"] = df_wren.n_pred_n0
df_vasp["n_cgcnn"] = df_cgcnn.n_pred_n0


# %%
df_vasp["fom_pbe"] = df_vasp.n_pbe**2 * df_vasp.bandgap
df_vasp["fom_wren"] = df_vasp[diel_total_wren_col] * df_vasp.bandgap
df_vasp["fom_cgcnn"] = df_vasp.n_cgcnn**2 * df_vasp.bandgap


# %%
df_vasp_wren = df_vasp[df_vasp.series == "Wren top 100 FoM"]
df_vasp_cgcnn_200 = df_vasp[df_vasp.series == "CGCNN top 200 - 100 FoM"]
df_vasp_cgcnn_100 = df_vasp[df_vasp.series == "CGCNN top 100 FoM"]


# %%
n_mae_wren = (df_vasp.n_pbe - df_vasp.n_wren).abs().mean()
n_mae_cgcnn = (df_vasp.n_pbe - df_vasp.n_cgcnn).abs().mean()

n_r2_wren = r2_score(df_vasp.n_pbe, df_vasp.n_wren)
n_r2_cgcnn = r2_score(df_vasp.n_pbe, df_vasp.n_cgcnn)

n_wren_perf = f"Wren:  R$^2$ = {n_r2_wren:.2f},  MAE = {n_mae_wren:.2f}"
n_cgcnn_perf = f"CGCNN:  R$^2$ = {n_r2_cgcnn:.2f},  MAE = {n_mae_cgcnn:.2f}"

ax = df_vasp.plot.scatter(
    x="n_pbe", y="n_wren", color="orange", figsize=(12, 8), label=n_wren_perf, s=75
)
ax = df_vasp.plot.scatter(x="n_pbe", y="n_cgcnn", ax=ax, label=n_cgcnn_perf, s=75)

line_styles = dict(alpha=0.5, zorder=0, linestyle="dashed", color="black")
ax.axline((0, 0), (1, 1), label="ideal", **line_styles)

plt.title(
    f"{len(df_vasp)} CGCNN/Wren vs VASP refractive index "
    "(marker size = VASP figure of merit)"
)
plt.legend()
plt.xlabel("VASP refractive index")
plt.ylabel("CGCNN/Wren refractive index")
plt.savefig("plots/wren+cgcnn-vs-vasp-top-n-scatter.pdf")


# %%
fom_mae_wren = (df_vasp.fom_pbe - df_vasp.fom_wren).abs().mean()
fom_mae_cgcnn = (df_vasp.fom_pbe - df_vasp.fom_cgcnn).abs().mean()

fom_r2_wren = r2_score(df_vasp.fom_pbe, df_vasp.fom_wren)
fom_r2_cgcnn = r2_score(df_vasp.fom_pbe, df_vasp.fom_cgcnn)

fom_wren_perf = f"Wren:  R$^2$ = {fom_r2_wren:.2f},  MAE = {fom_mae_wren:.2f}"
fom_cgcnn_perf = f"CGCNN:  R$^2$ = {fom_r2_cgcnn:.2f},  MAE = {fom_mae_cgcnn:.2f}"

ax = df_vasp.plot.scatter(
    x="fom_pbe",
    y="fom_wren",
    color="orange",
    figsize=(12, 8),
    label=fom_wren_perf,
    s=75,
)
df_vasp.plot.scatter(x="fom_pbe", y="fom_cgcnn", ax=ax, label=fom_cgcnn_perf, s=75)

line_styles = dict(alpha=0.5, zorder=0, linestyle="dashed", color="black")
ax.axline((0, 0), (1, 1), label="ideal", **line_styles)

plt.title(
    f"{len(df_vasp)} CGCNN/Wren vs VASP FoM predictions "
    "(marker size = VASP figure of merit)"
)
plt.legend(loc="upper right")
plt.xlabel("VASP figure of merit")
plt.ylabel("CGCNN/Wren figure of merit")
plt.savefig("plots/wren+cgcnn-vs-vasp-top-fom-scatter.pdf")


# %%
df_vasp.plot.bar(y=["fom_pbe", "fom_wren", "fom_cgcnn"], figsize=(10, 7))
plt.title(
    "VASP vs CGCNN vs WREN figure of merit (FoM) predictions"
    " on top 100 CGCNN-predicted FoM materials"
)
mae_wren = (df_vasp.fom_pbe - df_vasp.fom_wren).abs().mean()
mae_cgcnn = (df_vasp.fom_pbe - df_vasp.fom_cgcnn).abs().mean()
plt.legend(title=f"Wren MAE = {mae_wren:.2f}\nCGCNN MAE = {mae_cgcnn:.2f}")
# plt.savefig("plots/vasp-vs-wren-vs-cgcnn-top-100-fom-bar.pdf")


# %%
ax = df_vasp.plot.scatter(
    x="n_pbe", y="n_wren", c="blue", figsize=[8, 8], label=n_wren_perf
)
df_vasp.plot.scatter(
    x="n_pbe", y="n_cgcnn", c="red", ax=ax, marker="D", label=n_cgcnn_perf
)
plt.axis("square")
plt.legend()
plt.ylabel("Wren/CGCNN refractive index")
plt.xlabel("VASP refractive index")


# %%
pred_by_wren = df_vasp_wren[~df_vasp_wren.index.isin(df_vasp_cgcnn_100.index)]
pred_by_wren_and_cgcnn = df_vasp_wren[df_vasp_wren.index.isin(df_vasp_cgcnn_100.index)]
pred_by_cgcnn = df_vasp_cgcnn_100[~df_vasp_cgcnn_100.index.isin(df_vasp_wren.index)]


plt.figure(figsize=(10, 8))
n_max = 6
plt.hexbin(
    # square refractive index n to get dielectric constant epsilon_r
    df_diel_train.query("n < @n_max").n ** 2,
    df_diel_train.query("n < @n_max").bandgap,
    mincnt=1,
)

plt.scatter(
    pred_by_wren.n_pbe**2,
    pred_by_wren.bandgap,
    color="orange",
    label=f"{len(pred_by_wren)} VASP computed from top 100 Wren preds",
    alpha=0.8,
    s=70,
)
plt.scatter(
    pred_by_wren_and_cgcnn.n_pbe**2,
    pred_by_wren_and_cgcnn.bandgap,
    color="palegreen",
    label=f"{len(pred_by_wren_and_cgcnn)} VASP computed from top 100 Wren+CGCNN preds",
    alpha=0.8,
    s=70,
)
plt.scatter(
    pred_by_cgcnn.n_pbe**2,
    pred_by_cgcnn.bandgap,
    color="magenta",
    label=f"{len(pred_by_cgcnn)} VASP computed from top 100 CGCNN preds",
    alpha=0.8,
    s=70,
)

epsilon = np.linspace(0.1, n_max**2, 50)
for num in [4, 9, 16]:
    plt.plot(epsilon, num / epsilon, "r--")

plt.title("Some CGCNN/Wren preds reach the Pareto front")
plt.legend()
plt.colorbar(label="Density")
plt.xlabel(r"Dielectric Constant $\epsilon_r = n^2$")
plt.ylabel("PBE Bandgap / eV")

plt.xlim((0, n_max**2))
plt.ylim((0, 9))
plt.savefig("plots/wren+cgcnn-pareto.pdf")


# %% Quiver Plot Wren
plt.figure(figsize=(8, 8))

n_max = 6

df_vasp_wren["diel_elec_pbe"] = df_vasp_wren.n_pbe**2
df_vasp_wren["diel_elec_wren"] = df_vasp_wren[diel_total_wren_col]
ax = df_vasp_wren.plot.scatter(
    x="diel_elec_pbe", y="bandgap", color="orange", label="VASP", figsize=(8, 8)
)
df_vasp_wren.plot.scatter(
    x="diel_elec_wren", y="bandgap", color="magenta", label="CGCNN", ax=ax
)

dx = df_vasp_wren.n_pbe**2 - df_vasp_wren[diel_total_wren_col]
plt.quiver(
    df_vasp_wren[diel_total_wren_col],
    df_vasp_wren.bandgap,
    dx,
    len(df_vasp_wren) * [0],
    color=dx.map(lambda x: "blue" if x > 0 else "gray"),
    angles="xy",
    scale_units="xy",
    scale=1,
    width=0.003,
)


plt.xlim((0, n_max**2))
plt.ylim((0, 6))
plt.legend()
plt.title("Wren to VASP quiver plot")
plt.xlabel(r"Dielectric Constant $\epsilon_r = n^2$")
plt.ylabel("PBE Bandgap / eV")


epsilon = np.linspace(0.1, n_max**2, 50)
for num in [4, 9, 16]:
    plt.plot(epsilon, num / epsilon, "r--")

plt.savefig("plots/quiver-wren.pdf")


# %% Quiver Plot CGCNN
df_vasp_cgcnn_100["diel_elec_pbe"] = df_vasp_cgcnn_100.n_pbe**2
df_vasp_cgcnn_100["diel_elec_cgcnn"] = df_vasp_cgcnn_100.n_cgcnn**2
ax = df_vasp_cgcnn_100.plot.scatter(
    x="diel_elec_pbe", y="bandgap", color="orange", label="VASP", figsize=(8, 8)
)
df_vasp_cgcnn_100.plot.scatter(
    x="diel_elec_cgcnn", y="bandgap", color="magenta", label="CGCNN", ax=ax
)

dx = df_vasp_cgcnn_100.n_pbe**2 - df_vasp_cgcnn_100.n_cgcnn**2
plt.quiver(
    df_vasp_cgcnn_100.n_cgcnn**2,
    df_vasp_cgcnn_100.bandgap,
    dx,
    len(df_vasp_cgcnn_100) * [0],
    color=dx.map(lambda x: "blue" if x > 0 else "gray"),
    angles="xy",
    scale_units="xy",
    scale=1,
    width=0.003,
)


log = False
if log:
    plt.xscale("log")
    plt.yscale("log")
    n_max, y_max = 7, 9
else:
    n_max, y_max = 6, 6

plt.xlim((None, n_max**2))
plt.ylim((None, y_max))
plt.legend()
plt.title("CGCNN to VASP quiver plot")
plt.xlabel(r"Dielectric Constant $\epsilon_r = n^2$")
plt.ylabel("PBE Bandgap / eV")


epsilon = np.linspace(0.1, n_max**2, 50)
for num in [4, 9, 16]:
    plt.plot(epsilon, num / epsilon, "r--")

plt.savefig("plots/quiver-cgcnn.pdf")


# %%
df_vasp = df_vasp.sort_values(by=bandgap_us_col)

df_wren_bandgap = pd.read_csv(
    f"{DATA_DIR}/wren/screen/wren-bandgap-mp+wbm-ensemble-screen-mp-top1k-fom-elemsub.csv",
    index_col=id_col,
)

wren_bg_cols = list(df_wren_bandgap.filter(regex=r"bandgap_pred_n\d"))
assert len(wren_bg_cols) == 10
df_wren_bandgap[bandgap_wren_col] = df_wren_bandgap[wren_bg_cols].mean(axis=1)
bandgap_wren_std_col = "bandgap_wren_std"
df_wren_bandgap[bandgap_wren_std_col] = df_wren_bandgap[wren_bg_cols].std(axis=1)
df_vasp[bandgap_wren_col] = df_wren_bandgap[bandgap_wren_col]
df_vasp[bandgap_wren_std_col] = df_wren_bandgap[bandgap_wren_std_col]

ax = df_wren_bandgap[bandgap_wren_col].hist(bins=50, figsize=[10, 6])
ax.set(xlabel="Wren band gap (eV)", ylabel="Count", xlim=(0, None))


# %% Plot rolling MAE of Wren band gap and dielectric models vs DFT
# swap these to use either Wren or our DFT band gaps as x-axis values
for (x_axis_bandgap, other_bandgap), (x_axis_diel, other_diel) in [
    [(bandgap_wren_col, bandgap_us_col), (diel_total_wren_col, diel_total_pbe_col)],
    [(bandgap_us_col, bandgap_wren_col), (diel_total_pbe_col, diel_total_wren_col)],
]:
    df_plot = df_vasp.set_index(x_axis_bandgap, drop=False).sort_index()

    # compute MAE and R^2 for dielectric and bandgap line to show in plot annotation
    bandgap_mae = (df_vasp[other_bandgap] - df_vasp[x_axis_bandgap]).abs().mean()
    diel_mae = (df_vasp[diel_total_wren_col] - df_vasp[diel_total_pbe_col]).abs().mean()

    window = 300
    # bandgap rolling MAE calculation
    bandgap_rolling_err_col = (
        f"<b>Rolling |E<sub>gap,Wren</sub> - E<sub>gap,PBE</sub>|</b><br>"
        f"MAE={bandgap_mae:.1f}eV (std={df_vasp[x_axis_bandgap].std():.3})"
    )
    df_plot[bandgap_rolling_err_col] = abs(
        df_plot[x_axis_bandgap] - df_plot[other_bandgap]
    )
    rolling_bandgap_err = (
        df_plot[bandgap_rolling_err_col].dropna().rolling(window=window).mean()
    )

    fig = px.line(
        rolling_bandgap_err,
        color_discrete_sequence=[bandgap_color := "blue"],
        width=500,
        height=300,
    )

    # add rolling MAE of MP band gap w.r.t. our own PBE band gaps into same plot
    # bandgap_mp_err = bandgap_rolling_err.replace("Wren", "MP")
    # df_plot[bandgap_mp_err] = abs(df_plot[bandgap_pbe_col] - df_plot.index)
    # rolling_mp_err = df_plot[bandgap_mp_err].dropna().rolling(window=100).mean()
    # fig.add_scatter(x=rolling_mp_err.index, y=rolling_mp_err, name=bandgap_mp_err)

    diel_rolling_error_col = (
        f"<b>Rolling |ε<sub>total,Wren</sub> - ε<sub>total,PBE</sub>|</b><br>"
        f"MAE={diel_mae:.1f} (std={df_vasp[diel_total_pbe_col].std():.3})"
    )

    df_plot = df_plot.set_index(x_axis_diel, drop=False).sort_index()
    df_plot[diel_rolling_error_col] = abs(df_plot[x_axis_diel] - df_plot[other_diel])
    rolling_diel_err = (
        df_plot[diel_rolling_error_col].dropna().rolling(window=window).mean()
    )
    # add rolling MAE of Wren dielectric constant into same plot (top x and right y axis)
    fig.add_scatter(
        x=rolling_diel_err.index,
        y=rolling_diel_err,
        name=diel_rolling_error_col,
        yaxis="y2",
        xaxis="x2",
        line=dict(color=(diel_color := "red")),
        marker=dict(symbol="square"),
    )

    x1_title = f"E<sub>gap,{'Wren' if 'wren' in x_axis_bandgap else 'PBE'}</sub> (eV)"
    x2_title = f"ε<sub>total,{'Wren' if 'wren' in x_axis_diel else 'PBE'}</sub>"
    y1_title = "Rolling E<sub>gap</sub> absolute error (eV)"
    y2_title = "Rolling ε<sub>total</sub> absolute error"

    common = dict(showline=True, linewidth=2, title_standoff=5)
    fig.layout.xaxis = dict(color=bandgap_color, title=x1_title, **common)
    fig.layout.yaxis = dict(color=bandgap_color, title=y1_title, **common)

    common_2 = dict(showgrid=False, color=diel_color, **common)
    fig.layout.xaxis2 = dict(overlaying="x", side="top", **common_2, title=x2_title)
    fig.layout.yaxis2 = dict(overlaying="y", side="right", **common_2, title=y2_title)

    fig.layout.margin = dict(l=20, r=20, t=20, b=20)
    fig.update_traces(marker=dict(size=4), mode="lines+markers")
    legend_title = dict(text=f"{window=}", font=dict(size=12))
    if "wren" in x_axis_bandgap:
        fig.update_layout(showlegend=False)
    else:
        fig.layout.legend = dict(
            x=1, y=0.15, xanchor="right", title=legend_title, bgcolor="rgba(0,0,0,0)"
        )

    # set x-min to 0 (can't use None for xmax, has no effect)
    fig.layout.xaxis.update(range=[0, 8.5])
    fig.layout.xaxis2.update(range=[0, 750])

    fig.show()
    assert ("wren" in x_axis_bandgap, "wren" in x_axis_diel) in (
        (True, True),
        (False, False),
    )
    suffix = f"{'wren' if 'wren' in x_axis_bandgap else 'pbe'}-as-x.pdf"
    save_fig(fig, f"{PAPER_FIGS}/rolling-bandgap+diel-error-{suffix}")


# %%
df_vasp.plot.scatter(x=bandgap_us_col, y=bandgap_wren_col, alpha=0.1)
