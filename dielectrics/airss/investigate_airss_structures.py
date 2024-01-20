# %%
import itertools
from collections.abc import Sequence
from glob import glob
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matminer.featurizers.site import CrystalNNFingerprint
from matminer.featurizers.structure import SiteStatsFingerprint
from pymatgen.core import Structure
from pymatgen.ext.matproj import MPRester
from pymatgen.io.res import AirssProvider
from pymatviz import plot_structure_2d
from robocrys import StructureCondenser, StructureDescriber

from dielectrics import DATA_DIR, Key, today
from dielectrics.db.fetch_data import df_diel_from_task_coll


__author__ = "Janosh Riebesell"
__date__ = "2022-06-27"

formula = "NaLiTa2O6"
res_files = glob(f"{DATA_DIR}/airss/{formula}/good_castep/*.res")
castep_files = glob(f"{DATA_DIR}/airss/{formula}/good_castep/*.castep")


# %% 2022-06-30
def get_pairwise_struct_distances(
    df: pd.DataFrame,
    structure_col: str = "structure",
    fingerprint_col: str = "site_stats_fingerprint",
    # show only half of symmetric matrix by default, set to False to show all
    triangular: Literal["lower", "upper", False] = "lower",
    stats: Sequence[str] = ("mean", "std_dev", "minimum", "maximum"),
) -> pd.DataFrame:
    """Get pairwise distances between structures in a DataFrame.

    SiteStatsFingerprint compares local coordination environments across sites in
    different crystals to measure dissimilarity. Anything above 0.9 is said to be
    different structure prototypes. The AIRSS structures are 1.66 - 1.75 from the WBM
    structure with the much higher permittivity but more similar to each other (1.02).
    https://docs.materialsproject.org/methodology/related-materials

    Args:
        df (pd.DataFrame): DataFrame with structures
        structure_col (str, optional): Column name of structures.
            Defaults to 'structure'.
        fingerprint_col (str, optional): Column name of fingerprints.
            Defaults to 'site_stats_fingerprint'.
        triangular ('lower' | 'upper' | False, optional):
            Show only half of symmetric matrix by default, set to False to show all.
            Defaults to 'lower'.
        stats (Sequence[str], optional): Stats to use in fingerprint. Defaults to
            ('mean', 'std_dev', 'minimum', 'maximum').

    Returns:
        pd.DataFrame: df with pairwise distances.
    """
    cnn_fp = CrystalNNFingerprint.from_preset("ops")
    site_stats_fp = SiteStatsFingerprint(cnn_fp, stats=stats)

    df[fingerprint_col] = df[structure_col].map(site_stats_fp.featurize).map(np.array)

    df_out = pd.DataFrame(index=df.index, columns=df.index, dtype=float)

    for (idx1, fp1), (idx2, fp2) in itertools.combinations_with_replacement(
        df[fingerprint_col].items(), 2
    ):
        if triangular in ("lower", False):
            df_out.loc[idx2, idx1] = np.linalg.norm(fp1 - fp2)
        if triangular in ("upper", False):
            df_out.loc[idx1, idx2] = np.linalg.norm(fp1 - fp2)

    return df_out.style.format("{:.3g}", na_rep="").background_gradient(axis=None)


# %%
df_res = pd.DataFrame(
    [AirssProvider.from_file(file).as_dict(verbose=False) for file in res_files]
).set_index("seed")

df_res[Key.structure] = df_res.structure.map(Structure.from_dict)
df_res[Key.n_sites] = df_res[Key.structure].map(len)

df_res[Key.e_per_atom] = df_res.energy / df_res[Key.n_sites]
df_res = df_res.sort_values(by=Key.e_per_atom)

df_res["mev_above_lowest"] = 1e3 * (
    df_res[Key.e_per_atom] - df_res[Key.e_per_atom].min()
)


# %% 2022-06-24
# fetch some promising metastable elemental substitution structures for Chris Pickard
# tun run AIRSS on to get a better sense of the convex hull around them
airss_candidates_for_chris = [
    "mp-755367:Cu->Na",
    "mp-755367:Cu->Rb",
    "mp-755367:Cu->Ag",
    "mp-1225854:W->Te",
]
df_diel_from_task_coll(airss_candidates_for_chris, ["output.structure"])

# ended up sending Chris mp-755367:Cu->Na


# %% cell created 2022-06-27, edited 2022-07-13
airss_mongo_ids = ("airss-1", "airss-2", "mp-755367:Cu->Na")

df_mongo = df_diel_from_task_coll(
    {"material_id": {"$in": airss_mongo_ids}},
    ["output.structure", "airss_id"],
    cache=False,
)

df_mongo.index = ("vasp_" + df_mongo.airss_id).fillna(df_mongo.material_id)

df_mongo.structure.map(lambda struct: struct.add_oxidation_state_by_guess())


# %% add robocrys structure descriptions (wasn't that useful for understanding large
# differences in permittivity for similar structures)
df_mongo["robocrys_description"] = df_mongo.structure.map(
    StructureCondenser().condense_structure
).map(StructureDescriber().describe)


# %%
n_cols = min(len(df_mongo), 4)
n_rows = int(np.ceil(len(df_mongo) / n_cols))
fig, axs = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 5 * n_rows))

for ax, (material_id, struct) in zip(
    axs.flat, df_mongo.structure.items(), strict=False
):
    spg_num, sgp_symbol = struct.get_space_group_info()
    plot_structure_2d(struct, ax=ax)
    ax.set(title=f"{material_id} {spg_num} ({sgp_symbol})")

fig.suptitle(struct.formula, fontweight="bold", fontsize=16)
fig.show()

# compute pairwise dissimilarity matrix for VASP-relaxed AIRSS + WBM seed structures
get_pairwise_struct_distances(df_mongo)


# %% pairwise dissimilarity matrix for AIRSS result structures
df_res_struct_dists = get_pairwise_struct_distances(df_res)
# set title
df_res_struct_dists  # noqa: B018
# dataframe_image.export(df_res_struct_dists, "airss-structure-dissimilarity.png")


# %% compute some pairwise dissimilarities for MP structures copied from
# https://docs.materialsproject.org/methodology/related-materials#examples
# just as a reference for dissimilarity values
df_mp = pd.DataFrame(
    [
        ("mp-66", "diamond"),
        ("mp-2534", "GaAs"),
        ("mp-22862", "NaCl"),
        ("mp-5827", "CaTiO3"),
        ("mvc-12728", "spinel_CaCo2S4"),
        ("mp-560842", "spinel_sicd2O4"),
    ],
    columns=["material_id", "name"],
).set_index(Key.mat_id)

with MPRester() as mpr:
    df_mp["structure"] = df_mp.material_id.map(mpr.get_structure_by_material_id)


df_mp_struct_dists = get_pairwise_struct_distances(df_mp)
df_img_path = f"{today}-mp-struct-structure-dissimilarity.png"
# dataframe_image.export(df_mp_struct_dists, df_img_path)
df_mp_struct_dists.head()


# %%
df_res_and_mongo = df_res.append(df_mongo.drop(columns=["material_id"]))

df_res_and_mongo = df_res_and_mongo.filter(regex="(4142|6811)", axis=0).sort_index()

get_pairwise_struct_distances(df_res_and_mongo)


# %%
n_cols = min(len(df_res_and_mongo), 2)
n_rows = int(np.ceil(len(df_res_and_mongo) / n_cols))
fig, axs = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 5 * n_rows))

for ax, (material_id, struct) in zip(
    axs.flat, df_res_and_mongo.structure.items(), strict=False
):
    spg_num, sgp_symbol = struct.get_space_group_info()
    plot_structure_2d(struct, ax=ax)
    ax.set(title=f"{material_id}\n{spg_num} ({sgp_symbol})")

fig.suptitle("AIRSS vs VASP relaxed structures", fontweight="bold", fontsize=16)
fig.show()
