"""Investigate the input VASP parameters Materials Project used for their dielectric
calcs.
"""

# %%
import pandas as pd
from pymatgen.core import Composition
from pymatgen.ext.matproj import MPRester
from pymatgen.io.vasp import Kpoints

from dielectrics import Key
from dielectrics.plots import plt


# %%
mp_diel_inputs = MPRester().query(
    criteria={"has": "diel"},
    properties=["material_id", "input", "created_at", "pretty_formula"],
)


# %%
df_input = pd.json_normalize(mp_diel_inputs).set_index(Key.mat_id)

df_input["date"] = pd.to_datetime(df_input.pop("created_at")).dt.date

df_input.columns = df_input.columns.str.replace("input.", "")


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
# df_input.round(4).to_csv("data/mp-diel-vasp-input.csv")

df_input = pd.read_csv("data/mp-diel-vasp-input.csv").set_index(Key.mat_id)

df_input["date"] = pd.to_datetime(df_input.date)


# %%
df_structs = pd.read_json("data/mp-diel-train.json.bz2")

df_input["structure"] = df_structs.structure


# %%
df_input[["incar.EDIFF", "incar.ENCUT"]].value_counts().nlargest(20)


# %%
fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(14, 5))

fig.suptitle(
    "Materials Project EDIFF and ENCUT settings for dielectric calcs over time"
)

df_input.sample(1000).plot.scatter(x="date", y="incar.EDIFF", ax=axs[0])
df_input.sample(1000).plot.scatter(x="date", y="incar.ENCUT", ax=axs[1])


plt.savefig("plots/mp-diel-ediff+encut-over-time.pdf")


# %% important to convert to Composition for 'in' check as Osmium would also give true
# for '"O" in string' check
df_input["is_oxide"] = df_input.formula.map(lambda x: "O" in Composition(x))


# %%
fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(14, 5))

fig.suptitle("Sample 1000 EDIFF and ENCUT without oxygen")

df_input[~df_input.is_oxide].sample(1000).plot.scatter(
    x="date", y="incar.EDIFF", ax=axs[0]
)
df_input[~df_input.is_oxide].sample(1000).plot.scatter(
    x="date", y="incar.ENCUT", ax=axs[1]
)


# %%
df_input["auto_kpts"] = df_input.structure.map(
    lambda struct: Kpoints.automatic_density(struct, 3000).kpts
)


# %%
df_input[["auto_kpts", "kpoints"]].head(30)
