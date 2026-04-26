"""Currently we replace all instances of an element when making a swap. The
alternative would be to swap individual Wyckoff positions but this may lead to
higher-order chemical compositions that are more challenging to validate.
"""

import os
import pickle
import urllib.request
from collections.abc import Sequence
from string import digits
from typing import Any

import numpy as np
import pandas as pd
import pymatviz as pmv
from numpy.typing import NDArray
from pymatgen.core import Composition, Structure

from dielectrics import DATA_DIR, Key


ICSD_MATRIX_URL = (
    "https://github.com/janosh/dielectrics/releases/download/v0.1.0/"
    "rhys-icsd-elem-count-matrix.pkl"
)


# atomic numbers of the 88 elements present in materials project (1 - 83 plus 89 - 94)
# look at non-grayed out elements in the periodic table of their search UI
mp_atom_nums = np.array([*range(1, 84), *range(89, 94)])

# MP atomic numbers excluding rare earths (lanthanides + actinides)
mp_atom_nums_wout_rare_earths = np.array([*range(56), *range(72, 83)])


def load_icsd_trans_mat() -> NDArray[np.float32]:
    """Load the ICSD element matrix counting the number of co-occurrences for each pair
    of elements in a crystal structure. Represents data-mined substitution probabilities
    for a given element in a crystal structure.

    Inspired by the modified Pettifor Scale paper.
    https://doi.org/10.1088/1367-2630/18/9/093011

    Returns:
        np.ndarray: ICSD element substitution matrix
    """
    # get icsd count matrices, loads a dict mapping spacegroup numbers to submatrices
    pkl_path = f"{DATA_DIR}/element-substitution/rhys-icsd-elem-count-matrix.pkl"
    if not os.path.isfile(pkl_path):
        os.makedirs(os.path.dirname(pkl_path), exist_ok=True)
        print(f"Downloading ICSD element count matrix to {pkl_path}...")
        urllib.request.urlretrieve(ICSD_MATRIX_URL, pkl_path)  # noqa: S310

    with open(pkl_path, mode="rb") as icsd_data:
        trans_mats = pickle.load(icsd_data)  # noqa: S301

    # combine per-spacegroup transition matrices to get an overall transition matrix
    trans_mat = np.sum([mat for mat in trans_mats.values() if len(mat)], axis=0)

    # subtract 1 due to 0-indexing of arrays
    trans_mat = trans_mat[:, mp_atom_nums - 1]

    # normalize rows (and cols since symmetric) so substitution probabilities sum to 1
    return trans_mat / trans_mat.sum(axis=1, keepdims=1)


remove_digits = str.maketrans("", "", digits)


def aflow_wren_to_comp(aflow_wren_label: str) -> Composition:
    """Generate Pymatgen Composition object from Aflow Wren input string."""
    aflow_str, chem_sys = aflow_wren_label.split(":")
    formula_anonym = aflow_str.split("_")[0]
    elem_list = chem_sys.split("-")
    anonym_letters = list(formula_anonym.translate(remove_digits))
    letter_elem_map = dict(zip(anonym_letters, elem_list, strict=True))
    formula = formula_anonym.translate(str.maketrans(letter_elem_map))
    return Composition(formula)


def replace_similar_elem(
    transition_matrix: NDArray[np.float32],
    atomic_nums: Sequence[int],
    elem_list: Sequence[str],
    rng: np.random.Generator | None = None,
) -> tuple[str, str]:
    """Substitute one in a set of elements based on chemical similarity as determined by
    transition_matrix.

    Args:
        transition_matrix (np.ndarray): Transition probability matrix for elements.
        atomic_nums (list[int]): Admissible integers specifying which atomic numbers to
            consider during substitutions.
        elem_list (list[str]): List of elements to be substituted.
        rng (np.random.Generator | None): Random number generator. If None, creates one
            without a fixed seed.

    Returns:
        tuple[str, str]: Original and new element symbol.
    """
    if rng is None:
        rng = np.random.default_rng()

    orig_elem = rng.choice(elem_list)

    # unlike Rhys' original code, this does not handle isotopes (mostly relevant for
    # Deuterium and Tritium, heavier isotopes are less different) https://git.io/JRUC7
    z_orig = pmv.utils.atomic_numbers[orig_elem]

    while True:
        z_new = rng.choice(atomic_nums, p=transition_matrix[z_orig - 1])

        # avoid swapping an element for itself
        if z_new not in elem_list:
            break

    new_elem = pmv.utils.element_symbols[z_new]

    return orig_elem, new_elem


def replace_elems_in_aflow_wyckoff(
    aflow_wren_label: str, elem_map: dict[str, str]
) -> str:
    """Replace elements in aflow_wren_label according to elem_map.

    Args:
        aflow_wren_label (str): Wren input string encoding Wyckoff positions and
            occupying elements.
        elem_map (dict[str, str]): Map from old to new elements.

    Returns:
        str: Aflow Wyckoff label with substituted elements.
    """
    aflow_str, chem_sys = aflow_wren_label.split(":")
    # update elem_list with elements from elem_map, fallback to original elements
    new_elems = [elem_map.get(elem, elem) for elem in chem_sys.split("-")]
    return f"{aflow_str}:{'-'.join(new_elems)}"


def struct_apply_elem_substitution(
    orig_struct: Structure,
    new_formula: str | Composition,
    *,
    verbose: bool = True,
    strict: bool = True,
) -> Structure | None:
    """Generate a new Pymatgen structure given the original structure and a Pymatgen
    Composition object with one species replaced by another (usually chemically similar)
    element.

    Args:
        orig_struct (Structure): original crystal structure.
        new_formula (str | Composition): Composition string or object
            after elemental substitution by e.g. data-mined ICSD similarity matrix.
        verbose (bool, optional): Whether to print problematic replacements.
            Defaults to True.
        strict (bool, optional): Whether to raise ValueError for invalid replacements.
            Defaults to True.

    Raises:
        ValueError: If strict and the replacement is not balanced or not a single
            element replacement.

    Returns:
        Structure | None: New structure with substituted element, or None if the
            replacement was invalid and strict=False.
    """
    elem_diff = dict(
        Composition(orig_struct.formula, allow_negative=True).reduced_composition
        - Composition(new_formula).reduced_composition
    )

    is_single_replacement = len(elem_diff) == 2
    is_balanced = sum(elem_diff.values()) == 0

    if not is_single_replacement or not is_balanced:
        msg = f"problematic replacement: {elem_diff}"
        if strict:
            raise ValueError(msg)
        if verbose:
            print(msg)
        return None

    # dicts are insertion ordered in py3.6+ so the old element is certain to come first
    old_el, new_el = elem_diff.keys()

    new_struct = orig_struct.copy()
    new_struct.replace_species({old_el: new_el})

    return new_struct


def df_struct_apply_elem_substitution(
    df: pd.DataFrame,
    orig_struct_col: str = "orig_structure",
    new_formula_col: str = str(Key.formula),
    new_struct_col: str = str(Key.structure),
    **kwargs: Any,
) -> pd.DataFrame:
    """Apply struct_apply_elem_substitution to a DataFrame.

    Args:
        df (pd.DataFrame): DataFrame with columns orig_struct_col and new_formula_col.
        orig_struct_col (str, optional): Column name of original Structure objects.
            Defaults to "orig_structure".
        new_formula_col (str, optional): Column name of new Composition objects.
            Defaults to "formula".
        new_struct_col (str, optional): Column name of new Structure objects.
            Defaults to "structure".
        **kwargs: Keyword arguments passed to struct_apply_elem_substitution.

    Returns:
        pd.DataFrame: DataFrame with new_struct_col added.
    """
    df[new_struct_col] = [
        struct_apply_elem_substitution(
            getattr(row, orig_struct_col), getattr(row, new_formula_col), **kwargs
        )
        for row in df.itertuples()
    ]

    if (n_missing_new_struct := sum(df[new_struct_col].isna())) > 0:
        print(
            f"WARNING: {n_missing_new_struct} entries missing elemental "
            "substitution structure."
        )

    return df
