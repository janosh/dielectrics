"""Investigate the input VASP parameters Materials Project used for their dielectric
calcs.
"""

# %%
import pandas as pd
from emmet.core.summary import HasProps
from mp_api.client import MPRester
from pymatgen.core import Composition
from pymatgen.io.vasp import Kpoints
from tqdm import tqdm

from dielectrics import DATA_DIR, PAPER_FIGS, Key
from dielectrics.plots import plt  # side-effect import sets plotly template and plt.rc


# %% fetch the DFPT Dielectric task INCAR/KPOINTS for each material with dielectric data
# (the legacy materials-doc "input" field is gone; VASP inputs now live on task docs)
with MPRester() as mpr:
    diel_docs = mpr.materials.summary.search(
        has_props=[HasProps.dielectric],
        fields=["material_id", "formula_pretty", "task_ids"],
    )

    records = []
    for doc in tqdm(diel_docs, desc="Fetching MP dielectric VASP inputs"):
        tasks = mpr.materials.tasks.search(
            task_ids=doc.task_ids, fields=["task_type", "completed_at", "orig_inputs"]
        )
        diel_task = next(
            (task for task in tasks if task.task_type == "DFPT Dielectric"), None
        )
        if diel_task is None:
            continue
        incar = diel_task.orig_inputs.incar or {}
        date = diel_task.completed_at.date() if diel_task.completed_at else None
        records.append(
            {
                Key.mat_id: str(doc.material_id),
                Key.formula: doc.formula_pretty,
                Key.date: date,
                "kpoints": diel_task.orig_inputs.kpoints,
                **{f"incar.{key}": val for key, val in incar.items()},
            }
        )


# %%
df_input = pd.DataFrame(records).set_index(Key.mat_id)


# %% drop single-value columns
unique_vals_per_col = df_input.select_dtypes(["number"]).nunique()
uniform_cols = unique_vals_per_col[unique_vals_per_col == 1].index

df_input = df_input.drop(columns=uniform_cols)

print(f"removed {len(uniform_cols)} single-value columns: {', '.join(uniform_cols)}")


# %%
nans_per_col = df_input.isna().sum()
nan_cols = nans_per_col[nans_per_col > 0.95 * len(df_input)].index

df_input = df_input.drop(columns=nan_cols)

print(f"removed {len(nan_cols)} mostly NaN columns: {', '.join(nan_cols)}")


# %%
kpoint_cols = ["generation_style", "kpoints"]

df_input[kpoint_cols] = pd.json_normalize(df_input.kpoints.map(lambda x: x.as_dict()))[
    kpoint_cols
].to_numpy()


# %%
# df_input.round(4).to_csv(f"{DATA_DIR}/mp-exploration/mp-diel-vasp-input.csv")

df_input = pd.read_csv(f"{DATA_DIR}/mp-exploration/mp-diel-vasp-input.csv").set_index(
    Key.mat_id
)

df_input[Key.date] = pd.to_datetime(df_input[Key.date])


# %%
df_structs = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-train.json.bz2")

df_input[Key.structure] = df_structs[Key.structure]


# %%
df_input[["incar.EDIFF", "incar.ENCUT"]].value_counts().nlargest(20)


# %%
fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(14, 5))

fig.suptitle(
    "Materials Project EDIFF and ENCUT settings for dielectric calcs over time"
)

df_input.sample(1000).plot.scatter(x=Key.date, y="incar.EDIFF", ax=axs[0])
df_input.sample(1000).plot.scatter(x=Key.date, y="incar.ENCUT", ax=axs[1])


plt.savefig(f"{PAPER_FIGS}/mp-diel-ediff+encut-over-time.pdf")


# %% important to convert to Composition for 'in' check as Osmium would also give true
# for '"O" in string' check
df_input["is_oxide"] = df_input[Key.formula].map(lambda x: "O" in Composition(x))


# %%
fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(14, 5))

fig.suptitle("Sample 1000 EDIFF and ENCUT without oxygen")

df_input[~df_input.is_oxide].sample(1000).plot.scatter(
    x=Key.date, y="incar.EDIFF", ax=axs[0]
)
df_input[~df_input.is_oxide].sample(1000).plot.scatter(
    x=Key.date, y="incar.ENCUT", ax=axs[1]
)


# %%
df_input["auto_kpts"] = df_input[Key.structure].map(
    lambda struct: Kpoints.automatic_density(struct, 3000).kpts
)


# %%
df_input[["auto_kpts", "kpoints"]].head(30)
