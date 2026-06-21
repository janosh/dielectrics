"""Dataset published in https://www.nature.com/articles/am201557.
Received 'dielectrics.tgz' via email on 2022-03-16 from Changho Hong.

It contains binary and ternary oxides. Each file is named after by the structure's ICSD
collection code and contains information of dielectric properties.
"""

# %%
import tarfile
import warnings
from os.path import basename, isdir, splitext

import numpy as np
import pandas as pd
from mp_api.client import MPRester
from pymatgen.core import Structure
from tqdm import tqdm

from dielectrics import ROOT, Key


# %% Parse data from archive
data = {}
with tarfile.open("dielectrics.tgz") as arxiv:
    for member in arxiv:
        icsd_id = splitext(basename(member.name))[0]

        file = arxiv.extractfile(member)

        if "ICSD" not in member.name or file is None:
            continue

        lines = file.read().decode("utf-8").splitlines()

        diel_total = float(lines[9].split("Averaged static dielectric constant: ")[1])

        eps_elec = np.fromstring("\n".join(lines[1:4]), sep="\t").reshape(-1, 3)
        eps_ionic = np.fromstring("\n".join(lines[5:8]), sep="\t").reshape(-1, 3)

        dct = {
            Key.diel_total_pbe: diel_total,
            "eps_elec": eps_elec,
            "eps_ionic": eps_ionic,
        }
        data[int(icsd_id.replace("ICSD_", ""))] = dct


# %%
df_yim = pd.DataFrame(data).T
df_yim.index.name = Key.icsd_id

df_yim[Key.diel_elec_pbe] = [np.linalg.eigvalsh(x).mean() for x in df_yim.eps_elec]
df_yim[Key.diel_ionic_pbe] = [np.linalg.eigvalsh(x).mean() for x in df_yim.eps_ionic]

assert (
    max(
        df_yim[Key.diel_elec_pbe]
        + df_yim[Key.diel_ionic_pbe]
        - df_yim[Key.diel_total_pbe]
    )
    < 0.002
), "Discrepancy between total diel. constant and sum of electronic and ionic tensors"

assert all(df_yim.isna().sum() == 0)


# %%
# TODO: can these cifs be shared?
cif_dir = f"{ROOT}/../icsd/icsd_cifs"
assert isdir(cif_dir), "Looking for CIFs in the wrong place"

warnings.simplefilter("ignore")
structs = {}

for icsd_id in tqdm(df_yim.index):
    cif_file = f"icsd_{icsd_id:06}.cif"
    try:
        structs[icsd_id] = Structure.from_file(f"{cif_dir}/{cif_file}")
    except (FileNotFoundError, ValueError):
        continue

df_yim[Key.structure] = pd.Series(structs)
df_yim[Key.formula] = [
    struct.formula if struct else None
    for struct in df_yim[Key.structure].fillna(value=False)
]

print(f"{df_yim.isna().sum()=}")


# %% match Yim structures to MP materials by structure (the legacy icsd_ids query field
# is no longer available in the MP API), then attach MP dielectric properties. Scalar
# diel averages are e_total/e_electronic/n (legacy poly_total/poly_electronic)
diel_cols = ["n_mp", Key.diel_elec_mp, Key.diel_total_mp]
fields = ["material_id", "band_gap", "n", "e_electronic", "e_total"]
mp_rows = []
with MPRester() as mpr:
    for icsd_id, struct in tqdm(df_yim[Key.structure].dropna().items()):
        mp_ids = mpr.find_structure(struct, allow_multiple_results=True)
        if not mp_ids:  # empty material_ids would fetch the entire DB
            continue
        mp_rows.extend(
            {
                Key.icsd_id: icsd_id,
                Key.mat_id: str(doc.material_id),
                "band_gap": doc.band_gap,
                "n_mp": doc.n,
                Key.diel_elec_mp: doc.e_electronic,
                Key.diel_total_mp: doc.e_total,
            }
            for doc in mpr.materials.summary.search(material_ids=mp_ids, fields=fields)
        )

# groupby(level=0).first() removes rows with duplicate index (i.e. icsd_id)
df_map = pd.DataFrame(mp_rows).set_index(Key.icsd_id).groupby(level=0).first()
df_yim[Key.bandgap_mp] = df_map.band_gap
df_yim["possible_mp_id"] = df_map[Key.mat_id]
df_yim[diel_cols] = df_map[diel_cols]


# %%
df_yim[[Key.bandgap_pbe, Key.bandgap_hse]] = pd.read_csv("bandgaps.csv").set_index(
    Key.icsd_id
)


# %%
df_yim.to_json("dielectrics.json.bz2", default_handler=lambda x: x.as_dict())


df_yim = pd.read_json("dielectrics.json.bz2")
df_yim.index.name = Key.icsd_id
