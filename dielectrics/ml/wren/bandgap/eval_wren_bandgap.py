# %%
import numpy as np
import pandas as pd
from pymatviz import density_hexbin, roc_curve

from dielectrics import DATA_DIR, Key
from dielectrics.plots import plt


# %%
df_ens = pd.read_csv(
    f"{DATA_DIR}/wren/bandgap/wren-bandgap-mp+wbm-ensemble.csv"
).set_index([Key.mat_id, Key.formula])

df_ens[Key.bandgap_wren] = df_ens.filter(like="pred_n").mean(1)
df_ens["bandgap_std"] = df_ens.filter(like="pred_n").std(1)


# %%
df_ens_rob = pd.read_csv(
    f"{DATA_DIR}/wren/bandgap/wren-bandgap-mp+wbm-ensemble-robust.csv"
).set_index([Key.mat_id, Key.formula])

df_ens_rob[Key.bandgap_wren] = df_ens_rob.filter(like="pred_n").mean(1)
df_ens_rob["bandgap_std"] = (
    df_ens_rob.filter(like="pred_n").var(1)
    # average aleatoric uncertainties in quadrature
    + (df_ens_rob.filter(like="ale_n") ** 2).mean(1)
) ** 0.5


# %%
# with uncertainty criterion
df_insul = df_ens[df_ens[Key.bandgap_wren] - df_ens.bandgap_std > 0.5]
# without uncertainty criterion
n_insul = sum(df_ens[Key.bandgap_wren] > 0.5)
n_false_metals = sum(df_insul[Key.bandgap_wren] < 0.01)

print(
    f"Wren ensemble predicts bandgap >0.5 eV for {len(df_insul):,} of {len(df_ens):,} "
    f"materials ({n_insul:,} without uncertainty) of which {n_false_metals:,} "
    f"({n_false_metals / len(df_insul):.2%}) are really metals."
)
# Wren ensemble predicts bandgap >0.5 eV for 10,339 of 63,921 materials (11,458 without
# uncertainty) of which 43 (0.42%) are really metals.


# %%
# with uncertainty criterion
df_rob_insul = df_ens_rob[df_ens_rob[Key.bandgap_wren] - df_ens_rob.bandgap_std > 0.5]
# without uncertainty criterion
n_rob_insul = sum(df_ens_rob[Key.bandgap_wren] > 0.5)
n_rob_false_metals = sum(df_rob_insul[Key.bandgap_wren] < 0.01)

print(
    f"Wren robust ensemble predicts bandgap >0.5 eV for {len(df_rob_insul):,} of "
    f"{len(df_ens_rob):,} ({n_rob_insul:,} without uncertainty) materials of which "
    f"{n_rob_false_metals:,} ({n_rob_false_metals / len(df_rob_insul):.2%}) are really "
    "metals."
)


# %%
df_gt0 = pd.read_csv(f"{DATA_DIR}/wren/bandgap/wren-bandgap>0-mp+wbm.csv").set_index(
    [Key.mat_id, Key.formula]
)
df_gt0_rob = pd.read_csv(
    f"{DATA_DIR}/wren/bandgap/wren-bandgap>0-mp+wbm-robust.csv"
).set_index([Key.mat_id, Key.formula])
df_l2 = pd.read_csv(f"{DATA_DIR}/wren/bandgap/wren-bandgap-mp+wbm-L2.csv").set_index(
    [Key.mat_id, Key.formula]
)

df_ens_nonmet = df_ens[df_ens[Key.bandgap_wren] > 0]
df_ens_rob_nonmet = df_ens_rob[df_ens_rob[Key.bandgap_wren] > 0]


# %%
df_clf = pd.read_csv(
    f"{DATA_DIR}/wren/bandgap/wren-metal-clf-ens=5-mp+wbm.csv"
).set_index([Key.mat_id, Key.formula])


# %%
def softmax(arr: np.ndarray, axis: int = -1) -> np.ndarray:
    """Compute the softmax of an array along an axis."""
    exp = np.exp(arr)
    return exp / exp.sum(axis=axis, keepdims=True)


for ens_idx in range(5):
    df_model_i = df_clf.filter(like=f"_n{ens_idx}")
    model_i_cols = df_model_i.columns.str.replace("pre-", "")

    df_clf[model_i_cols] = softmax(df_model_i.values)

df_clf["is_metal_logits_c0"] = df_clf.filter(like="_logits_c0").mean(1)
df_clf["is_metal_logits_c1"] = df_clf.filter(like="_logits_c1").mean(1)
df_clf["is_metal"] = (
    df_clf[["is_metal_logits_c0", "is_metal_logits_c1"]].idxmax(1).str.contains("_c1")
)


# %%
assert all(df_l2.index == df_clf.index)

n_non_metals_wo_clf = sum(df_l2.bandgap_pred_n0 > 0.5)
n_non_metals_w_clf = sum((~df_clf.is_metal) & (df_l2.bandgap_pred_n0 > 0.5))

print(f"Predicted non-metals w/o classifier: {n_non_metals_wo_clf:,}")
print(f"Predicted non-metals w classifier: {n_non_metals_w_clf:,}")
print(f"Remaining: {n_non_metals_w_clf / n_non_metals_wo_clf:.2%}")
# Predicted non-metals w/o classifier: 11,802
# Predicted non-metals w classifier: 11,221
# decrease: 95.08%


# %%
plt.figure(figsize=(12, 8))
roc_curve(targets=df_clf.is_metal_target, proba_pos=df_clf["is_metal_logits_c1"])


# %%
fig, axs = plt.subplots(5, 2, figsize=(12, 22), sharex=True, sharey=True)

ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8, ax9, ax10 = axs.flat

fig.suptitle("Wren Bandgap Models trained on MP+WBM (showing only non-metals)\n\n")

x, y = df_ens_rob_nonmet[[Key.bandgap_wren, "bandgap_pred_n0"]].to_numpy().T
density_hexbin(x, y, ax=ax1)
ax1.set_title("Single robust Wren trained on all data")

x, y = df_ens_rob_nonmet[[Key.bandgap_wren, Key.bandgap_wren]].to_numpy().T
density_hexbin(x, y, ax=ax2)
ax2.set_title("Ensemble robust Wren trained on all data")

x, y = df_ens_nonmet[[Key.bandgap_wren, "bandgap_pred_n0"]].to_numpy().T
density_hexbin(x, y, ax=ax3)
ax3.set_title("Single non-robust Wren trained on all data")

x, y = df_ens_nonmet[[Key.bandgap_wren, Key.bandgap_wren]].to_numpy().T
density_hexbin(x, y, ax=ax4)
ax4.set_title("Ensemble non-robust Wren trained on all data")

x, y = df_gt0[[Key.bandgap_wren, "bandgap_pred_n0"]].to_numpy().T
density_hexbin(x, y, ax=ax5)
ax5.set_title("Single non-robust Wren trained on non-metals only")

x, y = df_gt0_rob[[Key.bandgap_wren, "bandgap_pred_n0"]].to_numpy().T
density_hexbin(x, y, ax=ax6)
ax6.set_title("Single robust Wren trained on non-metals only")

x, y = (
    df_l2[df_l2.bandgap_pred_n0 > 0.5][[Key.bandgap_wren, "bandgap_pred_n0"]]
    .to_numpy()
    .T
)
density_hexbin(x, y, ax=ax7)
ax7.set_title("Single non-robust Wren trained on all data with L2 loss")

x, y = (
    df_l2[(~df_clf.is_metal) & (df_l2.bandgap_pred_n0 > 0.5)][
        [Key.bandgap_wren, "bandgap_pred_n0"]
    ]
    .to_numpy()
    .T
)
density_hexbin(x, y, ax=ax8)
ax8.set_title(
    "Single non-robust Wren trained on all data with L2 loss\n"
    "after dropping materials classified as metals"
)

x, y = df_l2[df_clf.is_metal][[Key.bandgap_wren, "bandgap_pred_n0"]].to_numpy().T
density_hexbin(x, y, ax=ax9)
ax9.set_title(
    "Single non-robust Wren trained on all data with L2 loss\n"
    "where wren_clf.is_metal"
)

x, y = (
    df_l2[(df_clf.is_metal) & (df_l2.bandgap_pred_n0 > 0.5)][
        [Key.bandgap_wren, "bandgap_pred_n0"]
    ]
    .to_numpy()
    .T
)
density_hexbin(x, y, ax=ax10)
ax10.set_title(
    "Single non-robust Wren trained on all data with L2 loss\n"
    "where wren_clf.is_metal & wren_L2.bandgap_pred_n0 > 0.5"
)


# plt.savefig("plots/wren-bandgap-non-metal-density-scatter.pdf")
