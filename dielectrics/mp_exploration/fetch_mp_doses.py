# %%
import pandas as pd
from pymatgen.core import Element
from pymatgen.electronic_structure.plotter import DosPlotter
from pymatgen.ext.matproj import MPRester
from tqdm import tqdm


# %%
rare_earths = [
    str(Element.from_Z(x))
    for x in range(1, 110)
    if Element.from_Z(x).is_rare_earth_metal
]


# %%
mp_data = MPRester().query(
    {
        "nsites": {"$lte": 20},
        "has": {"$all": ["diel", "bandstructure"]},
        "icsd_ids": {"$ne": []},
        "nelements": {"$lte": 5},
        "e_above_hull": {"$lte": 0.1},
        "elements": {"$nin": rare_earths},
    },
    ["material_id"],
)

print(f"materials matching filters: {len(mp_data):,}")


# %%
# df_dos = pd.DataFrame(mp_data).set_index(id_col)

# df_dos.round(4).to_csv("data/mp-doses.csv")

df_dos = pd.read_csv("data/mp-doses.csv").set_index("material_id", drop=False)


# %%
doses = {}

with MPRester() as mpr:
    for mp_id in tqdm(df_dos.index):
        dos = mpr.get_dos_by_material_id(mp_id)
        doses[mp_id] = dos


# %%
dos_plotter = DosPlotter()
plot_label = dos.structure.composition
dos_plotter.add_dos(plot_label, dos)
dos_plotter.get_plot()


# %%
df_dos["dos"] = pd.Series(doses)
df_dos.to_json("mp_doses.json.gz", default_handler=lambda x: x.as_dict())
