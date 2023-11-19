# %%
import pandas as pd
from matbench_discovery.data import DATA_FILES
from matbench_discovery.data import df_wbm as df_summary
from pymatgen.ext.matproj import MPRester
from pymatviz import ptable_heatmap

from dielectrics import DATA_DIR, diel_total_wren_col, id_col
from dielectrics.plots import plt


# %%
df_elec = pd.read_csv(
    f"{DATA_DIR}/wren/screen/wren-screen-mp+wbm-diel-elec-ensemble-robust-trained-on-all-mp.csv"
).set_index(id_col)
df_ionic = pd.read_csv(
    f"{DATA_DIR}/wren/screen/wren-screen-mp+wbm-diel-ionic-ensemble-robust-trained-on-all-mp.csv"
).set_index(id_col)


# %%
df_wren = df_ionic[["formula", "wyckoff", "bandgap_pbe"]].copy()

df_wren["diel_elec_wren"] = df_elec.filter(like="_pred_n").mean(1)
df_wren["diel_ionic_wren"] = df_ionic.filter(like="_pred_n").mean(1)
df_wren[diel_total_wren_col] = df_wren.diel_elec_wren + df_wren.diel_ionic_wren

df_wren["fom_wren"] = df_wren.diel_total_wren * df_wren.bandgap_pbe

df_wren["fom_wren_rank"] = df_wren.fom_wren.rank(ascending=False).astype(int)

df_wren["fom_wren_rank_size"] = len(df_wren)


# %%
df_wren.hist(bins=50, figsize=[12, 8], log=True)

plt.suptitle(f"{len(df_wren) = :,}", y=1.08)


# %%
n_from_mp, n_from_wbm = (sum(df_wren.index.str.startswith(s)) for s in ("mp-", "wbm-"))

assert n_from_mp + n_from_wbm == len(df_wren)

print(f"{n_from_mp = :,}\t{n_from_wbm = :,}\ttotal = {len(df_wren):,} non-metals")

df_top_1k = df_wren.nlargest(1000, "fom_wren")
df_top_1k.describe().round(2)

#       bandgap_pbe   diel_elec_wren    diel_ionic_wren     diel_total_wren     fom_wren
# mean      2.96            24.11           100.85          124.96              266.17
# std       1.53            107.21          124.62          175.82              227.96
# min       0.09            1.20            1.83            11.89               145.89
# 50%       2.90            5.06            66.69           75.71               197.72
# max       17.90           1350.34         1734.77         2621.68             3628.10


# %%
df_mp_diel = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-train.json.bz2")

# discard negative and unrealistically large dielectric constants
df_mp_diel = df_mp_diel.query("0 < diel_total_mp < 2000").round(3)


# %%
plt.figure(figsize=(12, 8))

plt.title(f"{len(df_mp_diel)} MP materials with computed dielectric properties")

plt.hexbin(df_mp_diel.diel_total_mp, df_mp_diel.bandgap_mp, mincnt=1)

df_top_1k.plot.scatter(x=diel_total_wren_col, y="bandgap_pbe", ax=plt.gca())

plt.xlim((0, 1500))

plt.colorbar(label="Density")
plt.xlabel(r"$\epsilon_\mathrm{tot}$")
plt.ylabel(r"PBE Band Gap $E_\mathrm{gap}$ / eV")

plt.legend()


# %%
mp_data = MPRester().query(
    criteria={id_col: {"$in": list(df_top_1k.index)}},
    properties=[
        id_col,
        "final_structure",
        "final_energy",
        "formation_energy_per_atom",
        "e_above_hull",
    ],
)

df_mp = pd.DataFrame(mp_data).set_index(id_col)
df_mp.columns = df_mp.columns.str.replace("final_", "")
df_mp = df_mp.rename(
    columns={"formation_energy_per_atom": "e_form", "e_above_hull": "e_hull"}
)


# %%
df_wbm = pd.read_json(DATA_FILES.wbm_computed_structure_entries).set_index(id_col)
df_wbm[list(df_summary)] = df_summary
df_wbm = df_wbm.query("bandgap_pbe > 0")  # discard metals

df_top_1k["structure"] = df_wbm.computed_structure_entry.map(
    lambda cse: cse.structure
).append(df_mp.structure)
cols = ["energy", "e_form", "e_hull"]
df_top_1k[cols] = df_wbm.append(df_mp)[cols]

assert not any(
    nans_per_col := df_top_1k.isna().sum()
), f"some columns have missing data:\n{nans_per_col}"


# %%
df_top_1k.to_json(
    f"{DATA_DIR}/wren/screen/top-diel-wren-ens-robust-for-vasp-val.json.gz",
    default_handler=lambda x: x.as_dict(),
)

# df_top_1k = pd.read_json(
#     f"{DATA_DIR}/wren/screen/top-diel-wren-ens-robust-for-vasp-val.json.gz"
# )


# %% ------------------------------------------------------
# Wren predictions from non-robust ionic and electronic ensembles with std adjusted FoM
# FoM = (diel_total_wren - diel_total_wren_std) * bandgap_pbe
df_elec = pd.read_csv(
    f"{DATA_DIR}/wren/screen/wren-mp+wbm-for-screen-diel-elec-ensemble-trained-on-all-mp.csv"
).set_index(id_col)
df_ionic = pd.read_csv(
    f"{DATA_DIR}/wren/screen/wren-mp+wbm-for-screen-diel-ionic-ensemble-trained-on-all-mp.csv"
).set_index(id_col)

df_mp_wbm_screen = pd.read_json(f"{DATA_DIR}/wbm/mp+wbm-for-screen.json.gz").set_index(
    id_col
)


# %%
df_wren = df_ionic[["formula", "wyckoff"]].copy()

df_wren["diel_elec_wren"] = df_elec.filter(like="_pred_n").mean(1)
df_wren["diel_elec_wren_std"] = df_elec.filter(like="_pred_n").std(1)

df_wren["diel_ionic_wren"] = df_ionic.filter(like="_pred_n").mean(1)
df_wren["diel_ionic_wren_std"] = df_ionic.filter(like="_pred_n").std(1)

df_wren[diel_total_wren_col] = df_wren.diel_elec_wren + df_wren.diel_ionic_wren
df_wren["diel_total_wren_std"] = (
    df_wren.diel_elec_wren_std**2 + df_wren.diel_ionic_wren_std**2
) ** 0.5


df_wren[list(df_mp_wbm_screen)] = df_mp_wbm_screen
df_wren = df_wren.rename(columns={"bandgap": "bandgap_pbe"})

df_wren["fom_wren"] = df_wren.diel_total_wren * df_wren.bandgap_pbe
df_wren["fom_wren_std_adj"] = (
    df_wren.diel_total_wren - df_wren.diel_total_wren_std
) * df_wren.bandgap_pbe

df_wren["fom_wren_rank"] = df_wren.fom_wren.rank(ascending=False).astype(int)
df_wren["fom_wren_std_adj_rank"] = df_wren.fom_wren_std_adj.rank(
    ascending=False
).astype(int)

df_wren["fom_wren_rank_size"] = len(df_wren)


# %%
df_wren.filter(like="diel").hist(figsize=[12, 8], bins=50, log=True)

plt.suptitle(f"{len(df_wren):,} samples", y=1.02)


# %%
ptable_heatmap(df_wren.nlargest(1000, "fom_wren").formula, heat_label="percent")

ptable_heatmap(df_wren.sample(1000).formula, heat_label="percent")


# %%
df_wren.structure.update(
    df_wren.pop("computed_structure_entry").dropna().map(lambda x: x.structure)
)

df_wren.isna().sum()


# %%
df_top_1k = df_wren.nlargest(1000, "fom_wren_std_adj")
df_top_1k.describe().round(2)


# %%
df_top_1k.to_json(
    f"{DATA_DIR}/wren/screen/top-diel-wren-ens-std-adj-for-vasp-val.json.gz",
    default_handler=lambda x: x.as_dict(),
)

# df_top_1k = pd.read_json(
#     f"{DATA_DIR}/wren/screen/top-diel-wren-ens-std-adj-for-vasp-val.json.gz"
# )
