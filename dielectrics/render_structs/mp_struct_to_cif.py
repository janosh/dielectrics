"""This file fetches MP structures with only 1 different element and saves as CIF for
visualization in Vesta to illustrate elemental substitution input-output pairs.

## How to generate images with Vesta?

1. Find MP materials with identical structure and only 1 different atom via Materials
    Explorer <https://materialsproject.org>
2. Download MP structures by ID and export to CIF using code in `fetch_cifs_from_mp.py`.
3. Open CIF in Vesta and adjust angle and remove periodic atoms as desired. Usually a
    slight angle off two crystal axis looks best.
4. Go to File > Export Raster Image, place the file in `/pngs` folder and leave same
    name as CIF file.
5. Set scale=2 and check the transparent background option, then click save.

Cropped PNGs used to be in in an earlier version of discovery-workflow.drawio.
No they're unused.
"""


# %%
import os
import subprocess
from glob import glob
from os.path import basename, isfile

from pymatgen.ext.matproj import MPRester
from tqdm import tqdm


__author__ = "Janosh Riebesell"
__date__ = "2022-05-25"
module_dir = os.path.dirname(__file__)
os.makedirs(f"{module_dir}/mp", exist_ok=True)
os.makedirs(f"{module_dir}/us", exist_ok=True)


# %%
mp_ids = {
    "mp-8023": "AlO",
    "mp-5827": "CaTiO3",
    "mp-557203": "SrZrO3",
    "mp-5229": "SrTiO3",
    "mp-4819": "MgGeO3",
    "mp-4170": "NaTaO3",
    "mp-3834": "BaZrO3",  # originally from Petousis 2017, bandgap_mp=3.4 eV
    "mp-1265": "MgO",
    # "mp-19845": "TiPbO3",
    "mp-1185841": "MgAlO3",
    "mp-1183154": "AlPbO3",
}

with MPRester() as mpr:
    for mp_id, formula in tqdm(mp_ids.items()):
        cif_path = f"{module_dir}/mp/{mp_id}-{formula}.cif"

        if isfile(cif_path):
            continue

        struct = mpr.get_structure_by_material_id(mp_id, conventional_unit_cell=True)
        # safety check to make we have correct formulas
        mp_formula = struct.composition.reduced_formula
        assert formula == mp_formula, f"{formula} != {mp_formula}"

        struct.to(filename=cif_path)


# %% automatically crop PNGs exported from Vesta using ImageMagick
# this is not used anymore, but kept for reference
existing = glob("cropped/*.png")
to_be_cropped = glob("cifs/*.png")

print(f"{len(existing) = }")
print(f"{len(to_be_cropped) = }")
existing = " ".join(existing)

for png in to_be_cropped:
    # make sure no spaces in file names else cmd.split() will fail
    assert " " not in png, f"found space in {png!r}"
    png_base = basename(png)

    if png_base in existing:
        continue

    print(f"Processing {png}")

    # uses ImageMagick's convert CLI
    # cropping to 1200x1200 might works well for cubic Perovskites but might be too
    # small for other crystals. Those need to be handled manually e.g. in Preview.app.
    cmd = (
        f"convert {png} -gravity Center -crop 1200x1200+0+0 +repage cropped/{png_base}"
    )
    subprocess.run(cmd.split())  # noqa: PLW1510, S603
