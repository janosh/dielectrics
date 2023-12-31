from typing import Any

import pandas as pd
from pymatgen.ext.matproj import MPRester

from dielectrics import formula_col, n_sites_col, structure_col


target_properties = [
    "material_id",
    "task_ids",
    "icsd_ids",
    "pretty_formula",
    "formation_energy_per_atom",
    "e_above_hull",
    "band_gap",
    "diel",
    # MAPI docs for spacegroup fields https://git.io/JODU7
    "spacegroup.number",
    "spacegroup.crystal_system",
    "nelements",
    "nsites",
    "final_structure",
]
column_rename_map = {
    "final_structure": structure_col,
    "pretty_formula": formula_col,
    "nsites": n_sites_col,
    "nelements": "n_elements",
    "band_gap": "bandgap_mp",
    "poly_total": "diel_total_mp",
    "poly_electronic": "diel_elec_mp",
    "formation_energy_per_atom": "e_form_mp",
    "e_above_hull": "e_above_hull_mp",
    "e_electronic": "eps_elec_mp",
    "e_total": "eps_total_mp",
    "n": "n_mp",
    "spacegroup.number": "spacegroup_mp",
    "spacegroup.crystal_system": "crystal_system",
}


def fetch_mp_dielectric_structures(query: str | dict[str, Any]) -> pd.DataFrame:
    """Fetch dielectric materials from Materials Project along with some relevant
    properties like band gap, e_form, e_above_hull, icsd_ids, task_ids, etc.

    Args:
        query (str | dict[str, Any]): If string, an MP material Id. Else a dictionary
            of filter criteria.
    """
    mp_diel_train_data = MPRester().query(criteria=query, properties=target_properties)

    df = pd.DataFrame(mp_diel_train_data)

    if "diel" in df:
        df_diel = pd.json_normalize(df.pop("diel"))
        df[list(df_diel)] = df_diel.to_numpy()

    df = df.rename(columns=column_rename_map)

    if "diel_total_mp" in df:
        df["diel_ionic_mp"] = df.diel_total_mp - df.diel_elec_mp
        df["fom_mp"] = df.diel_total_mp * df.bandgap_mp

    return df
