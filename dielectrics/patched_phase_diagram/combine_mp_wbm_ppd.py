"""Combine all of Materials Project and the WBM dataset into a single
PatchedPhaseDiagram. Takes a while, even on CSD3:
sintr -A LEE-JR769-SL2-CPU -p icelake -n 24 -t 1:0:0.

PatchedPhaseDiagram added in PR https://github.com/materialsproject/pymatgen/pull/2042

code below adapted from file 'combine-mp-petti-ppd.py' Rhys sent on Jun 24, 2021
https://ml-physics.slack.com/files/UD6TCLWAY/F025PJSBB0F/combine-mp-petti-ppd.py

Rhys' original PPD was generated with all MP entries from 2021-04-27.
"""

# %%
import gzip
import os
import pickle
import warnings

import pandas as pd
import plotly.express as px
from matbench_discovery.data import DATA_FILES
from pymatgen.analysis.phase_diagram import PatchedPhaseDiagram, PDEntry
from pymatgen.core import Composition
from pymatgen.entries.compatibility import MaterialsProject2020Compatibility
from pymatgen.entries.computed_entries import ComputedStructureEntry
from pymatgen.ext.matproj import MPRester
from tqdm import tqdm

from dielectrics import Key, today
from dielectrics.patched_phase_diagram import MODULE_DIR


__author__ = "Janosh Riebesell"
__date__ = "2021-08-05"


# %%
df_wbm = pd.read_json(DATA_FILES.wbm_computed_structure_entries).set_index(Key.mat_id)

df_wbm.computed_structure_entry = df_wbm.computed_structure_entry.map(
    ComputedStructureEntry.from_dict
)


# %% query all ComputedStructureEntries (CSE) from MP incl. final structure
# use inc_structure='initial' to fetch initial structures
mp_cse_path = f"{MODULE_DIR}/2022-01-25-mp-cses-queried.json.gz"
if os.path.exists(mp_cse_path):
    df_mp = pd.read_json(mp_cse_path, orient="split")
else:
    mp_cses = MPRester().get_entries({}, inc_structure=True)

    df_mp = pd.DataFrame(mp_cses).rename(columns={0: "computed_structure_entry"})

    for col in ["composition", "energy", "entry_id"]:
        df_mp[col] = [cse[col] for cse in df_mp.computed_structure_entry]

    df_mp = df_mp.set_index("entry_id")
    df_mp.index.name = Key.mat_id
    df_mp["composition"] = df_mp.composition.map(Composition)

    # got 126,335 CSEs
    df_mp.to_json(
        "2022-01-25-mp-cses-queried-with-cols.json.gz",
        default_handler=lambda x: x.as_dict(),
    )


# %%
mp_entries = [
    PDEntry(row.composition, energy=row.energy, name=row.Index)
    for row in df_mp.itertuples()
]


# %%
mp_ppd = PatchedPhaseDiagram(mp_entries, verbose=True)

# save to disk (last run on 2022-01-25)
with gzip.open(f"{MODULE_DIR}/{today}-ppd-mp.pkl.gz", "wb") as zip_file:
    pickle.dump(mp_ppd, zip_file)

# load from disk
# with gzip.open(f"{MODULE_DIR}/ppd-mp-2022-01-25.pkl.gz", mode="rb") as zip_file:
#     mp_ppd = pickle.load(zip_file)


# %%
# remove single-element calculations from WBM so that we only use MP entries as
# terminal references for formation energy
df_wbm["n_elements"] = df_wbm[Key.formula].map(Composition).map(len)

warnings.filterwarnings(action="ignore", category=UserWarning, module="pymatgen")
wbm_computed_struct_entries: list[ComputedStructureEntry] = df_wbm.query(
    "n_elements > 1"
).computed_structure_entry.map(ComputedStructureEntry.from_dict)


wbm_processed_struct_entries = MaterialsProject2020Compatibility().process_entries(
    wbm_computed_struct_entries, verbose=True
)

n_skipped = len(df_wbm) - len(wbm_processed_struct_entries)
print(f"{n_skipped:,} ({n_skipped / len(df_wbm):.1%}) entries not processed")


# %% merge MP and WBM entries into a single PatchedPhaseDiagram
mp_wbm_ppd = PatchedPhaseDiagram(
    wbm_processed_struct_entries + mp_entries, verbose=True
)


# %%
with gzip.open(f"{MODULE_DIR}/2022-01-25-ppd-mp+wbm.pkl.gz", "wb") as zip_file:
    pickle.dump(mp_wbm_ppd, zip_file)


# %% --- EDA of MaterialsProject2020Compatibility energy corrections ---
# vs WBM corrections which used MaterialsProjectCompatibility (without 2020)
correction_cols = [
    "correction",
    "correction_per_atom",
    "correction_uncertainty",
    "correction_uncertainty_per_atom",
    "energy",
    "energy_adjustments",
    Key.e_per_atom,
    "entry_id",
    "name",
    "uncorrected_energy",
    "uncorrected_energy_per_atom",
]

df_corrections = pd.DataFrame(
    [
        [getattr(entry, x) for x in correction_cols]
        for entry in wbm_processed_struct_entries
    ],
    columns=correction_cols,
).set_index("entry_id")

n_uncorrected = sum(df_corrections.correction == 0)
print(
    f"no corrections applied to {n_uncorrected:,} / {len(df_corrections):,} = "
    f"{n_uncorrected / len(df_corrections):.1%}\n"
)

print("energy corrections in eV per atom:")
print(df_corrections.correction_per_atom.describe())


# %%
df_corrections["e_form_wbm"] = df_wbm.e_form
df_corrections["energy_wbm"] = df_wbm.energy
df_corrections["energy_per_atom_wbm"] = df_wbm.energy / df_wbm[Key.formula].map(
    lambda x: Composition(x).num_atoms
)

df_corrections["e_form_mp2020"] = [
    mp_ppd.get_form_energy_per_atom(entry)
    for entry in tqdm(wbm_processed_struct_entries)
]

df_corrections.filter(like="e_form_").describe()

fig = px.scatter(
    df_corrections,
    x="e_form_mp2020",
    y="e_form_wbm",
    labels={
        "energy_per_atom_wbm": "WBM Energy/atom (eV)",
        Key.e_per_atom: "MP 2020 Compat Energy/atom (eV)",
    },
    marginal_x="violin",
    marginal_y="violin",
)
fig.write_image(f"{today}-wbm-vs-mp-2020-compat-e-form.png", scale=2)


abs_err_wbm_vs_mp2020_corrections = (
    df_corrections.energy_per_atom_wbm - df_corrections.energy_per_atom
).abs()
print("absolute error in eV per atom between WBM and MP 2020 corrections:")
print(abs_err_wbm_vs_mp2020_corrections.describe().round(4))


# %%
px.histogram(
    df_corrections,
    x=["energy", "uncorrected_energy"],
    nbins=1000,
    barmode="overlay",
    log_y=True,
)


# %%
px.histogram(
    df_corrections,
    x=["energy_wbm", "energy"],
    nbins=1000,
    barmode="overlay",
    range_x=[-200, 10],
    labels={
        "energy_wbm": "WBM Energy/atom (eV)",
        "y": "MP 2020 Compat Energy/atom (eV)",
    },
)


# %%
px.histogram(
    df_corrections, x=["correction"], nbins=1000, barmode="overlay", log_y=True
)
