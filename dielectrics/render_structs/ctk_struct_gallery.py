# %%
import crystal_toolkit.components as ctc
import dash
from crystal_toolkit.core.plugin import CrystalToolkitPlugin
from dash import html
from mp_api.client import MPRester
from pymatgen.core import Structure

from dielectrics import Key, SelectionStatus
from dielectrics.db.fetch_data import df_diel_from_task_coll


__author__ = "Janosh Riebesell"
__date__ = "2023-10-22"


# %%
df_all = df_diel_from_task_coll(
    {Key.selection_status: {"$exists": 1}},
    # {"nsites": {"$lt": 5}, "nelements": {"$gt": 2}},
    # crystal system is cubic and less than 5 sites
    # {"spacegroup.number": {"$in": [195, 221, 229, 230, 231]}},
    # {id_col: {"$regex": "^mp-.+->"}, "nsites": {"$lt": 12}},
    fields=["formula", "output.structure", Key.selection_status],
)

df_all[Key.structure] = [
    Structure.from_dict(obj) if isinstance(obj, dict) else obj
    for obj in df_all[Key.structure]
]
for row in df_all.itertuples():
    row.structure.properties["id"] = row.material_id
if Key.selection_status in df_all:
    df_synth = df_all.query(
        f"{Key.selection_status} == '{SelectionStatus.selected_for_synthesis}'"
    )


# %%
struct_comps = []
for struct in df_synth.structure:
    # composition.charge_balanced is experimental, returns None if can't determine
    # charge balance
    assert struct.composition.charge_balanced in (None, True)

    ctk_comp_kwds = dict(
        # show_compass=False,
        show_controls=False,
        unit_cell_choice="primitive",
        # color_scheme="JMOL",
        # bonded_sites_outside_unit_cell=False,
        # draw_image_atoms=False,
        # bonding_strategy="CutOffDictNN",
        scene_settings={
            # "zoomToFit2D": True,
            "defaultZoom": 1.4,
            "enableZoom": True,
            "staticScene": False,
            "secondaryObjectView": False,
            "showAxes": True,
            "drawImageAtoms": False,
        },
        # scene_kwargs={
        #     "customCameraState": {"quaternion": {"x": 45, "y": 0, "z": 0, "w": 0}},
        # },
    )

    struct_comp = ctc.StructureMoleculeComponent(struct_or_mol=struct, **ctk_comp_kwds)
    struct_title_style = {
        "textAlign": "center",
        "fontWeight": "bold",
        "margin": "4em 0 -2em",
    }
    struct_title = html.H3(
        f"{struct.properties['id']} ({struct.formula})", style=struct_title_style
    )
    struct_comps.append(html.Div([struct_title, struct_comp.layout()]))

    mat_id = struct.properties.get("id", "")
    is_elem_sub_struct = "->" in mat_id
    if is_elem_sub_struct and mat_id.startswith("mp-"):
        mp_id = mat_id.split(":")[0]
        mp_struct = MPRester().get_structure_by_material_id(mp_id)
        mp_struct.properties["id"] = f"{mp_id} (parent structure)"

        struct_comp = ctc.StructureMoleculeComponent(
            struct_or_mol=mp_struct, **ctk_comp_kwds
        )
        struct_title = html.H3(mp_struct.properties["id"], style=struct_title_style)
        struct_comps.append(html.Div([struct_title, struct_comp.layout()]))


layout = html.Div(
    struct_comps,
    style={"display": "flex", "flex-wrap": "wrap", "gap": "1rem", "margin": "0.5rem"},
)
app = dash.Dash(plugins=[CrystalToolkitPlugin(layout=layout)])
app.run(debug=True, port=8050)
