# %%
import pandas as pd
import pymatviz as pmv

from dielectrics import DATA_DIR, PAPER_FIGS, Key
from dielectrics.db.fetch_data import df_diel_from_task_coll
from dielectrics.plots import plt  # side-effect import sets plotly template and plt.rc


# %%
idx_cols = [Key.mat_id, Key.formula]

df_ionic_rob_ens = pd.read_csv(
    f"{DATA_DIR}/wren/diel/wren-mp-diel-ionic-ensemble-robust.csv"
).set_index(idx_cols)
df_elec_rob_ens = pd.read_csv(
    f"{DATA_DIR}/wren/diel/wren-mp-diel-elec-ensemble-robust.csv"
).set_index(idx_cols)

# filter out obviously wrong highly negative predictions
print(df_elec_rob_ens.diel_elec_target.nsmallest(5))
df_elec_rob_ens = df_elec_rob_ens.query("diel_elec_target > 0")
df_elec_rob_ens.diel_elec_target.hist(bins=100, log=True)

df_ionic_rob_ens["diel_ionic_pred"] = df_ionic_rob_ens.filter(
    like="pred_n", axis=1
).mean(axis=1)
df_elec_rob_ens["diel_elec_pred"] = df_elec_rob_ens.filter(like="pred_n", axis=1).mean(
    1
)

df_ionic_rob_ens["diel_ionic_ale"] = df_ionic_rob_ens.filter(like="ale_", axis=1).mean(
    1
)
df_elec_rob_ens["diel_elec_ale"] = df_elec_rob_ens.filter(like="ale_", axis=1).mean(
    axis=1
)


# %%
fig, axs = plt.subplots(2, 2, figsize=(12, 10))

fig.suptitle("Wren Dielectric Models trained on MP")
for ax, df, title in zip(
    axs.flat,
    (
        df_ionic_rob_ens[["diel_ionic_target", "diel_ionic_pred"]],
        df_elec_rob_ens[["diel_elec_target", "diel_elec_pred"]],
        df_ionic_rob_ens[["diel_ionic_target", "diel_ionic_pred_n0"]],
        df_elec_rob_ens[["diel_elec_target", "diel_elec_pred_n0"]],
    ),
    ("Single ionic", "Single electronic", "Ensemble ionic", "Ensemble electronic"),
    strict=True,
):
    x, y = df.to_numpy().T
    pmv.density_hexbin(x, y, ax=ax)
    ax.set_title(title)

# plt.savefig(f"{PAPER_FIGS}/wren-diel-density-scatter-trained-on-all-mp.pdf")


# %%
df_wren_seed = pd.read_csv(
    f"{DATA_DIR}/wren/screen/wren-diel-single-robust-mp+wbm.csv"
).set_index(Key.mat_id)
df_wren_seed.describe()


# %%
ax_res = (df_wren_seed[Key.diel_total_wren] - df_wren_seed.diel_total_wren_indi).hist(
    log=True, bins=70, figsize=[10, 6]
)

ax_res.set_title(
    "Histogram of residual between directly predicting total dielectric "
    "constant vs\nionic + electronic individually on MP + WBM dataset"
)
# plt.savefig(f"{PAPER_FIGS}/mp+wbm-indi-vs-direct-diel-residual.pdf")


# %%
df_wren_elemsub = pd.read_csv(
    f"{DATA_DIR}/wren/screen/wren-elemsub-mp+wbm+hull.csv"
).set_index(Key.mat_id)


# %% write elemental substitution seeds to disk, we'll use these to perform formula
# mutations based on chemical similarity
# df_wren_seed.nlargest(1000, Keys.fom_wren).round(4).to_csv(
#     f"{DATA_DIR}/wren/screen/wren-diel-single-robust-mp+wbm-fom-elemsub-seeds.csv"
# )


# %%
fom_wren_top = df_wren_elemsub.query("e_above_hull_wren < 0.1").fom_wren.nlargest(1000)
ax = fom_wren_top.hist(
    bins=70, figsize=[12, 6], label="top 1k Wren FoM elemsub < 0.1 eV above hull"
)

df_wren_seed.nlargest(1000, Key.fom_wren).fom_wren.hist(
    ax=ax, bins=70, color="orange", label="top 1k from MP+WBM"
)

ax.set_title("Wren-predicted FoM")
pmv.save_fig(f"{PAPER_FIGS}/wren/screen/top-1k-elemsub-vs-mp+wbm.pdf")


# %% EVALUATING WREN ENSEMBLE STARTS HERE
df_elec = pd.read_csv(
    f"{DATA_DIR}/wren/screen/wren-screen-mp+wbm-diel-elec-ensemble-robust"
    "-trained-on-all-mp.csv"
).set_index(Key.mat_id)
df_ionic = pd.read_csv(
    f"{DATA_DIR}/wren/screen/wren-screen-mp+wbm-diel-ionic-ensemble-robust"
    "-trained-on-all-mp.csv"
).set_index(Key.mat_id)


# %%
df_wren = df_ionic[[Key.formula, Key.wyckoff, Key.bandgap_pbe]].copy()

for key, df in zip(("elec", "ionic"), (df_elec, df_ionic), strict=True):
    df_wren[f"diel_{key}_wren"] = df.filter(like="_pred_n").mean(axis=1)

    df_wren[f"diel_{key}_wren_std"] = (
        (df.filter(like="_ale_n") ** 2).mean(axis=1)
        + df.filter(like="_pred_n").var(axis=1)
    ) ** 0.5


df_wren["diel_total_wren_std"] = (
    df_wren.diel_elec_wren_std**2 + df_wren.diel_ionic_wren_std**2
) ** 0.5

df_wren[Key.diel_total_wren] = (
    df_wren[Key.diel_elec_wren] + df_wren[Key.diel_ionic_wren]
)

df_wren[Key.fom_wren] = df_wren[Key.diel_total_wren] * df_wren[Key.bandgap_pbe]

df_wren["fom_wren_rank"] = df_wren[Key.fom_wren].rank(ascending=False).astype(int)

df_wren["fom_wren_rank_size"] = len(df_wren)


# %%
df_vasp_ens = df_diel_from_task_coll({"series": "MP+WBM top 1k Wren-diel-ens-pred FoM"})
df_vasp_single = df_diel_from_task_coll({"series": "MP+WBM top 1k Wren-pred FoM"})

wren_cols = ["diel_total_wren_std", Key.diel_total_wren]

df_vasp_ens[wren_cols] = df_wren[wren_cols]
df_vasp_single[Key.diel_total_wren] = df_wren_seed[Key.diel_total_wren]


# %% Compare Wren 2 months older single predictions with recent ensemble preds
df_vasp_cleaned = df_vasp_ens.query(
    "fom_wren_rank < 1000 and diel_total_wren_std < 1000"
)

plt.figure(figsize=(12, 8))
pmv.scatter_with_err_bar(
    df_vasp_cleaned[Key.diel_total_pbe],
    df_vasp_cleaned[Key.diel_total_wren],
    yerr=df_vasp_cleaned.diel_total_wren_std,
)


# %%
ax = df_vasp_single.plot.scatter(
    x=Key.diel_total_pbe, y=Key.diel_total_wren, figsize=(12, 8)
)

pmv.powerups.annotate_metrics(
    df_vasp_single[Key.diel_total_pbe], df_vasp_single[Key.diel_total_wren]
)
ax.axline((0, 0), (1, 1), alpha=0.5, zorder=0, linestyle="dashed", color="black")


# %%
df_ionic_ens = pd.read_csv(
    f"{DATA_DIR}/wren/diel/wren-mp-diel-ionic-ensemble-excl-petousis.csv"
).set_index(idx_cols)

df_exp = pd.read_csv(f"{DATA_DIR}/others/petousis/exp-petousis.csv").set_index(idx_cols)
df_elec_ens = pd.read_csv(
    f"{DATA_DIR}/wren/diel/wren-mp-diel-elec-ensemble-excl-petousis.csv"
).set_index(idx_cols)

df_elec_ens["diel_elec_target"] = df_exp[Key.diel_elec_mp]
df_ionic_ens["diel_ionic_target"] = df_exp[Key.diel_total_mp] - df_exp[Key.diel_elec_mp]

# filter out obviously wrong highly negative targets (if any)
print(df_elec_ens.diel_elec_target.nsmallest(5))
df_elec_ens = df_elec_ens.query("diel_elec_target > 0")
df_elec_ens.diel_elec_target.hist(bins=100, log=True)

df_ionic_ens["diel_ionic_pred"] = df_ionic_ens.filter(like="pred_n", axis=1).mean(
    axis=1
)
df_elec_ens["diel_elec_pred"] = df_elec_ens.filter(like="pred_n", axis=1).mean(axis=1)


# %%
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

fig.suptitle(
    "Non-robust Wren Dielectric Models\ntrained on MP excluding chemical systems in "
    "the Petousis experimental dataset"
)

labels = {"xlabel": "Materials Project", "ylabel": "Wren"}

x, y = df_ionic_ens[["diel_ionic_target", "diel_ionic_pred_n0"]].to_numpy().T
pmv.density_hexbin(x, y, ax=ax1, **labels)
ax1.set_title("Single ionic")

x, y = df_elec_ens[["diel_elec_target", "diel_elec_pred_n0"]].to_numpy().T
pmv.density_hexbin(x, y, ax=ax2, **labels)
ax2.set_title("Single electronic")

x, y = df_ionic_ens[["diel_ionic_target", "diel_ionic_pred"]].to_numpy().T
pmv.density_hexbin(x, y, ax=ax3, **labels)
ax3.set_title("Ensemble ionic")

x, y = df_elec_ens[["diel_elec_target", "diel_elec_pred"]].to_numpy().T
pmv.density_hexbin(x, y, ax=ax4, **labels)
ax4.set_title("Ensemble electronic")

# plt.savefig(f"{PAPER_FIGS}/wren-diel-density-scatter-trained-on-mp-excl-petousis.pdf")
