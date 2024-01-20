# %%
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.transforms import blended_transform_factory
from pymatgen.core import Composition
from pymatviz import ptable_heatmap

from dielectrics import DATA_DIR, Key
from dielectrics.element_substitution import df_struct_apply_elem_substitution


# %%
df_ene = pd.read_csv(
    f"{DATA_DIR}/wren/screen/wren-e_form-ens-rhys-screen-mp-top1k-fom-elemsub.csv"
).set_index(Key.mat_id)

df_elec = pd.read_csv(
    f"{DATA_DIR}/wren/screen/wren-diel-elec-ens-trained-on-all-mp-screen-mp-top1k-fom-elemsub.csv"
).set_index(Key.mat_id)

df_ionic = pd.read_csv(
    f"{DATA_DIR}/wren/screen/wren-diel-ionic-ens-trained-on-all-mp-screen-mp-top1k-fom-elemsub.csv"
).set_index(Key.mat_id)

df_bandgap = pd.read_csv(
    f"{DATA_DIR}/wren/screen/wren-bandgap-mp+wbm-ensemble-screen-mp-top1k-fom-elemsub.csv"
).set_index(Key.mat_id)


for df in [df_ene, df_elec, df_ionic, df_bandgap]:
    # Replace NaN values in formula/composition columns stemming from incorrectly
    # parsed chemical formula for sodium nitride with string 'NaN'.
    df.formula.fillna("NaN", inplace=True)  # noqa: PD002


# %%
dfs = (df_elec, df_ionic, df_bandgap)
cols = ("diel_elec_wren", "diel_ionic_wren", "bandgap_wren")

id_cols = ["formula", "wyckoff", "e_form_wren", "e_form_wren_std"]
ene_cols = ["e_above_hull_wren", "e_above_hull_wren_std_adj"]
df_wren = df_ene[id_cols + ene_cols].copy()

for col, df in zip(cols, dfs, strict=True):
    df_wren[col] = df.filter(like="pred_n").mean(1)
    df_wren[f"{col}_std"] = (
        df.filter(like="pred_n").var(1)
        # average aleatoric uncertainties in quadrature
        + (df.filter(like="ale_n") ** 2).mean(1).fillna(0)
    ) ** 0.5


# %%
df_wren[Key.diel_total_wren] = df_wren.diel_elec_wren + df_wren.diel_ionic_wren

df_wren[Key.fom_wren] = (df_wren.diel_total_wren * df_wren.bandgap_wren).clip(0)

df_wren["fom_wren_rank"] = df_wren.fom_wren.rank(ascending=False).astype(int)


# df_wren.round(4).to_csv(
#     f"{DATA_DIR}/wren/screen/wren-ens-screen-mp-top1k-fom-elemsub.csv"
# )

# new col intentionally not saved to CSV
df_wren["fom_wren_rank_size"] = len(df_wren)


# %% calculate and analyze fom_wren_std
df_wren["n_elems"] = df_wren.formula.map(Composition).map(len)
df_wren.n_elems.value_counts()


df_wren.diel_total_wren_std = (
    df_wren.diel_elec_wren_std**2 + df_wren.diel_ionic_wren_std**2
) ** 0.5

# to get FoM uncertainty, sum relative uncertainties in band gap and diel total in
# quadrature, then multiply by abs(FoM)
df_wren["fom_wren_std"] = (
    (df_wren.diel_total_wren * df_wren.bandgap_wren_std) ** 2
    + (df_wren.bandgap_wren * df_wren.diel_total_wren_std) ** 2
) ** 0.5

fom_std_spearmen = df_wren[["fom_wren_std", Key.fom_wren]].corr(method="spearman")
print(f"FoM Wren with std correlation: {fom_std_spearmen}")

df_wren.query("fom_wren > 100 and diel_total_wren < 2000").sample(5000).plot.scatter(
    x=Key.diel_total_wren, y=Key.fom_wren, yerr="fom_wren_std"
)

df_wren.query("fom_wren > 100 and diel_total_wren < 2000").sample(5000).plot.scatter(
    x="bandgap_wren", y=Key.fom_wren, yerr="fom_wren_std"
)

ax1 = (df_wren.fom_wren - 0.5 * df_wren.fom_wren_std).hist(bins=100, log=True)
ax1.set(title="fom_wren - fom_wren_std")
plt.show()
ax2 = df_wren.fom_wren.hist(bins=100, log=True)
ax2.set(title=Key.fom_wren)

# pick as uncertainty adjusted figure of merit FoM_std_adj = FoM - c * FoM_std
df_wren["fom_wren_std_adj"] = df_wren.fom_wren - 0.5 * df_wren.fom_wren_std

df_wren["fom_wren_std_adj_rank"] = df_wren.fom_wren_std_adj.rank(
    ascending=False
).astype(int)


# %%
df_all_mp_formulas = pd.read_csv(
    f"{DATA_DIR}/mp-exploration/all-mp-formulas.csv"
).set_index(Key.mat_id)


# %% makes little difference whether comparing formula strings or Composition objects
df_clean = df_wren.copy()

is_mp_formula = df_clean.formula.isin(df_all_mp_formulas.formula)

print(
    "removing compositions with existing MP dielectric properties: "
    # stands to reason MP already took the lowest lying polymorph so no point checking
    # any other material with same composition
    f"{len(df_clean):,} -> {sum(~is_mp_formula):,}"
)
df_clean = df_clean[~is_mp_formula]

n_elem_2to4 = (df_clean.n_elems > 1) & (df_clean.n_elems < 5)
print(f"removing n_elems = 1 or > 4: {len(df_clean):,} -> {sum(n_elem_2to4):,}")
# drop unary and higher-than quaternary compounds, former won't be novel, latter hard
# to make
df_clean = df_clean[n_elem_2to4]

small_bandgap = df_clean.bandgap_wren < 0.5
print(f"removing small bandgap: {len(df_clean):,} -> {sum(~small_bandgap):,}")
# drop unary and higher-than quaternary compounds, former won't be novel, latter hard
# to make
df_clean = df_clean[~small_bandgap]


# %%
axs1 = df_clean[["e_form_wren", "bandgap_wren"]].hist(bins=100, figsize=[18, 4])
axs2 = df_clean[
    [Key.fom_wren, "diel_ionic_wren", Key.diel_total_wren, "diel_elec_wren"]
].hist(bins=100, figsize=[18, 8], log=True)


# mark top 1k threshold as that's about how many candidates we can run DFT on
for ax in (*axs1.flat, *axs2.flat):
    xloc = df_clean[ax.get_title()].nlargest(1000).min()
    ax.axvline(xloc, color="darkorange", linestyle="dashed", linewidth=2)

    trans = blended_transform_factory(
        x_transform=ax.transData, y_transform=ax.transAxes
    )
    ax.annotate("top 1k", xy=(xloc, 1.02), xycoords=trans, color="darkorange")


# %%
ptable_heatmap(df_clean.formula)
ptable_heatmap(df_clean.nlargest(1000, "fom_wren_std_adj").formula)
# no change in elemental prevalence from selecting the top 1k Wren-predicted FoMs


# %%
df_mp_diel = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-train.json.bz2")


# %%
keep_top = 4000
top_fom: pd.DataFrame = df_clean.nlargest(4000, "fom_wren_std_adj")


top_fom = top_fom.reset_index()
top_fom.index = top_fom.material_id.str.split(":").str[0]
top_fom["structure"] = df_mp_diel.structure
top_fom = top_fom.rename(columns={"structure": "orig_structure"})
df_struct_apply_elem_substitution(top_fom, strict=False, verbose=True)

print(f"{len(top_fom)} of {keep_top} completed element substitution")


# %%
top_fom.to_json(
    f"{DATA_DIR}/wren/screen/2022-01-30-wren-ens-screen-mp-top1k-fom-elemsub.json.gz",
    default_handler=lambda x: x.as_dict(),
)


# %% Wren predicts higher dielectric constants that it was trained on so this should not
# stop us from pushing the dielectric Pareto front
hist_args = dict(bins=100, log=True, density=True, alpha=0.8, layout=(1, 3))

axs = df_wren.query("0 < diel_total_wren < 800")[
    ["diel_elec_wren", "diel_ionic_wren", Key.diel_total_wren]
].hist(figsize=[15, 3], **hist_args)

df_mp_diel.query("0 < diel_total_mp < 800")[
    ["diel_elec_mp", "diel_ionic_mp", "diel_total_mp"]
].hist(ax=axs, **hist_args)

plt.legend(["Wren", "MP"])
