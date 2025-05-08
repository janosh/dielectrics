# %%
import pandas as pd
from matbench_discovery.structure.prototype import get_protostructure_label
from pymatgen.core import Composition
from tqdm.notebook import tqdm

from dielectrics import DATA_DIR, Key
from dielectrics.mp_exploration import fetch_mp_dielectric_structures


"""
Fetch MP dielectric structures for training ML models and assemble screening set
defined by screening_set_filters.
"""

# %%
df_diel_train = fetch_mp_dielectric_structures({"has": "diel"})


# %%
screening_set_filters = {
    "has": {"$nin": ["diel"]},  # exclude materials already in training set
    "e_above_hull": {"$lte": 0.1},  # exclude non-stable materials
    "band_gap": {"$gte": 0.5},  # at least semiconductor band gap
    # i.e. exclude conductors since they don't have dielectric effect
    "nelements": {"$gte": 5, "$lte": 10},  # exclude elemental/overly complex stuff
    "nsites": {"$gte": 100},  # exclude huge unit-cells for computational efficiency
    # 2x of https://www-nature-com.ezp.lib.cam.ac.uk/articles/sdata2016134#Sec4
}
df_diel_screen = fetch_mp_dielectric_structures(screening_set_filters)


# %%
# Maximum observed refractive index is n = 38.6
# https://nature.com/articles/nature09776
print(
    f"{df_diel_train.n_mp.max()=:.1f}\n{sum(df_diel_train.n_mp > 38.6)} materials in "
    f"training set contains bigger-than-ever-experimentally-observed refractive index"
)


# %% add Wren's input column as Aflow-like Wyckoff encoding
df_diel_train[Key.wyckoff] = [
    get_protostructure_label(s) for s in tqdm(df_diel_train[Key.structure])
]
df_diel_screen[Key.wyckoff] = [
    get_protostructure_label(s) for s in tqdm(df_diel_screen[Key.structure])
]


# %% save data to disk
df_diel_train.to_json(
    f"{DATA_DIR}/mp-exploration/mp-diel-train.json.bz2",
    default_handler=lambda x: x.as_dict(),
)

df_diel_screen.to_json(
    f"{DATA_DIR}/mp-exploration/mp-diel-screen.json.bz2",
    default_handler=lambda x: x.as_dict(),
)


# %% load data from disk
# TODO what is train-2?
df_diel_train_2 = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-train-2.json.bz2")

df_diel_screen = pd.read_csv(f"{DATA_DIR}/mp-exploration/mp-diel-screen.csv.bz2")


# %% Enrichment Experiment 1 (small)
# combine 100 highest figure of merit (FoM) (n^2 * E_gap) materials with 900 more
# random materials from the remaining training set into an enrichment screening set
# if we manage to select based on ML predictions a higher than 10% proportion
# of the top 100, that's positive enrichment

df_diel_top_100 = df_diel_train.nlargest(100, Key.fom_mp)
df_diel_remain = df_diel_train.nlargest(100, Key.fom_mp)

df_diel_enrich_small_test = pd.concat(
    [df_diel_top_100, df_diel_remain.sample(900, random_state=0)]
)


df_diel_enrich_train = df_diel_train[
    ~df_diel_train.index.isin(df_diel_enrich_small_test.index)
]

df_diel_enrich_train.to_json(
    f"{DATA_DIR}/mp-exploration/mp-diel-enrich-small-train.json.bz2",
    default_handler=lambda x: x.as_dict(),
)

df_diel_enrich_small_test.to_json(
    f"{DATA_DIR}/mp-exploration/mp-diel-enrich-small-test.json.bz2",
    default_handler=lambda x: x.as_dict(),
)


# %% Enrichment Experiment 2 (big)
# combine 100 highest figure of merit materials with MP screening set
# see screen_data criteria above for what enters the screening set
df_diel_enrich_big_test = pd.concat([df_diel_screen, df_diel_top_100])

df_diel_remain.to_json(
    f"{DATA_DIR}/mp-exploration/mp-diel-enrich-big-train.json.bz2",
    default_handler=lambda x: x.as_dict(),
)

df_diel_enrich_big_test.to_json(
    f"{DATA_DIR}/mp-exploration/mp-diel-enrich-big-test.json.bz2",
    default_handler=lambda x: x.as_dict(),
)


# %% Create MP training dataset excluding all materials with chemical systems present in
# the Petousis experimental database.
df_exp = pd.read_csv(f"{DATA_DIR}/others/petousis/exp-petousis.csv")

df_exp["composition"] = df_exp[Key.formula].map(Composition)
df_exp["chem_sys"] = df_exp.composition.map(lambda comp: comp.chemical_system)
chem_sys_exp = df_exp.chem_sys.unique()

df_diel_train["chem_sys"] = df_diel_train[Key.formula].map(
    lambda comp: Composition(comp).chemical_system
)

df_diel_train.query("chem_sys not in @chem_sys_exp").to_json(
    f"{DATA_DIR}/mp-exploration/mp-diel-train-excl-petousis.json.bz2",
    default_handler=lambda x: x.as_dict(),
)
