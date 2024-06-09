# %%
import pandas as pd
import plotly.express as px
from pymatgen.ext.matproj import MPRester
from pymatviz.powerups import add_identity_line

from dielectrics import Key, today
from dielectrics.db.fetch_data import df_diel_from_task_coll
from dielectrics.plots import plt


# %%
df_vasp = df_diel_from_task_coll({})  # get all static dielectric calcs

df_vasp["n_pbe"] = df_vasp[Key.diel_elec_pbe] ** 0.5


# %%
material_ids = [
    mat_id for mat_id in df_vasp.index.tolist() if mat_id.startswith(("mp-", "mvc-"))
]

with MPRester(use_document_model=False) as mpr:
    mp_docs = mpr.materials.dielectric.search(
        material_ids=material_ids,
    )

df_mp = pd.DataFrame(mp_docs).rename(columns={"formula_pretty": Key.formula})

df_mp = df_mp.set_index(Key.mat_id)


# %%
df_vasp["n_mp"] = df_mp.n

# number of identical material IDs in MP and our df
n_overlap = len(df_vasp.index.intersection(df_mp.index))
print(
    f"{today}: {n_overlap:,} / {len(df_vasp):,} = {n_overlap / len(df_vasp):.1%} of "
    "our materials have MP data"
)
# 2022-06-02: 236 / 2,532 = 9.3% of our materials have MP data
# 2024-04-19: 241 / 2,532 = 9.5% of our materials have MP data


# %%
# about 5 % of materials (ex.: YN, MnN, SeSn) deviate strongly from MP results
# perhaps due to being magnetic
ax = df_vasp.dropna(subset=["n_mp"]).plot.scatter(
    x="n_mp", y="n_pbe", c="nelements", cmap="viridis", s="nsites"
)
ax.set(yscale="log", xscale="log")
ax.set(xlabel="MP dielectric constant", ylabel="Our dielectric constant")
n_us_vs_n_mp_title = (
    f"{n_overlap:,} / {len(df_vasp):,} = {n_overlap / len(df_vasp):.0%} of "
    f"our materials have MP dielectric data,\nMarkers sized by num crystal sites"
)
ax.set_title(n_us_vs_n_mp_title, y=1.02)
ax.annotate(today, xy=(1, -0.2), xycoords=ax.transAxes)
ax.axline([10, 10], [11, 11], c="black", ls="dashed", alpha=0.5, zorder=0)
# plt.savefig("plots/us-vs-mp-refractive-n.pdf")


# %%
fig = px.scatter(
    df_vasp,
    x="n_mp",
    y="n_pbe",
    color="nelements",
    size=(size_col := "nsites"),
    log_x=True,
    log_y=True,
    range_x=[0.5, 200],
    range_y=[0.5, 200],
    labels={
        "n_mp": "MP refractive index",
        "n_pbe": "Our refractive index",
        "nelements": "Element<br>Count",
    },
    title=n_us_vs_n_mp_title,
)
add_identity_line(fig)
fig.update_traces(marker_sizeref=0.04, selector=dict(mode="markers"))


# %%
df_vasp_mp_wbm = df_diel_from_task_coll(
    {"series": "MP+WBM top 1k Wren-pred FoM EDIFF:1e-7 ENCUT:700"}
)


# %%
mp_docs = MPRester().query(
    {Key.mat_id: {"$in": list(df_vasp_mp_wbm.index)}, "has": "diel"},
    [Key.mat_id, "pretty_formula", "diel"],
)

df_mp = pd.DataFrame(mp_docs)

df_diel = pd.json_normalize(df_mp.diel)
df_mp[df_diel.add_suffix("_mp").columns.str.replace("poly_", "diel_")] = df_diel

df_mp = df_mp.set_index(Key.mat_id, drop=False)

df_mp[Key.diel_elec_wren] = df_mp[Key.diel_total_mp] - df_mp.diel_electronic_mp


# %%
diel_cols = [Key.diel_elec_pbe, Key.diel_total_pbe, Key.diel_ionic_pbe]
df_mp[diel_cols] = df_vasp_mp_wbm[diel_cols]


# %% IDs recomputed with tighter MP convergence EDIFF = 1e-7 eV, ENCUT = 700 eV
# mp-1113016, mp-1209295, mp-1214502, mp-1214569, mp-1218560, mp-12385, mp-1539667

fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(12, 5))

fig.suptitle("Us vs Materials Project electronic and total dielectric constant")

df_mp.plot.scatter(x="diel_electronic_mp", y=Key.diel_elec_pbe, ax=ax1)
ax1.set(xlabel=r"MP $\epsilon_\infty$", ylabel=r"our $\epsilon_\infty$")

df_mp.plot.scatter(x=Key.diel_total_mp, y=Key.diel_total_pbe, ax=ax2)
ax2.set(xlabel=r"MP $\epsilon_\mathrm{tot}$", ylabel=r"our $\epsilon_\mathrm{tot}$")

for ax in (ax1, ax2):
    ax.axline([2, 2], [3, 3], color="black", linestyle="dashed", alpha=0.5, zorder=0)

for row in df_mp.itertuples():
    mp_id = row[Key.mat_id]
    ax1.annotate(
        mp_id, (row.diel_electronic_mp, row.diel_elec_pbe), ha="center", va="top"
    )
    ax2.annotate(mp_id, (row.diel_total_mp, row.diel_total_pbe), ha="center", va="top")


# plt.savefig("plots/us-vs-mp-total-diel.png")
