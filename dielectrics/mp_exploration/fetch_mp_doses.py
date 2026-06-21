# %%
import pandas as pd
from emmet.core.summary import HasProps
from mp_api.client import MPRester
from pymatgen.core import Element
from pymatgen.electronic_structure.plotter import DosPlotter
from tqdm import tqdm

from dielectrics import DATA_DIR, Key


# %%
rare_earths = [
    str(Element.from_Z(x))
    for x in range(1, 110)
    if Element.from_Z(x).is_rare_earth_metal
]


# %%
with MPRester() as mpr:
    docs = mpr.materials.summary.search(
        num_sites=(None, 20),
        num_elements=(None, 5),
        energy_above_hull=(None, 0.1),
        has_props=[HasProps.dielectric, HasProps.bandstructure],
        theoretical=False,  # has an ICSD entry (experimentally observed)
        exclude_elements=rare_earths,
        fields=["material_id"],
    )
mp_data = [str(doc.material_id) for doc in docs]

print(f"materials matching filters: {len(mp_data):,}")


# %%
# df_dos = pd.DataFrame(mp_data).set_index(Keys.mat_id)

# df_dos.round(4).to_csv(f"{DATA_DIR}/mp-exploration/mp-doses.csv")

df_dos = pd.read_csv(f"{DATA_DIR}/mp-exploration/mp-doses.csv").set_index(
    Key.mat_id, drop=False
)


# %%
doses = {}

with MPRester() as mpr:
    for mp_id in tqdm(df_dos.index):
        dos = mpr.get_dos_by_material_id(mp_id)
        doses[mp_id] = dos


# %% plot one example DOS (get_dos_by_material_id now returns a bare Dos without an
# attached structure, so label the plot with the material ID instead of its composition)
example_id = df_dos.index[0]
dos_plotter = DosPlotter()
dos_plotter.add_dos(example_id, doses[example_id])
dos_plotter.get_plot()


# %%
df_dos["dos"] = pd.Series(doses)
df_dos.to_json(
    f"{DATA_DIR}/mp-exploration/mp_doses.json.gz", default_handler=lambda x: x.as_dict()
)
