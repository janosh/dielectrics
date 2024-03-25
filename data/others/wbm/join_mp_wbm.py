# %%
import os

import pandas as pd
from matbench_discovery.data import DATA_FILES
from matbench_discovery.data import df_wbm as df_summary
from pymatgen.ext.matproj import MPRester

from dielectrics import DATA_DIR, Key
from dielectrics import plots as plots


module_dir = os.path.dirname(__file__)


# %%
df_mp_wbm = pd.read_csv(f"{module_dir}/data/mp+wbm-all.csv.bz2").set_index(Key.mat_id)

df_wbm = pd.read_json(DATA_FILES.wbm_computed_structure_entries).set_index(Key.mat_id)
df_wbm[list(df_summary)] = df_summary


# %%
n_wbm = sum(df_mp_wbm.index.str.startswith("wbm-"))
n_mp = sum(df_mp_wbm.index.str.startswith(("mp-", "mvc-")))
print(
    f"combined MP+WBM: {len(df_mp_wbm):,}, of which {n_wbm:,} WBM materials, "
    f"{n_mp:,} MP materials"
)
# combined MP+WBM: 319,601, of which 220,751 WBM materials, 98,850 MP materials
assert n_wbm + n_mp == len(df_mp_wbm)


# %% Rhys selected MP entries with less than 64 sites and less than 16 Wyckoff
# positions, leaves about ~108k materials
material_ids = [x for x in df_mp_wbm.index if x.startswith("mp-")]

mp_data = MPRester().query(
    {"material_id": {"$in": material_ids}}, ["material_id", "bandgap"]
)

df_mp_wbm["bandgap"] = df_wbm.bandgap.append(
    pd.DataFrame(mp_data).set_index(Key.mat_id).bandgap
)

# 3,314 MP materials with mvc-... IDs have no band gap, we drop them
df_mp_wbm = df_mp_wbm.query("bandgap.notnull()")


# %%
[[ax1, ax2, ax3]] = df_mp_wbm.hist(figsize=[20, 4], bins=80, log=True, layout=[1, 3])

ax1.set_xlabel("VASP energy [eV]")
ax2.set_xlabel("formation energy [eV/atom]")
ax3.set_xlabel("band gap [eV]")
# plt.savefig("plots/wbm+mp-hists.pdf")


# %%
n_metals = sum(df_mp_wbm.bandgap == 0)

print(
    f"{n_metals:,} / {len(df_mp_wbm):,} = {n_metals / len(df_mp_wbm):.1%} of materials "
    "in combined MP + WBM dataset are metals"
)
# 243,095 / 319,601 = 76.1% of materials in combined MP + WBM dataset are metals


# %%
df_mp_wbm.to_json(
    f"{module_dir}/data/mp+wbm-all.json.gz", default_handler=lambda x: x.as_dict()
)

df_mp_wbm.query("bandgap > 0").to_json(
    f"{module_dir}/data/mp+wbm-bandgap>0.json.gz", default_handler=lambda x: x.as_dict()
)


# %% Create MP+WBM screening data set by applying the same filter criteria as in
# mp_exploration/fetch_diel_data.py
df_wbm["n_elems"] = [len(x["composition"]) for x in df_wbm.computed_structure_entry]
df_wbm_screen = df_wbm.query(
    "bandgap > 0.5 & n_sites < 40 & e_above_hull < 0.1 & n_elems <= 5"
)
df_wbm.e_above_hull.describe()

print(
    f"leaves {len(df_wbm_screen):,} out of {len(df_wbm):,} "
    f"({len(df_wbm_screen) / len(df_wbm):.1%})"
)
print(f"excluded by {sum(df_wbm.bandgap < 0.5)=:,}")
print(f"excluded by {sum(df_wbm.n_sites > 40)=:,}")
print(f"excluded by {sum(df_wbm.e_above_hull > 0.1)=:,}")
print(f"excluded by {sum(df_wbm.n_elems > 5)=:,}")

# leaves 22,026 out of 257,489 (8.6%)
# excluded by sum(df_all_steps.bandgap < 0.5) = 229,989
# excluded by sum(df_all_steps.n_sites > 40) = 158
# excluded by sum(df_all_steps.e_above_hull > 0.1) = 109,622
# excluded by sum(df_all_steps.n_elems > 5) = 0


# %%
df_mp_screening_set = pd.read_csv(f"{DATA_DIR}/mp-exploration/mp-diel-screen.csv.bz2")


# %%
print(f"{df_wbm_screen.columns.intersection(df_mp_screening_set.columns)=}")
print(f"{df_wbm_screen.columns.difference(df_mp_screening_set.columns)=}")
print(f"{df_mp_screening_set.columns.difference(df_wbm_screen.columns)=}")

df_wbm_screen[Key.mat_id] = df_wbm_screen.index

print(f"{len(df_mp_screening_set)=:,} + {len(df_wbm_screen)=:,} ")
# len(df_mp_screen) = 25,296 + len(df_wbm_screen) = 22,026

df_mp_wbm_screen = df_mp_screening_set.rename(
    columns={"formula": "composition"}
).append(df_wbm_screen)

df_mp_wbm_screen.to_json(
    f"{module_dir}/data/mp+wbm-for-screen.json.gz",
    default_handler=lambda x: x.as_dict(),
)
