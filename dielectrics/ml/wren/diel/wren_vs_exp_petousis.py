# %%
from itertools import combinations

import pandas as pd
from pymatviz import annotate_metrics

from dielectrics import DATA_DIR, Key, PAPER_FIGS
from dielectrics.plots import plt


# %%
path_fn = lambda part: f"{DATA_DIR}/wren/diel/wren-mp-diel-{part}-trained-on-all-mp.csv"

wren_models = [
    "elec-ensemble",
    "elec-ensemble-robust",
    "ionic-ensemble",
    "ionic-ensemble-robust",
]
dfs = {
    model.replace("-ensemble", "").replace("-", "_"): pd.read_csv(path_fn(model))
    for model in wren_models
}


df_exp = pd.read_csv(f"{DATA_DIR}/others/petousis/exp-petousis.csv")
df_exp = df_exp.drop_duplicates(Key.mat_id).set_index(Key.mat_id)


# %% drop meaningless target columns (only needed once)
# for idx, df in enumerate(dfs.values()):
#     df = df.drop(df.filter(like="_target"), axis=1)
#     df.set_index(Keys.mat_id).round(4).to_csv(path_fn(models[idx]))


# %%
for key, df_diel_model in dfs.items():
    df_diel_model = df_diel_model.drop(
        df_diel_model.filter(like="_target"), axis=1
    ).drop_duplicates(Key.mat_id)

    df_diel_model = df_diel_model.set_index(Key.mat_id)

    df_diel_model[f"diel_{key}_pred"] = df_diel_model.filter(like="_pred_n").mean(1)

    df_exp[f"diel_{key}_wren"] = df_diel_model[f"diel_{key}_pred"]

    if "robust" in key:
        df_exp[f"diel_{key}_wren_std"] = (
            (df_diel_model.filter(like="_ale_n") ** 2).mean(1)
            + df_diel_model.filter(like="_pred_n").var(1)
        ) ** 0.5
    else:
        df_exp[f"diel_{key}_wren_std"] = df_diel_model.filter(like="_pred_n").std(1)

    dfs[key] = df_diel_model


# %%
df_exp[Key.diel_total_wren] = df_exp[Key.diel_elec_wren] + df_exp[Key.diel_ionic_wren]
df_exp["diel_total_robust_wren"] = (
    df_exp.diel_elec_robust_wren + df_exp.diel_ionic_robust_wren
)


# %% add up ionic and electronic uncertainties in quadrature
df_exp["diel_total_wren_std"] = (
    df_exp.diel_elec_wren_std**2 + df_exp.diel_ionic_wren_std**2
) ** 0.5
df_exp["diel_total_robust_wren_std"] = (
    df_exp.diel_elec_robust_wren_std**2 + df_exp.diel_ionic_robust_wren_std**2
) ** 0.5


# %%
fig, axs = plt.subplots(nrows=3, ncols=2, figsize=(12, 12))

fig.suptitle("Blue points from Petousis 2017, red ones from Petousis 2016", y=1)

for ax, (col1, col2) in zip(
    axs.flat, combinations(["exp", "wren", "mp", "robust_wren"], 2), strict=True
):
    cs = ["red" if "2017" in series else "C0" for series in df_exp.series]
    df_exp.plot.scatter(x=f"diel_total_{col1}", y=f"diel_total_{col2}", color=cs, ax=ax)
    n_samples = len(df_exp[[f"diel_total_{col1}", f"diel_total_{col2}"]].dropna())

    ax.set(xscale="log", xlabel=rf"$\epsilon_\mathrm{{tot}}^\mathrm{{{col1}}}$")
    ax.set(yscale="log", ylabel=rf"$\epsilon_\mathrm{{tot}}^\mathrm{{{col2}}}$")
    ax.set(title=f"{col1} vs {col2} total dielectric ({n_samples=})")

    annotate_metrics(df_exp[f"diel_total_{col1}"], df_exp[f"diel_total_{col2}"], ax=ax)
    ax.axline(
        [10, 10], [11, 11], color="black", linestyle="dashed", alpha=0.5, zorder=0
    )

fig.tight_layout()

plt.savefig(f"{PAPER_FIGS}/exp-vs-wren-vs-mp-diel-total.pdf")


# %%
fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(10, 5))

for ax, wren in zip(axs, ("wren", "robust_wren"), strict=True):
    df_exp.plot.scatter(
        x=Key.diel_total_exp,
        y=Key.diel_total_wren,
        yerr="diel_total_wren_std",
        ax=ax,
        loglog=True,
    )
    n_samples = len(df_exp[[f"diel_total_{wren}", Key.diel_total_exp]].dropna())

    ax.set(xlabel=r"$\epsilon_\mathrm{tot}^\mathrm{exp}$")
    ax.set(ylabel=rf"$\epsilon_\mathrm{{tot}}^\mathrm{{{wren}}}$")
    ax.set(title=f"{wren} vs exp total dielectric ({n_samples=})")

    annotate_metrics(df_exp[f"diel_total_{wren}"], df_exp[Key.diel_total_exp], ax=ax)
    ax.axline(
        [10, 10], [11, 11], color="black", linestyle="dashed", alpha=0.5, zorder=0
    )

fig.tight_layout()

plt.savefig(f"{PAPER_FIGS}/exp-vs-wren-std-diel-total.pdf")
