# %%
from __future__ import annotations

import gzip
import pickle
from typing import TYPE_CHECKING

import pandas as pd
from pymatgen.core import Composition
from pymatgen.entries.compatibility import MaterialsProject2020Compatibility
from pymatgen.entries.computed_entries import ComputedEntry
from pymatgen.ext.matproj import MPRester
from tqdm import tqdm

from dielectrics import DATA_DIR, PKG_DIR, Key
from dielectrics.db import db
from dielectrics.plots import plt  # side-effect import sets plotly template and plt.rc


if TYPE_CHECKING:
    from pymatgen.analysis.phase_diagram import PatchedPhaseDiagram


# %%
ppd_path = f"{PKG_DIR}/patched_phase_diagram/2022-01-25-ppd-mp+wbm.pkl.gz"

with gzip.open(ppd_path, mode="rb") as file:
    ppd_mp_wbm: PatchedPhaseDiagram = pickle.load(file)  # noqa: S301


# %%
wren_fom_csv_path = (
    f"{DATA_DIR}/wren/screen/wren-e_form-ens-rhys-screen-mp-top1k-fom-elemsub.csv"
    # f"{DATA_DIR}/wren/screen/wren-elemsub-mp+wbm.csv"
)
df_wren = pd.read_csv(wren_fom_csv_path, na_filter=False).set_index(
    Key.mat_id, drop=False
)

compositions = df_wren[Key.formula].map(Composition)
df_wren["e_hull"] = [ppd_mp_wbm.try_get_e_hull(c) for c in tqdm(compositions)]
df_wren["e_ref"] = [ppd_mp_wbm.try_get_e_ref(c) for c in tqdm(compositions)]


# %%
df_wren[Key.e_form_wren] = df_wren.filter(like="pred_n").mean(axis=1)
df_wren["e_form_wren_std"] = (
    df_wren.filter(like="pred_n").var(axis=1)
    # average aleatoric uncertainties in quadrature
    + (df_wren.filter(like="ale_n") ** 2).mean(axis=1)
) ** 0.5

# the hull energy is relative to the reference energies for single element systems
# e.g. for Fe2O3 the e_hull is relative to e_ref = 2 * e_Fe + 3 * e_O?
# so we subtract e_ref from e_hull so that the hull energy is comparable to e_form
df_wren[Key.e_above_hull_wren] = df_wren[Key.e_form_wren] - (
    df_wren.e_hull - df_wren.e_ref
)


# for 1st round of single Wren elem-substitution picking only the more likely stable
# compounds based on e_above_hull_wren_std_adj < 0.1 eV did not significantly harm mean
# FoM of remaining materials (~10% decrease from 326 to 299)
df_wren["e_above_hull_wren_std_adj"] = (
    df_wren[Key.e_form_wren]
    + df_wren.e_form_wren_std
    - (df_wren.e_hull - df_wren.e_ref)
)


# %%
stability_cutoff = 0.1
n_meta_stable = sum(df_wren.e_above_hull_wren < stability_cutoff)
n_meta_stable_std_adj = sum(df_wren.e_above_hull_wren_std_adj < stability_cutoff)
print(
    f"{n_meta_stable:,} / {len(df_wren):,} ({n_meta_stable / len(df_wren):.1%}) are < "
    f"{stability_cutoff} eV above the hull."
)
meta_stable_ratio = n_meta_stable_std_adj / len(df_wren)
print(
    f"{n_meta_stable_std_adj:,} / {len(df_wren):,} ({meta_stable_ratio:.1%}) "
    f"are < {stability_cutoff} eV above the hull when adding Wren std to e_form."
)
print(f"{sum(df_wren[Key.e_form_wren] > 0):,} have positive Wren formation energy.")
# For initial single Wren elemental substitution:
# Out of 67,659, 19,884 are less than 0.1 eV above the hull, 19,393 also have
# negative formation energy. Anything with positive formation energy will not be stable,
# no matter if above or below the known hull.

# For second Wren ensemble elemental substitution (Nov 3, 2021):
# 52,105 / 131,685 (39.6%) less than 0.1 eV above hull
# 25,864 / 131,685 (19.6%) less than 0.1 eV above hull when adding Wren std to e_form


# %%
df_wren.e_above_hull_wren.hist(bins=200, figsize=[10, 6])

plt.title(
    f"{sum(df_wren.e_above_hull_wren < 0.1):,} out of {len(df_wren):,} materials are "
    "< 0.1 eV/atom above the convex hull"
)

plt.axvline(0.1, linestyle="dashed", color="orange")
plt.xlim(-1, 2)


# %%
# df_wren.round(4).to_csv(csv_path)


# %% below cells add hull distances to MongoDB task collection
filters = {
    # Key.mat_id: {"$regex": "^m(p|vc)-", "$not": {"$regex": "->"}},
    # Key.mat_id: {"$regex": "^wbm-"},
    Key.e_above_hull_pbe: {"$exists": False},
    # "task_label": "static dielectric",
}

db.tasks.count_documents(filters)


# %%
task_fields = {
    "calcs_reversed.run_type": 1,
    Key.mat_id: 1,
    "composition_unit_cell": 1,
    Key.e_above_hull_wren: 1,
    Key.e_above_hull_pbe: 1,
    "which_hull": 1,
    Key.e_form_wren: 1,
    "output.energy": 1,
    "input.is_hubbard": 1,
    "input.hubbards": 1,
    "input.pseudo_potential": 1,
    "input.potcar_spec": 1,
}

task_docs = db.tasks.aggregate([{"$match": filters}, {"$project": task_fields}])

df_tasks = pd.DataFrame(task_docs).set_index(Key.mat_id, drop=False)
df_tasks = df_tasks.rename(columns={Key.e_above_hull_pbe: "e_above_hull_pbe_old"})
df_tasks.isna().sum()


# %% fetch MP hull distances
mp_ids = list(df_tasks[Key.mat_id].filter(regex="m(p|vc)-\\d+$").unique())

if mp_ids:
    data = MPRester().query(
        {Key.mat_id: {"$in": mp_ids}},
        ["e_above_hull", Key.mat_id],
    )

    df_mp = pd.DataFrame(data).set_index(Key.mat_id)

    df_tasks[Key.e_above_hull_mp] = df_tasks[Key.mat_id].map(df_mp.e_above_hull)

    df_tasks.e_above_hull_mp.describe()


# %% apply MaterialsProject2020Compatibility final energy corrections
unprocessed_entries = [
    ComputedEntry(
        row.composition_unit_cell,
        row.output["energy"],
        parameters={
            "run_type": row.calcs_reversed[0]["run_type"],
            "potcar_symbols": [dic["titel"] for dic in row.input["potcar_spec"]],
            **row.input,  # see task_fields above for contents of row.input
        },
        entry_id=row[Key.mat_id],
    )
    for row in tqdm(df_tasks.itertuples())
]


# since we used the latest VASP POTCARs which deprecate W_sv in favor of W_pv, running
# MaterialsProject2020Compatibility.process_entries() requires monkey-patching
# Compatibility.get_correction() with
# if "W_sv" in psp_settings:
#     psp_settings.remove("W_sv")
#     psp_settings.add("W_pv")
processed_entries = MaterialsProject2020Compatibility().process_entries(
    unprocessed_entries, verbose=True
)
n_skipped = len(unprocessed_entries) - len(processed_entries)
if n_skipped > 0:
    print(f"Warning: {n_skipped:,} entries were skipped")


# %%
df_tasks["energy_per_atom_corrected"] = pd.Series(
    {ent.entry_id: ent.energy_per_atom for ent in processed_entries}
)
compositions = df_tasks.composition_unit_cell.map(Composition)

for key, ppd in {
    # "mp_wbm_ppd_old": mp_wbm_ppd_old,
    "mp_wbm_ppd": ppd_mp_wbm,
    # "mp_ppd": mp_ppd,
}.items():
    print(ppd, flush=True)
    df_tasks[f"e_hull_{key}"] = [
        ppd_mp_wbm.try_get_e_hull(c) for c in tqdm(compositions)
    ]
    df_tasks[f"e_ref_{key}"] = [ppd_mp_wbm.try_get_e_ref(c) for c in tqdm(compositions)]

    df_tasks[f"e_form_pbe_{key}"] = (
        df_tasks.energy_per_atom_corrected - df_tasks[f"e_ref_{key}"]
    )

    df_tasks[f"e_above_hull_pbe_{key}"] = df_tasks[f"e_form_pbe_{key}"] - (
        df_tasks[f"e_hull_{key}"] - df_tasks[f"e_ref_{key}"]
    )


df_tasks = df_tasks.round(4)


# %%
df_tasks.filter(like="e_above_hull_").hist(bins=200)


# %%
stability_cutoff = 0.1
hull_col, form_col = "e_above_hull_pbe_mp_wbm_ppd", "e_form_pbe_mp_wbm_ppd"
n_meta_stable = sum(df_tasks[hull_col] < stability_cutoff)
n_below = sum(df_tasks[hull_col] < 0)
print(f"\n{hull_col}")
print(
    f"{n_meta_stable:,} / {len(df_tasks):,} ({n_meta_stable / len(df_tasks):.1%}) "
    f"materials less than {stability_cutoff} eV above the hull. {n_below:,} / "
    f"{len(df_tasks):,} ({n_below / len(df_tasks):.1%}) are below the hull."
)
print(f"Materials with positive PBE formation energy: {sum(df_tasks[form_col] > 0):,}")
# Incorrect (forgetting MP compat energy corrections) For all materials with elemental
# substitutions (Nov 19, 2021):
# > 49 / 971 (5%) are less than 0.1 eV above the hull.
# > Materials with positive PBE formation energy: 4

# With MP corrections applied for all elem-sub materials (Dec 9, 2021):
# > 325 / 1,295 (25.1%) materials less than 0.1 eV above the hull.
# > Materials with positive PBE formation energy: 4


# %%
# mp_version = '2020-09-08' at last run
mp_version = MPRester().get_database_version().replace("_", "-")
n_skipped = n_updated = 0

for row in tqdm(list(df_tasks.set_index("_id").itertuples())):
    if pd.isna(row.e_above_hull_pbe_mp_wbm_ppd):
        n_skipped += 1
        continue

    set_fields = {
        Key.e_above_hull_pbe: row.e_above_hull_pbe_mp_wbm_ppd,
        # time of fetching e_above_hull values from Materials Project
        "which_hull": "MP+WBM PPD 2022-01-25",
    }
    if Key.e_above_hull_mp in row and not pd.isna(row.e_above_hull_mp):
        set_fields[Key.e_above_hull_mp] = row.e_above_hull_mp
        set_fields["mp_hull_version"] = mp_version

    db.tasks.update_one({"_id": row.Index}, {"$set": set_fields})
    n_updated += 1

print(f"{n_skipped=} due to missing hull distance\n{n_updated=}")
