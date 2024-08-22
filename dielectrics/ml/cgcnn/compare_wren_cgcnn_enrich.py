# %%
import pandas as pd

from dielectrics import DATA_DIR, Key
from dielectrics.plots import plt  # side-effect import sets plotly template and plt.rc


# %%
expt = "enrich-big"

df_diel_train = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-{expt}-train.json.bz2")
df_diel_train.index.name = Key.mat_id
df_diel_train = df_diel_train.rename(columns={"band_gap": Key.bandgap})


df_diel_test = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-{expt}-test.json.bz2")

df_diel_test = df_diel_test.rename(columns={"band_gap": Key.bandgap})


# %%
model_1 = "cgcnn"
model_2 = "wren"

df_enrich_1 = pd.read_csv(
    f"{DATA_DIR}/cgcnn/results/{model_1}-refract-{expt}.csv"
).set_index(Key.mat_id)
df_enrich_2 = pd.read_csv(
    f"{DATA_DIR}/wren/enrich/{model_2}-refract-{expt}.csv"
).set_index(Key.mat_id)

for df in [df_enrich_1, df_enrich_2]:
    df.columns = df.columns.str.replace("_n0", "")
    df[Key.bandgap] = df_diel_test[Key.bandgap]
    df[Key.fom] = df[Key.bandgap] * df.n_pred**2


# %%
axs = df_enrich_1.hist(
    ["n_pred", Key.fom], figsize=[10, 5], bins=50, alpha=0.7, label=model_1
)
df_enrich_2.hist(["n_pred", Key.fom], bins=50, alpha=0.7, ax=axs, label=model_2)
plt.legend()
plt.suptitle(f"{model_1.title()} vs {model_2.title()} histogram")
# plt.savefig(f"{PAPER_FIGS}/{model_1}-vs-{model_2}-hist-n+fom.pdf")


# %%
top_100_n_target = df_enrich_2.n_target.nlargest(100)
top_100_n_pred = df_enrich_2.n_pred.nlargest(100)

ax = top_100_n_target.hist(bins=100, alpha=0.9, label="n")
top_100_n_pred.hist(ax=ax, bins=40, alpha=0.9, label="n_pred")

plt.legend()
plt.xscale("log")


# %% Number of top 100 predicted n materials that are in actual top 100
df_top_100_diel_n = df_diel_train.nlargest(100, "n")
n_found = sum(df_top_100_diel_n.index.isin(df_enrich_1.nlargest(100, "n_pred").index))
print(
    f"{model_1} has {n_found} matches between predicted and actual top 100 "
    f"FoM materials out of {len(df_enrich_1):,} candidates"
)
# cgcnn has 7 matches between predicted and actual top 100 FoM materials out of 41,635
# candidates


# %%
for df, model_name in [(df_enrich_1, model_1), (df_enrich_2, model_2)]:
    df_top_100_diel_n[f"n_pred_{model_name}"] = df.n_pred
ax = df_top_100_diel_n.plot.scatter(x="n", y=f"n_pred_{model_1}", label=model_1)
df_top_100_diel_n.plot.scatter(
    x="n", y=f"n_pred_{model_2}", ax=ax, color="red", label=model_2
)
ax.axline([5, 5], [6, 6], color="gray", linestyle="dotted", zorder=0)
# plt.savefig(f"{PAPER_FIGS}/enrich-{expt}-n-true-vs-pred-bar.pdf")


# %%
select_mask = df_top_100_diel_n.index.isin(df_enrich_1.nlargest(100, "n_pred").index)

df_top_100_diel_n.plot.bar(
    y="n", color=["red" if x else "blue" for x in select_mask], figsize=[12, 8]
)


# %% --------------------
# same plots but sorted by figure of merit instead of refractive index
df_enrich_1[Key.bandgap] = df_diel_train[Key.bandgap]
df_enrich_1[Key.fom] = df_enrich_1[Key.bandgap] * df_enrich_1.n_target**2
df_enrich_1["fom_pred"] = df_enrich_1[Key.bandgap] * df_enrich_1.n_pred**2


# %%
df_enrich_1.plot.scatter(x=Key.fom, y="fom_pred")
plt.axis("square")


# %%
top_100_fom_1 = df_enrich_1.nlargest(100, Key.fom)
sum(top_100_fom_1.index.isin(df_enrich_1.nlargest(100, "fom_pred").index))


# %%
top_100_fom_1["fom_cgcnn"] = df_enrich_1.fom_pred
top_100_fom_1.plot.bar(y=[Key.fom, "fom_cgcnn"], figsize=[14, 8], width=1)
plt.yscale("log")
# plt.savefig(f"{PAPER_FIGS}/enrich-fom-true-vs-pred-bar.pdf")


# %%
select_mask = top_100_fom_1.index.isin(df_enrich_1.nlargest(100, "fom_pred").index)

top_100_fom_1.plot.bar(
    y=Key.fom,
    color=["red" if x else "blue" for x in select_mask],
    figsize=[12, 8],
)
plt.yscale("log")
# plt.savefig(f"{PAPER_FIGS}/enrich-fom-(non-)selected-bar.pdf")
