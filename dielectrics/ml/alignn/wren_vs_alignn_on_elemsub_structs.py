# %%
import pandas as pd
from alignn.pretrained import get_figshare_model
from jarvis.core.graphs import Graph
from matbench_discovery.data import df_wbm as df_summary
from pymatgen.core import Structure
from pymatgen.io.jarvis import JarvisAtomsAdaptor
from pymatviz.powerups import add_identity_line
from sklearn.metrics import r2_score
from tqdm import tqdm

from dielectrics import DATA_DIR, PAPER_FIGS, Key, today
from dielectrics.db import db
from dielectrics.plots import px


__author__ = "Janosh Riebesell"
__date__ = "2022-06-06"


# %% load 1st step WBM step structures to compare Wren and Alignn performance on them
df_wbm_step1 = pd.read_json(f"{DATA_DIR}/wbm/step-1.json.bz2")
df_wbm_step1.index.name = Key.mat_id

df_wbm_step1[list(df_summary)] = df_summary
df_wbm_step1["jarvis_atoms"] = df_wbm_step1.computed_structure_entry.map(
    lambda cse: JarvisAtomsAdaptor().get_atoms(cse.structure)
)


# %%
df_wren_bandgaps = pd.read_csv(
    f"{DATA_DIR}/wren/bandgap/wren-bandgap-mp+wbm-ensemble.csv"
).set_index(Key.mat_id)

df_wren_bandgaps[Key.bandgap_wren] = df_wren_bandgaps.filter(like="pred_n").mean(1)
df_wren_bandgaps["bandgap_std"] = df_wren_bandgaps.filter(like="pred_n").std(1)

df_wbm_step1[Key.bandgap_wren] = df_wren_bandgaps[Key.bandgap_wren]


# %%
df_elemsub_wren = pd.read_json(
    f"{DATA_DIR}/element-substitution/wren-elemsub-mp+wbm-substituted-structs.json.bz2"
).set_index([Key.mat_id, Key.formula])


# %%
filters = {"task_label": "structure optimization", Key.bandgap_wren: {"$exists": True}}
fields = [
    Key.mat_id,
    "formula_pretty",
    "output.bandgap",
    Key.bandgap_wren,
    "input.structure",
    "output.structure",
    Key.e_above_hull_pbe,
    Key.e_above_hull_wren,
    "e_above_hull_vasp",
    "e_above_hull_pbe_rhys_2021-04-27_old_MP_compat_corrections",
]
db_data = list(db.tasks.find(filters, fields))

for dct in db_data:
    if "input" not in dct:
        continue
    dct["input_structure"] = Structure.from_dict(dct.pop("input")["structure"])
    output = dct.pop("output")
    dct[Key.bandgap_pbe] = output[Key.bandgap]
    dct["final_structure"] = Structure.from_dict(output[Key.structure])

df_db = pd.DataFrame(db_data)

df_db = df_db.rename(columns={"formula_pretty": Key.formula})

df_db = df_db.set_index([Key.mat_id, Key.formula], drop=False)

assert not df_db.index.duplicated().any()
df_db = df_db.groupby(level=[0, 1]).last()  # drop duplicate indices
if len(df_db) != len(db_data):
    print(f"Removing duplicates: {len(db_data):,} -> {len(df_db):,}")

assert df_db[Key.mat_id].str.contains("->").all(), (
    "df_db contains relaxed MP/WBM structures, expecting elemental substitution "
    "structures only"
)


# %% setup which alignn model to use and what df column serves as input
alignn_models = {
    Key.bandgap: "jv_mbj_bandgap_alignn",
    "bandgap_vdw": "jv_optb88vdw_bandgap_alignn",
    "e_above_hull": "jv_ehull_alignn",
}
alignn_models = {k: get_figshare_model(v) for k, v in alignn_models.items()}
property_name = "bandgap_vdw"
device = "cpu"


# %% save Alignn predictions in new column named pred_col on df_db
if "jarvis_atoms" not in df_db:
    df_db["jarvis_atoms"] = df_db[Key.structure].map(JarvisAtomsAdaptor().get_atoms)
    df_db[["alignn_atom_graph", "alignn_line_graph"]] = [
        Graph.atom_dgl_multigraph(x, cutoff=8) for x in tqdm(df_db.jarvis_atoms)
    ]
    print(f"Done converting {len(df_db):,} structures to Alignn atom+line graphs")

desc = f"Getting Alignn predictions for: {', '.join(alignn_models.keys())}"
for row in tqdm(df_db.itertuples(), total=len(df_db), desc=desc):
    idx, atom_graph = row.Index, row.alignn_atom_graph
    line_graph = row.alignn_line_graph

    for property_name, model in alignn_models.items():
        pred_col = (
            f"{property_name}_alignn_{'' if 'final' in Key.structure else 'un'}relaxed"
        )
        if pred_col in df_db and not pd.isna(df_db[pred_col][idx]):
            continue

        pred = model([atom_graph.to(device), line_graph.to(device)]).tolist()
        if isinstance(pred, list):
            pred = pred[0]
        df_db.loc[idx, pred_col] = pred


# %%
df_db.reset_index(drop=True).round(4).drop(
    columns=["jarvis_atoms", "alignn_atom_graph", "alignn_line_graph"]
).to_json(
    f"{DATA_DIR}/{today}-alignn-bandgaps-on-elemsub-structures.json.bz2",
    default_handler=lambda x: x.as_dict(),
)
df_db = pd.read_json(
    f"{DATA_DIR}/2022-06-09-alignn-bandgaps-on-elemsub-structures.json.bz2"
)


# %%
title = (
    "Alignn vs Wren hull distances on dielectric elemental substitution structures "
    "with old MP compat corrections"
)
# all columns containing bandgap not ending in '_err'
# y_cols = df_db.filter(regex="bandgap.*(alignn|wren).*(?<!_err)$").columns

y_cols = df_db.filter(regex="e_above_hull_(wren|vasp|alignn).*").columns

target = Key.e_above_hull_pbe
col_labels = {}
for y_col in y_cols:
    xs, ys = df_db[target], df_db[y_col]
    MAE = abs(xs - ys).mean()
    y_col_pretty = y_col.replace("_", " ").title()
    xs, ys = df_db[[target, y_col]].dropna().to_numpy().T
    R2 = r2_score(xs, ys)
    col_labels[y_col] = f"{y_col_pretty} ({len(xs):,})<br>{MAE=:.2f}, {R2=:.2f}"

fig = px.scatter(
    df_db.round(2).rename(columns=col_labels),
    x=target,
    y=list(col_labels.values()),
    hover_data=[Key.mat_id, Key.formula],
    labels={
        Key.e_above_hull_pbe: "PBE hull distance (eV)",
        "value": "ML hull distance (eV)",
        "variable": "",
    },
)
fig.update_traces(visible="legendonly", selector=lambda trace: "Vasp" in trace["name"])

add_identity_line(fig)
fig.layout.title.update(text=title, x=0.5, y=0.95)
fig.layout.margin.update(l=30, r=30, t=30, b=30)
fig.layout.legend.update(bgcolor="rgba(255, 255, 255, 0.4)")
img_path = (f"{PAPER_FIGS}/{today}-e-above-hull-scatter-alignn-vs-wren.png",)
fig.write_image(img_path, scale=2, width=1000, height=500)
fig.show()


# %%
title = "Histogram of ML band gap errors"
for y_col in y_cols:
    df_db[f"{y_col}_err"] = df_db[y_col] - df_db[Key.bandgap_pbe]

fig = px.histogram(
    df_db.round(2),
    x=df_db.filter(regex="bandgap.*_(wren|alignn_unrelaxed)_err").columns,
    labels={"value": "Band gap error (eV)"},
    marginal="rug",
    barmode="group",
    nbins=40,
)

fig.add_vline(0, line=dict(color="black", dash="dot", width=2))

fig.layout.title.update(text=title, x=0.5, y=0.95)
fig.layout.margin.update(l=30, r=30, t=50, b=30)
fig.layout.legend.update(x=1, y=0.5, xanchor="right", font_size=16)

# fig.write_image(f"{PAPER_FIGS}/{today}-bandgap-errors-hist-vs-wren.png", scale=2)
fig.show()
