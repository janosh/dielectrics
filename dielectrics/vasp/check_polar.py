# %%
from shutil import which

from pymatgen.command_line.chargemol_caller import ChargemolAnalysis

from dielectrics import DATA_DIR


which("Chargemol_09_26_2017_linux_serial")


# %%
vasp_dir = f"{DATA_DIR}/mp-756175-nomad-mylg2h-GT92Yos5RnJW1AQ"
ChargemolAnalysis(path=vasp_dir)
