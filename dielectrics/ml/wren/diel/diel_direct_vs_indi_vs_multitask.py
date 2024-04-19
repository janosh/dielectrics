# %%
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import r2_score

from dielectrics import DATA_DIR, Key


# %%
expt = "enrich-big"

df_diel_train = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-{expt}-train.json.bz2")

df_diel_test = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-{expt}-test.json.bz2")


# %%
df_wren = pd.read_csv(f"enrich/wren-diel-{expt}-total.csv", index_col=Key.mat_id)

for target in ["elec", "ionic"]:
    cols = [f"diel_{target}_target", f"diel_{target}_pred_n0"]
    df_wren[cols] = pd.read_csv(
        f"enrich/wren-diel-{expt}-{target}.csv", index_col=Key.mat_id
    )[cols]

n_top = 100
top_train = df_wren[df_wren.diel_ionic_target > 0]
assert len(top_train) == n_top


# %% Number of top 100 predicted n materials that are in actual top 100
sort_by = "diel_ionic_pred"
found_df = top_train.merge(df_wren.nlargest(100, sort_by))
print(
    f"Wren matches between predicted and actual top {n_top} {sort_by} materials out of "
    f"{len(df_wren):,} candidates:"
)
found_df.head()


# %%
models = ["total", "ionic", "elec"]
dfs_models = [
    pd.read_csv(f"enrich/wren-diel-test-{mod}.csv", index_col=[Key.mat_id, Key.formula])
    for mod in models
]
df_wren = pd.concat(dfs_models, axis=1)
df_wren.columns = df_wren.columns.str.replace("_n0", "")
df_wren = df_wren[df_wren.diel_total_target < 200]


# %%
line_styles = dict(alpha=0.5, zorder=0, linestyle="dashed", color="black")

for mod in ["total", "ionic", "elec"]:
    ax = df_wren.plot.scatter(
        x=f"diel_{mod}_target", y=f"diel_{mod}_pred", figsize=(10, 10)
    )

    ax.axline((0, 0), (1, 1), label="ideal", **line_styles)

    xs, ys = df_wren[f"diel_{mod}_target"], df_wren[f"diel_{mod}_pred"]
    r2 = r2_score(xs, ys)
    mae = (xs - ys).abs().mean()

    plt.legend(title=f"MAE = {mae:.3f}, $R^2$ = {r2:.3f}")


# %%
df_multitask = pd.read_csv(
    f"{DATA_DIR}/wren/enrich/wren-diel-test-elec+ionic-multitask.csv",
    index_col=[Key.mat_id, Key.formula],
)
df_multitask["diel_total_pred_mt"] = (
    df_multitask.diel_ionic_pred_n0 + df_multitask.diel_elec_pred_n0
)
df_wren["diel_total_pred_indi"] = df_wren.diel_elec_pred + df_wren.diel_ionic_pred

total_mae_direct = (df_wren.diel_total_target - df_wren.diel_total_pred).abs().mean()
total_mae_indi = (df_wren.diel_total_target - df_wren.diel_total_pred_indi).abs().mean()
total_mae_mt = (
    (df_wren.diel_total_target - df_multitask.diel_total_pred_mt).abs().mean()
)

print(f"{total_mae_direct=:.3f} vs {total_mae_indi=:.3f} vs {total_mae_mt=:.3f}")
# diel_total_mae_direct=5.519 vs diel_total_mae_indi=5.165 vs diel_total_mae_mt=5.378


# %%
ax = df_wren.plot.scatter(
    x="diel_total_target",
    y="diel_total_pred",
    figsize=(10, 10),
    color="orange",
    label="predict total diel directly",
)
df_wren.plot.scatter(
    x="diel_total_target",
    y="diel_total_pred_indi",
    figsize=(10, 10),
    ax=ax,
    label="elec. + ionic individually",
)

ax.axline((0, 0), (1, 1), label="ideal", **line_styles)
plt.legend()
