# %%
import pandas as pd

from dielectrics import DATA_DIR, Key, PAPER_FIGS
from dielectrics.plots import plt


# %%
expt = "enrich-big"

df_diel_train = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-{expt}-train.json.bz2")

df_diel_screen = pd.read_csv(
    f"{DATA_DIR}/mp-exploration/mp-diel-screen.csv.bz2"
).set_index(Key.mat_id)


# %%
df_cgcnn = pd.read_csv(f"{DATA_DIR}/cgcnn/cgcnn-refract-{expt}.csv").set_index(
    Key.mat_id
)
df_wren = pd.read_csv(f"{DATA_DIR}/wren/enrich/wren-refract-{expt}.csv").set_index(
    Key.mat_id
)


# %% if there's mismatch between ML preds index and screening set index from updating
# the screening set criteria, filter ML preds
df_wren = df_wren[df_wren.index.isin(df_diel_screen.index.append(df_diel_train.index))]
df_cgcnn = df_cgcnn[
    df_cgcnn.index.isin(df_diel_screen.index.append(df_diel_train.index))
]


# %% --- Select CGCNN Screening Candidates ---
df_cgcnn = pd.concat([df_diel_screen, df_diel_train])
df_cgcnn["fom_cgcnn"] = df_cgcnn[Key.bandgap] * df_cgcnn.n_pred_n0**2
df_cgcnn.describe()


# %%
df_cgcnn.hist(figsize=[12, 8], bins=40, log=True)


# %%
df_cgcnn[Key.fom].hist(figsize=[12, 8], bins=50, log=True)
cgcnn_fom_cutoff = df_cgcnn[Key.fom].nlargest(100).min()
plt.axvline(cgcnn_fom_cutoff, color="red", label="top FoM cutoff")


# %%
cgcnn_for_vasp_val = df_cgcnn.nlargest(100, "fom_cgcnn")
cgcnn_for_vasp_val.describe()

cgcnn_for_vasp_val.to_json(
    f"{DATA_DIR}/cgcnn/top-cgcnn-for-vasp-val.json.bz2",
    default_handler=lambda x: x.as_dict(),
)


# %%
cgcnn_for_vasp_val.plot.scatter(
    x=Key.bandgap, y="n_pred_n0", c="fom_cgcnn", cmap="viridis", s="nsites"
)
# plt.savefig(f"{PAPER_FIGS}/cgcnn-for-vasp-val-bandgap-vs-n_pred.pdf")
