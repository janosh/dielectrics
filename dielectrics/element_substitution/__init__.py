"""Currently we replace all instances of an element when making a swap. The
alternative would be to swap individual Wyckoff positions but this may lead to
higher-order chemical compositions that are more challenging to validate.
"""

import pickle
import random
from collections.abc import Sequence
from string import digits
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from pymatgen.core import Composition, Structure
from pymatviz.utils import atomic_numbers, element_symbols

from dielectrics import DATA_DIR


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
    with open(
        f"{DATA_DIR}/element-substitution/rhys-icsd-elem-count-matrix.pkl", "rb"
    ) as icsd_data:
        trans_mats = pickle.load(icsd_data)  # noqa: S301

    # combine per-spacegroup transition matrices to get an overall transition matrix
    trans_mat = np.sum([mat for mat in trans_mats.values() if len(mat) > 0], axis=0)

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

    trans = str.maketrans(letter_elem_map)

    formula_anonym = formula_anonym.translate(trans)

    return Composition(formula_anonym)


def replace_similar_elem(
    transition_matrix: NDArray[np.float32],
    atomic_nums: Sequence[int],
    elem_list: Sequence[str],
) -> tuple[str, str]:
    """Substitute one in a set of elements based on chemical similarity as determined by
    transition_matrix.

    transition_matrix is a matrix of element substitution probabilities.
    atomic_nums is a list of atomic numbers of the elements to be substituted.

    Args:
        transition_matrix (np.ndarray): Transition probability matrix for elements.
        atomic_nums (list[int]): Admissible integers specifying which atomic numbers to
            consider during substitutions.
        elem_list (list[str]): List of elements to be substituted.

    Returns:
        tuple[str]: New and old element symbol.
    """
    orig_elem = random.choice(elem_list)

    # unlike Rhys' original code, this does not handle isotopes (mostly relevant for
    # Deuterium and Tritium, heavier isotopes are less different) https://git.io/JRUC7
    z_orig = element_symbols[orig_elem]

    while True:
        # Z_orig - 1 for 0-indexing
        z_new = np.random.choice(atomic_nums, p=transition_matrix[z_orig - 1])  # noqa: NPY002

        # avoid swapping an element for itself
        if z_new not in elem_list:
            break

    new_elem = atomic_numbers[z_new]

    return (orig_elem, new_elem)


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

    elem_list = chem_sys.split("-")

    # update elem_list with elements from elem_map, fallback to original elements
    new_elem_list = [elem_map.get(elem, elem) for elem in elem_list]

    return f"{aflow_str}:{'-'.join(new_elem_list)}"


counter = 0


def struct_apply_elem_substitution(
    orig_struct: Structure,
    new_formula: str | Composition,
    verbose: bool = True,
    strict: bool = True,
) -> tuple[Structure, str] | None:
    """Generate a new Pymatgen structure given the original structure and a Pymatgen
    Composition object with one species replaced by another (usually chemically similar)
    element.

    Args:
        orig_struct (Structure): original crystal structure.
        new_formula (str | Composition): Composition string or object
            after elemental substitution by e.g. data-mined ICSD similarity matrix.
        verbose (bool, optional): Whether to print list of orig and replaced elements
            for failure cases. Defaults to False.
        strict (bool, optional): Whether to raise an AssertionError for failure cases.

    Raises:
        ValueError: If strict and the replacement is not balanced or not a single
            element replacement.

    Returns:
        Union[Tuple[Structure, str], None]: Either new structure and performed element
            replacement string or None if failed.
    """
    elem_diff = dict(
        Composition(orig_struct.formula, allow_negative=True).reduced_composition
        - Composition(new_formula).reduced_composition
    )
    global counter  # noqa: PLW0603
    counter += 1

    is_single_replacement = len(elem_diff) == 2
    is_balanced = sum(elem_diff.values()) == 0

    if strict and not is_balanced or not is_single_replacement:
        raise ValueError(
            f"problematic replacement: {elem_diff} for structure {counter}"
        )
    if verbose and not is_balanced or not is_single_replacement:
        print(f"problematic replacement: {elem_diff}")
        return None

    # dicts are insertion ordered in py3.6+ so the old element is certain to come first
    old_el, new_el = elem_diff.keys()

    new_struct = orig_struct.copy()
    new_struct.replace_species({old_el: new_el})

    return new_struct


def df_struct_apply_elem_substitution(
    df: pd.DataFrame,
    orig_struct_col: str = "orig_structure",
    new_formula_col: str = "formula",
    new_struct_col: str = "structure",
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
