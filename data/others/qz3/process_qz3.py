# %%
from __future__ import annotations

import gzip
import pickle
from typing import TYPE_CHECKING, Any

import pandas as pd
from pymatgen.core import Composition
from tqdm import tqdm

from dielectrics import PKG_DIR, Key, today


if TYPE_CHECKING:
    from pymatgen.analysis.phase_diagram import PatchedPhaseDiagram


__author__ = "Janosh Riebesell"
__date__ = "2023-11-19"


# %% download JSON file from https://doi.org/10.6084/m9.figshare.10482707.v2
# needs manual renaming of column names to match our own naming scheme
df_qz3 = pd.read_json("dielectrics.json")
df_tmp = pd.json_normalize(df_qz3.pop("meta"))
df_qz3[list(df_tmp)] = df_tmp


def extract_len1_lists(lst: list[Any]) -> Any:
    """Extract values from single-element lists."""
    return lst[0] if isinstance(lst, list) and len(lst) == 1 else lst


# %%
for col in df_qz3:
    df_qz3[col] = df_qz3[col].map(extract_len1_lists)
    df_qz3[col] = df_qz3[col].map(extract_len1_lists)
    df_qz3[col] = df_qz3[col].map(extract_len1_lists)

df_qz3[[Key.formula, "formula_factor"]] = pd.DataFrame(df_qz3[Key.formula].to_list())
df_qz3 = df_qz3.round(4)

df_qz3[Key.fom_pbe] = df_qz3.bandgap_pbe * df_qz3.diel_total_pbe

# rename columns containing dielectric tensors
df_qz3 = df_qz3.rename(
    columns={"e_total": "eps_total", "e_electronic": "eps_electronic"}
)


# %%
df_qz3.hist(bins=100, figsize=(14, 10))


# %%
ppd_path = f"{PKG_DIR}/patched_phase_diagram/2022-01-25-ppd-mp+wbm.pkl.gz"

with gzip.open(ppd_path, "rb") as file:
    ppd_mp_wbm: PatchedPhaseDiagram = pickle.load(file)  # noqa: S301


compositions = df_qz3[Key.formula].map(Composition)
df_qz3["e_hull"] = [ppd_mp_wbm.try_get_e_hull(c) for c in tqdm(compositions)]
df_qz3["e_ref"] = [ppd_mp_wbm.try_get_e_ref(c) for c in tqdm(compositions)]

# the hull energy is relative to the reference energies for single element systems
# e.g. for Fe2O3 the e_hull is relative to e_ref = 2 * e_Fe + 3 * e_O?
# so we subtract e_ref from e_hull so that the hull energy is comparable to e_form
df_qz3["e_above_hull_pbe_us"] = df_qz3.e_form_pbe - (df_qz3.e_hull - df_qz3.e_ref)

df_qz3.isna().sum()


# %%
ax = df_qz3.e_above_hull_pbe.hist(
    figsize=(10, 6), bins=50, label="Qu et al. hull distances"
)
df_qz3.e_above_hull_pbe_us.hist(
    alpha=0.8, bins=100, ax=ax, label="Our MP+WBM hull distances"
)
ax.set(title=f"Qu et al. vs our MP+WBM convex hull ({today})")
ax.legend()
ax.figure.savefig(f"{today}-our-vs-quz3-hull.pdf")

df_qz3.filter(like="hull_pbe").describe(percentiles=[]).round(3)

# e_above_hull_pbe  e_above_hull_pbe_us
# count   441       441
# mean    0.06      0.03
# std     0.03      0.03
# min     0         -0.1
# 50%     0.07      0.03
# max     0.1       0.09


# %%
df_qz3.to_csv("qz3-diel.csv.bz2", index=False)

df_qz3 = pd.read_csv("qz3-diel.csv.bz2")
