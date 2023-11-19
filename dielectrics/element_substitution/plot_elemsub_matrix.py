# %%
import pandas as pd
from matplotlib.colors import SymLogNorm
from pymatviz.utils import element_symbols

from dielectrics import DATA_DIR
from dielectrics.element_substitution import load_icsd_trans_mat
from dielectrics.plots import plt


# %%
substitution_matrix = load_icsd_trans_mat()

n_elements = 36


# %%
plt.figure(figsize=(8, 6))

plt.imshow(
    substitution_matrix[:n_elements, :n_elements],
    interpolation="nearest",  # 'nearest': faithful but blocky
    cmap="Spectral",
    norm=SymLogNorm(linthresh=1e-5, base=10, vmax=1),
)

plt.xticks(range(n_elements))
plt.yticks(range(n_elements))

ax = plt.gca()
ax.set_xticklabels(element_symbols[idx + 1] for idx in range(n_elements))
ax.set_yticklabels(element_symbols[idx + 1] for idx in range(n_elements))

# hide even/odd element symbols along x/y axis
ax.set_xticks(ax.get_xticks()[1::2])
ax.set_yticks(ax.get_yticks()[0::2])

# display ticks on all 4 sides of plot
ax.yaxis.set_ticks_position("both")
ax.xaxis.set_ticks_position("both")
ax.tick_params(labeltop=True, labelright=True)

plt.colorbar(pad=0.07, label="Substitution Probability")

# plt.title("Our element substitution matrix", y=1.05)
#

# plt.savefig("plots/elemental-substitution-matrix.pdf")
# plt.savefig("plots/elemental-substitution-matrix.png")


# %% downloaded from https://tddft.org/bmg/data.php
# file URL: https://tddft.org/bmg/files/data/pettifor/raw_data/substitution.dat
wbm_elem_sub_matrix = f"{DATA_DIR}/element-substitution/wbm-elem-sub-matrix.dat"
df_wbm_trans_mat = pd.read_csv(wbm_elem_sub_matrix, header=None).drop(0).drop(0, axis=1)


# %%
plt.figure(figsize=(8, 8))
plt.gca().matshow(
    df_wbm_trans_mat.iloc[:n_elements, :n_elements],
    interpolation="nearest",
    cmap="Spectral",
    norm=SymLogNorm(linthresh=1e-5, base=10),
)
plt.title("WBM dataset substitution matrix")
# from "The optimal one dimensional periodic table"
# https://doi.org/10.1088/1367-2630/18/9/093011
