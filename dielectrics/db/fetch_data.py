import gzip
import json
import os
import re
import urllib.request
from collections.abc import Hashable, Sequence
from datetime import UTC, datetime
from typing import Any, Literal, cast

import numpy as np
import pandas as pd
from numpy.linalg import LinAlgError
from numpy.typing import NDArray
from pymatgen.core import Structure

from dielectrics import DATA_DIR, ROOT, Key


# published static-dielectric task documents (GitHub release asset), the data source for
# all analysis. Live MongoDB is no longer required to reproduce results. The asset is a
# trimmed JSON export of the task collection from the v0.1.0 release mongodump.
TASKS_URL = (
    "https://github.com/janosh/dielectrics/releases/download/v0.1.0/"
    "dielectrics-tasks.json.gz"
)


def load_task_docs() -> list[dict[str, Any]]:
    """Load the published static-dielectric task documents, downloading them if absent.

    Returns:
        list[dict[str, Any]]: One trimmed task document per static dielectric calc.
    """
    local_path = f"{DATA_DIR}/dielectrics-tasks.json.gz"
    if not os.path.isfile(local_path):
        os.makedirs(DATA_DIR, exist_ok=True)
        print(f"Downloading task data to {local_path} from {TASKS_URL}")
        urllib.request.urlretrieve(TASKS_URL, local_path)  # noqa: S310
    with gzip.open(local_path, mode="rt", encoding="utf-8") as file:
        return json.load(file)


def doc_matches(doc: dict[str, Any], query: dict[str, Any]) -> bool:
    """Check if a task document satisfies a Mongo-style query (offline equivalent).

    Supports the operators used across the codebase: plain equality plus ``$in``,
    ``$regex`` and ``$exists``.

    Args:
        doc (dict[str, Any]): A task document.
        query (dict[str, Any]): Mongo-style filter.

    Returns:
        bool: True if the document matches all conditions.
    """
    for field, cond in query.items():
        val = doc.get(field)
        if not isinstance(cond, dict):
            if val != cond:
                return False
            continue
        for op, target in cond.items():
            if op == "$in":
                if val not in target:
                    return False
            elif op == "$regex":
                if val is None or not re.search(target, str(val)):
                    return False
            elif op == "$exists":
                if (field in doc) != bool(target):
                    return False
            else:
                raise ValueError(f"unsupported offline query operator {op!r}")
    return True


def diel_tensor_to_const(diel_tensor: NDArray[np.float64]) -> float:
    """Calculates a material's dielectric constant from its dielectric tensor
    same way as Materials Project does it.
    - https://docs.materialsproject.org/methodology/dielectricity#formalism
    - https://git.io/JROQa (DielectricBuilder).

    Tested on 2021-06-02 to give identical results to atomate's DielectricBuilder across
    31 diverse materials.

    Args:
        diel_tensor (array): 2d dielectric tensor. Can be electronic/ionic
            contributions or the combined tensor.

    Returns:
        float: Dielectric constant.
    """
    try:
        # diel_tensor should be symmetric so we use eigvalsh() for speed
        eig_vals = np.linalg.eigvalsh(diel_tensor)
    except LinAlgError:  # diel_tensor likely contains NaNs
        return np.nan

    return eig_vals.mean()  # dielectric const


def get_fitness(diel_total: float, bandgap: float) -> float:
    """Calculates the fitness of a material for electronic applications.

    Args:
        diel_total (float): The material's dielectric constant.
        bandgap (float): The material's bandgap.

    Returns:
        float: Fitness value based on https://doi.org/10.1107/S2053229613027861.
    """
    prefactor = 8.1882  # J/cm^3 from https://arxiv.org/abs/1307.6358
    bandgap_crit = 4  # critical band gap in eV separates semiconductors from insulators
    exp = 1 if bandgap > 4 else 3  # 3 for semiconductors, 1 for insulators
    return prefactor * diel_total * (bandgap / bandgap_crit) ** exp


# required for band gap vs dielectric constant Pareto front plot
REQUIRED_FIELDS = (
    Key.mat_id,
    "formula_pretty",
    "completed_at",
    "output.bandgap",
    "output.epsilon_ionic",
    "output.epsilon_static",
)

DEFAULT_FIELDS = (
    Key.bandgap_pbe,
    Key.bandgap_wren,
    Key.diel_elec_wren,
    Key.diel_ionic_wren,
    Key.diel_total_wren,
    Key.e_above_hull_mp,
    Key.e_above_hull_pbe,
    Key.e_above_hull_wren,
    Key.e_form_wren,
    "elements",
    "fom_wren_rank",
    "fom_wren_std_adj_rank",
    Key.fom_wren_std_adj,
    Key.fom_wren,
    Key.formula,
    "nelements",
    "nsites",
    "orig_formula",
    "series",
    "output.energy_per_atom",
    "output.spacegroup",
    "state",
    Key.selection_status,
    Key.task_id,
    "vbm",
    "which_hull",
    Key.wyckoff,
)


def df_diel_from_task_coll(
    query: dict[str, Any] | Sequence[str],
    *,
    fields: Sequence[Hashable] = DEFAULT_FIELDS,
    col_suffix: str = "_pbe",
    max_diel_total: int = 1000,
    cache: bool = True,
    drop_dup_ids: bool = True,
) -> pd.DataFrame:
    """Fetch dielectric calculation results from the published task dataset (see
    load_task_docs), filtering with a Mongo-style query.

    Args:
        query (dict[str, any]): Mongo-style filter for which task documents to keep.
        fields (list[str], optional): Which document fields to load. Defaults to
            REQUIRED_FIELDS + DEFAULT_FIELDS.
        col_suffix (str, optional): What suffix to append to df column names for
            dielectric constants and figure of merit. Defaults to "_pbe".
        max_diel_total (int): Total dielectric constants above this threshold are
            discarded as unreasonable. Defaults to 1000.
        cache (bool, optional): If True (default), reuse a processed dataframe cached
            under .db_cache/ when present. If False, reprocess from the dataset.
        drop_dup_ids (bool, optional): If True (default), drop duplicate material IDs.

    Raises:
        ValueError: If not all dielectric constants are positive.

    Returns:
        pd.DataFrame: DataFrame with the requested fields plus electronic, ionic and
            total dielectric constants and figure of merit.
    """
    if isinstance(query, list | tuple):  # treat list of strings as material_ids
        query = {str(Key.mat_id): {"$in": query}}
    if not isinstance(query, dict):
        raise TypeError(f"{query=} must be a dict or list of material IDs")

    query_dict = cast("dict[str, Any]", query)
    if "task_label" in query_dict:
        raise ValueError(
            "Don't set task_label in fields, 'static dielectric' is auto-set"
        )
    # only fetch dielectric calcs, ignore relaxations
    query_dict["task_label"] = "static dielectric"
    # material IDs must start with mp-, mvc- or wbm-
    query_dict.setdefault(str(Key.mat_id), {"$regex": "^(mp|mvc|wbm)-"})

    fields = (*fields, *REQUIRED_FIELDS)  # ensure required fields are fetched

    if not (suffix := col_suffix).startswith("_"):
        raise ValueError(f"{col_suffix=} must start with underscore")

    os.makedirs(cache_dir := f"{DATA_DIR}/.db_cache", exist_ok=True)
    hash_val = hash(str(query_dict) + str(sorted(fields)))
    json_path = f"{cache_dir}/{hash_val}.json.gz"

    if cache and os.path.isfile(json_path):
        print(
            f"Using cached data from {json_path}. Pass cache=False to reprocess "
            "from the published dataset."
        )
        df_from_cache = pd.read_json(json_path).set_index(Key.mat_id, drop=False)
        if Key.date in df_from_cache:
            df_from_cache[Key.date] = df_from_cache[Key.date].astype(str)
        if Key.structure in df_from_cache:
            df_from_cache[Key.structure] = df_from_cache[Key.structure].map(
                Structure.from_dict
            )
        return df_from_cache

    data = [doc for doc in load_task_docs() if doc_matches(doc, query_dict)]

    if len(data) == 0:
        raise ValueError(f"{query_dict=} matched 0 published task documents")

    df_diel = pd.DataFrame(data).rename(columns={"formula_pretty": Key.formula})

    output_series = df_diel.pop("output")
    try:
        df_diel[Key.structure] = output_series.map(
            lambda x: Structure.from_dict(x.pop("structure"))
        )
    except KeyError:  # no structure key in output dict
        pass
    df_output = pd.json_normalize(output_series.tolist()).rename(
        columns={Key.bandgap: Key.bandgap_us}
    )
    df_diel[list(df_output)] = df_output

    try:
        df_diel[Key.symmetry] = (
            df_diel["spacegroup.crystal_system"]
            + " | "
            + df_diel["spacegroup.number"].astype(str)
            + " | "
            + df_diel["spacegroup.symbol"].astype(str)
        )
    except KeyError:  # columns are missing
        pass

    df_diel["_id"] = df_diel["_id"].astype(str)

    diel_elec = df_diel[f"diel_elec{suffix}"] = df_diel.epsilon_static.map(
        diel_tensor_to_const
    )

    diel_ionic = df_diel[f"diel_ionic{suffix}"] = df_diel.epsilon_ionic.map(
        diel_tensor_to_const
    )

    # remove rows missing dielectric constants (should be about 20) 2022-08-07
    orig_len = len(df_diel)
    df_diel = df_diel.dropna(subset=[f"diel_elec{suffix}", f"diel_ionic{suffix}"])
    n_dropped = 25
    if len(df_diel) <= orig_len - n_dropped:
        min_size = orig_len - n_dropped
        raise ValueError(
            f"{len(df_diel)=} was expected to be no smaller than {min_size}"
        )

    if n_diel_const_elec_neg := sum(diel_elec < 0):
        raise ValueError(
            "negative electronic dielectric constants shouldn't happen, "
            f"found {n_diel_const_elec_neg:,}"
        )
    if n_diel_const_ionic_neg := sum(diel_ionic < 0):
        raise ValueError(
            "negative ionic dielectric constants shouldn't happen, "
            f"found {n_diel_const_ionic_neg:,}"
        )

    df_diel[f"diel_total{suffix}"] = diel_elec + diel_ionic

    # use database bandgap where available, fall back on our own VASP bandgap else
    bandgaps = (
        df_diel[f"bandgap{suffix}"].fillna(df_diel[Key.bandgap_us])
        if f"bandgap{suffix}" in df_diel
        else df_diel[Key.bandgap_us]
    )
    df_diel[f"bandgap{suffix}_best"] = bandgaps
    if bandgaps.isna().sum() > 0:
        raise ValueError(f"missing {bandgaps.isna().sum()} bandgaps")

    df_diel[f"fom{suffix}"] = df_diel[f"diel_total{suffix}"] * bandgaps

    df_diel[f"fitness{suffix}"] = [
        get_fitness(*tup)
        for tup in zip(df_diel[f"diel_total{suffix}"], bandgaps, strict=True)
    ]

    df_diel = df_diel.query(f"diel_total{suffix} <= {max_diel_total}")

    df_diel = df_diel.round(2)

    df_diel[Key.date] = df_diel.completed_at.str.split(" ").str[0]

    if drop_dup_ids:
        orig_len = len(df_diel)
        df_diel = df_diel.drop_duplicates(subset=Key.mat_id)

        if query_dict == {}:
            n_duplicates_expected = 138
            if len(df_diel) != orig_len - n_duplicates_expected:
                raise ValueError(
                    f"{n_duplicates_expected=}, found {orig_len - len(df_diel)}"
                )

    # convert structures to dict before saving to CSV
    df_diel.to_json(json_path, index=False, default_handler=lambda x: x.as_dict())
    return df_diel.set_index(Key.mat_id, drop=False)


def get_structures_from_task_db(
    material_id: str,
    *,
    save_dir: str = f"{ROOT}/tmp/structs",  # noqa: S108
    fmt: Literal["cif", "poscar", "json"] = "cif",
    verbose: bool = False,
) -> Structure:
    """Fetch a Pymatgen structure by material ID from MongoDB and save it as a CIF file
    for downstream analysis in tools like VESTA.

    Args:
        material_id (str): Material ID.
        save_dir (str, optional): Directory to save CIF file. Defaults to 'tmp/structs'.
        fmt ("cif" | "poscar" | "json", optional): Format to save structure as.
            Defaults to "cif".
        verbose (bool, optional): If True, print warnings about existing CIF files.
            Defaults to False.

    Returns:
        Structure: Fetched Pymatgen structure.
    """
    task_doc = next(
        (doc for doc in load_task_docs() if doc.get(str(Key.mat_id)) == material_id),
        None,
    )
    if task_doc is None:
        raise ValueError(f"{material_id=} not found in published task data")

    struct = Structure.from_dict(task_doc["output"]["structure"])

    # if save_as is extension, generate filename from date + formula + material ID
    if fmt.lower() not in ("cif", "poscar", "json"):
        raise ValueError(f"{fmt=} is not a valid format")

    if save_dir is not None:
        os.makedirs(save_dir, exist_ok=True)

        formula = struct.composition.reduced_formula
        filename = (
            f"{datetime.now(tz=UTC):%Y-%m-%d}-{formula}={material_id.replace(':', '-')}"
        )
        filepath = f"{save_dir}/{filename}.{fmt.lower()}"
        if os.path.isfile(filepath) and verbose:
            print(f"{filepath} already exists, not overwriting")
        else:
            struct.to(filename=filepath)
            if verbose:
                print(f"Saved structure as {filepath}")

    return struct
