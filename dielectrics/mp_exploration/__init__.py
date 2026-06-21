"""Fetch and explore Materials Project dielectric data."""

from collections.abc import Sequence
from typing import Any

import pandas as pd
from emmet.core.summary import HasProps
from mp_api.client import MPRester

from dielectrics import Key


# MP summary fields pulled for every material. Scalar dielectric averages live under
# e_total/e_electronic/n (legacy poly_total/poly_electronic); ICSD ids in database_IDs
summary_fields = [
    "material_id",
    "formula_pretty",
    "band_gap",
    "formation_energy_per_atom",
    "energy_above_hull",
    "nsites",
    "nelements",
    "symmetry",
    "structure",
    "e_total",
    "e_electronic",
    "n",
    "database_IDs",
    "task_ids",
]


def fetch_mp_dielectric_structures(
    material_ids: str | Sequence[str] | None = None,
    *,
    has_dielectric: bool = False,
    **search_kwargs: Any,
) -> pd.DataFrame:
    """Fetch materials from Materials Project with structure and properties relevant to
    dielectric screening (band gap, formation energy, energy above hull, dielectric
    constants, refractive index, ICSD IDs, task IDs, ...).

    Args:
        material_ids (str | Sequence[str] | None): A single MP material ID or a list
            thereof. Defaults to None to query by other filters instead.
        has_dielectric (bool): If True, restrict to materials with computed dielectric
            properties (adds has_props=[HasProps.dielectric]). Defaults to False.
        **search_kwargs (Any): Extra keyword filters forwarded to
            MPRester().materials.summary.search, e.g. band_gap=(0.5, None),
            energy_above_hull=(None, 0.1), num_elements=(5, 10), num_sites=(100, None).

    Returns:
        pd.DataFrame: One row per material with dielectric and stability properties.
    """
    if isinstance(material_ids, str):
        material_ids = [material_ids]
    if has_dielectric:
        search_kwargs["has_props"] = [HasProps.dielectric]

    with MPRester() as mpr:
        docs = mpr.materials.summary.search(
            material_ids=list(material_ids) if material_ids is not None else None,
            fields=summary_fields,
            **search_kwargs,
        )

    df_mp_diel = pd.DataFrame(
        [
            {
                Key.mat_id: str(doc.material_id),
                Key.formula: doc.formula_pretty,
                Key.bandgap_mp: doc.band_gap,
                "e_form_mp": doc.formation_energy_per_atom,
                Key.e_above_hull_mp: doc.energy_above_hull,
                Key.n_sites: doc.nsites,
                "n_elements": doc.nelements,
                "spacegroup_mp": doc.symmetry.number,
                Key.crystal_sys: str(doc.symmetry.crystal_system),
                Key.structure: doc.structure,
                Key.diel_total_mp: doc.e_total,
                Key.diel_elec_mp: doc.e_electronic,
                "n_mp": doc.n,
                "icsd_ids": (doc.database_IDs or {}).get("icsd", []),
                "task_ids": doc.task_ids,
            }
            for doc in docs
        ]
    )

    if Key.diel_total_mp in df_mp_diel:
        df_mp_diel[Key.diel_elec_wren] = (
            df_mp_diel[Key.diel_total_mp] - df_mp_diel[Key.diel_elec_mp]
        )
        df_mp_diel[Key.fom_mp] = (
            df_mp_diel[Key.diel_total_mp] * df_mp_diel[Key.bandgap_mp]
        )

    return df_mp_diel
