# %%
import pandas as pd
from pymatgen.core import Composition
from pymatgen.ext.matproj import MPRester
from pymatviz import count_elements, ptable_heatmap, ptable_heatmap_ratio
from tqdm import tqdm

from dielectrics import DATA_DIR, Key
from dielectrics.db.fetch_data import df_diel_from_task_coll
from dielectrics.element_substitution import (
    load_icsd_trans_mat,
    mp_atom_nums,
    replace_elems_in_aflow_wyckoff,
    replace_similar_elem,
)


# %% original Wren-single candidates from MP+WBM
# df_wren_single = pd.read_csv(
#     f"{DATA_DIR}/wren/screen/wren-diel-single-robust-mp+wbm-fom-elemsub-seeds.csv"
# )

df_vasp_ens_std_adj = df_diel_from_task_coll(
    {"series": "MP+WBM top 1k FoM std-adjusted by Wren diel ens"}
)

df_elem_sub_seeds = df_vasp_ens_std_adj.nlargest(200, Key.fom_pbe)


# %%
df_mp_diel = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-train.json.bz2")

# discard unstable and negative and unrealistically large dielectric constants
df_mp_diel = df_mp_diel.query("0 < diel_total_mp < 2000 and e_above_hull < 0.1")

df_elem_sub_seeds = df_mp_diel.nlargest(1000, Key.fom_mp)


# %%
trans_mat = load_icsd_trans_mat()

df_elem_sub_seeds["elem_list"] = df_elem_sub_seeds[Key.wyckoff].map(
    lambda x: tuple(x.split(":")[1].split("-"))
)


# %%
dfs, n_iters = [], 1000
for _ in tqdm(range(n_iters)):
    df_tmp = df_elem_sub_seeds[[Key.mat_id, Key.formula, "elem_list", Key.wyckoff]]

    # elem_swap is a tuple of two element symbols: (elem_orig, elem_new)
    df_tmp["elem_swap"] = df_tmp.elem_list.map(
        lambda elem_list: replace_similar_elem(trans_mat, mp_atom_nums, elem_list)
    )

    dfs.append(df_tmp)

df_elemsub = pd.concat(dfs)

n_subs = len(df_elemsub)
df_elemsub = df_elemsub.drop_duplicates(subset=["elem_list", "elem_swap"])

n_unique = len(df_elemsub)

print(
    f"Performed {n_subs:,} substitutions with {n_iters:,} iterations. {n_unique:,} of "
    f"them are unique. Now applying element swaps in Aflow wyckoff strings and "
    "old compositions. This takes a while."
)

df_elemsub = df_elemsub.rename(columns={Key.formula: "orig_formula"})
df_elemsub[Key.formula] = df_elemsub["composition"] = ""

for idx, row in tqdm(enumerate(df_elemsub.itertuples()), total=n_unique):
    mat_id = row.Index

    df_elemsub.loc[idx, Key.mat_id] = f"{mat_id}:{'->'.join(row.elem_swap)}"

    swap_dict = dict([row.elem_swap])
    comp = Composition(row.orig_formula).replace(swap_dict)
    df_elemsub.loc[idx, "composition"] = comp
    df_elemsub.loc[idx, Key.formula] = comp.reduced_formula

    df_elemsub.loc[idx, Key.wyckoff] = replace_elems_in_aflow_wyckoff(
        row.wyckoff, dict([row.elem_swap])
    )


# %% https://ml-physics.slack.com/archives/DD8GBBRLN/p1624547833027400
df_clean = df_elemsub.copy()

pre_existing = df_clean[Key.wyckoff].isin(df_elem_sub_seeds[Key.wyckoff])
print(
    "removing Wyckoff strings already present in elemental substitution seeds: "
    f"{len(df_clean):,} -> {sum(~pre_existing):,}"
)
df_clean = df_clean[~pre_existing]

rare_earths = df_clean.composition.map(
    lambda comp: any(el.is_rare_earth_metal for el in comp)
)
print(f"removing rare earths: {len(df_clean):,} -> {sum(~rare_earths):,}")
df_clean = df_clean[~rare_earths]

noble_gases = df_clean.composition.map(lambda comp: any(el.is_noble_gas for el in comp))
print(f"removing nobel gases: {len(df_clean):,} -> {sum(~noble_gases):,}")
df_clean = df_clean[~noble_gases]

all_mp_formulas_csv = f"{DATA_DIR}/mp-exploration/all-mp-formulas.csv"
try:
    df_all_mp_formulas = pd.read_csv(all_mp_formulas_csv)
except FileNotFoundError:
    # %% if CSV doesn't exist, re-download all MP formulas
    with MPRester() as mpr:
        data = mpr.query({}, [Key.mat_id, "pretty_formula"], chunk_size=5000)

    df_all_mp_formulas = pd.DataFrame(data).set_index(Key.mat_id)
    df_all_mp_formulas = df_all_mp_formulas.rename(
        columns={"pretty_formula": Key.formula}
    )
    df_all_mp_formulas.round(4).to_csv(all_mp_formulas_csv)

# We may want to keep only keep new compositions when substituting on a thoroughly
# curated database like Materials Project since the formula already present is likely
# the lowest lying polymorph. For something like WBM, this is much less likely, so makes
# more sense to drop this filter.
# NOTE: be careful to compare strings with strings here, not strings with tuples or
# composition objects
prev_len = len(df_clean)
df_clean = df_clean.query("formula not in @df_all_mp_formulas.formula")
print(f"removing existing MP compositions: {prev_len:,} -> {len(df_clean):,}")

# removing Wyckoff strings already present in elemental subst. seeds: 187,176 -> 187,176
# removing rare earths: 187,176 -> 133,367
# removing nobel gases: 133,367 -> 133,241
# removing existing MP compositions: 133,241 -> 131,685


# %%
elem_counts = count_elements(df_clean[Key.formula])
orig_elem_counts = count_elements(df_clean.orig_formula)

ptable_heatmap(elem_counts, log=True)

ptable_heatmap_ratio(
    elem_counts, orig_elem_counts, cbar_title="substituted/original elements"
)


# %%
# df_clean[[Key.mat_id, "orig_formula", Key.wyckoff, Key.formula]].round(4).to_csv(
#     f"{DATA_DIR}/wren/screen/mp-top-fom-elemsub-for-wren-screening.csv"
# )
