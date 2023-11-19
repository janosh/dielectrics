from __future__ import annotations

import gzip
import os
import pickle
import warnings
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from pymatgen.analysis.phase_diagram import PatchedPhaseDiagram


# PatchedPhaseDiagram added in PR https://github.com/materialsproject/pymatgen/pull/2042

warnings.filterwarnings(action="ignore", category=UserWarning, module="pymatgen")
MODULE_DIR = os.path.dirname(__file__)


def load_ppd(path: str) -> PatchedPhaseDiagram:
    """Load PatchedPhaseDiagram from gzipped pickle file.

    To store a PatchedPhaseDiagram for later loading, use:
    ```py
    with gzip.open("path/to/ppd.pkl.gz", "wb") as zip_file:
        pickle.dump(ppd_instance, zip_file)
    ```
    """
    with gzip.open(f"{MODULE_DIR}/{path}", "rb") as file:
        return pickle.load(file)
