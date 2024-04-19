# %%
from glob import glob

import pandas as pd
import yaml
from atomate.common.powerups import add_additional_fields_to_taskdocs, add_metadata
from atomate.vasp.powerups import (
    add_modify_incar,
    add_modify_kpoints,
    add_modify_potcar,
    add_priority,
    add_trackers,
    use_custodian,
)
from atomate.vasp.workflows import wf_dielectric_constant
from fireworks import LaunchPad
from pymatgen.core import Structure
from pymatgen.io.res import AirssProvider
from pymatgen.io.vasp import Kpoints
from pymatviz import ptable_heatmap

from dielectrics import DATA_DIR, ROOT, SCRIPTS_DIR, Key
from dielectrics.db import db
from dielectrics.mp_exploration import fetch_mp_dielectric_structures


with open(f"{ROOT}/fireworks-config/my_launchpad.yaml") as file:
    launchpad = LaunchPad.from_dict(yaml.safe_load(file))


# %% use 'workflows' rather than 'tasks' collection here to include calcs yet to run
existing_material_ids = db.workflows.distinct("metadata.material_id")

print(f"'workflows' collection has {len(existing_material_ids):,} material IDs")


# %% Wren predictions from non-robust ionic and electronic ensembles with std adjusted
# FoM_std_adjusted = (diel_total_ml - diel_total_ml_std) * bandgap_pbe
# df_wren_diel_ens_std_adj = pd.read_json(
#     f"{DATA_DIR}/wren/screen/top-diel-wren-ens-std-adj-for-vasp-val.json.gz",
#     orient="split",
# ).sort_values("fom_wren_std_adj_rank")

df_wren_diel_ens_elemsub = pd.read_json(
    f"{DATA_DIR}/wren/screen/"
    "2022-01-30-wren-ens-screen-mp-top1k-fom-elemsub.json.gz",
    orient="split",
)


# %% visualize workflow (requires graphviz)
# from fireworks.utilities.visualize import wf_to_graph
# wf_to_graph(wf_dielectric_constant(df_wren_diel_ens_elemsub[Key.structure][0]))


# %%
# df = df_wren_diel_ens_elemsub.sort_values(Key.fom_wren_std_adj).round(4)
# df = df.query("n_elems < 4 & ~material_id.isin(@existing_material_ids)")

# fetch single structure and MP properties like bandgap, e_form, e_above_hull, etc.
df_mp = fetch_mp_dielectric_structures("mp-22431")


# %%
res_files = glob(f"{SCRIPTS_DIR}/airss/NaLiTa2O6/good_castep/*.res")

df_airss = pd.DataFrame(
    [AirssProvider.from_file(filepath).as_dict(verbose=False) for filepath in res_files]
).sort_values(by="energy")


df_submit = df_airss.head(3).rename(
    columns={
        "pressure": "airss_pressure",
        "volume": "airss_volume",
        "energy": "airss_energy",
        "uid": "airss_id",
    }
)

df_submit[Key.structure] = df_submit.filepath.map(
    lambda fp: Structure.from_file(fp.replace(".res", ".cif"))
)
df_submit[Key.formula] = df_submit[Key.structure].map(lambda struct: struct.formula)
df_submit[Key.mat_id] = [f"airss-{idx}" for idx in range(1, len(df_submit) + 1)]
df_submit.head()


# %% workflow submission loop, launch jobs with qlaunch rapidfire --nlaunches int
dry_run = False
skipped_ids: list[str] = []
# collect metadata dicts for new workflows to ensure no missing data after a dry run
new_wf_metadata = []

for cnt, (mat_id, row) in enumerate(df_submit.iterrows()):
    if mat_id in existing_material_ids:
        print(f"{cnt}: {mat_id} ({row[Key.formula]}) already in DB, skipping")
        skipped_ids.append(mat_id)
        continue

    wf = wf_dielectric_constant(row.structure)
    # sets IBRION = 8 which we need to get the electronic (static) as well as ionic
    # contribution to the dielectric constant https://vasp.at/wiki/index.php/IBRION
    # also sets ISIF = 2 which calculates forces and stress tensor, treating atom
    # positions as degrees of freedom but keeping cell shape and volume fixed
    # great advice on how to parallelize DFPT calcs in VASP:
    # https://rehnd.github.io/tutorials/vasp/phonons

    # run a coarse initial relaxation with half the k-points followed by a finer one
    # with the full k-point density (likely especially helpful for structures generated
    # by elemental substitutions which are further from equilibrium)
    use_custodian(
        wf,
        custodian_params={
            "job_type": "double_relaxation_run",
            "half_kpts_first_relax": True,
        },
        fw_name_constraint="structure optimization",
    )

    # same INCAR and KPOINT settings for the DFPT calc as in https://rdcu.be/cjP5Z
    # ---
    # consider using KPAR <= 12 for better parallelization as suggested by
    # https://bit.ly/2UA4XG5
    add_modify_incar(
        wf,
        # using setup recommended by VASP for LINUX cluster linked by Infiniband, modern
        # multi-core machines https://vasp.at/wiki/NCORE
        modify_incar_params={"incar_update": {"NCORE": 4}},  # 2 up to # cores per node
    )
    add_modify_incar(
        wf,
        modify_incar_params={"incar_update": {"ENCUT": 700, "EDIFF": 1e-7}},
        fw_name_constraint="static dielectric",
    )
    # TODO: can we turn off spin? MP does so if magmom of all sites is below 0.02
    # (https://git.io/JRBiN) but we don't know that for structures generated via element
    # substitution
    # incar_update["ISPIN"] = 1
    # TODO not interested in local potential, could try setting
    # incar_update["LVHAR"] = ".FALSE."
    # TODO could unset LORBIT = 11, gives unneeded orbital characters in band structure
    # "incar_dictmod": {"LORBIT": {"$unset": ""}},
    # unsure if either affect the dielectric workflow

    # TODO: should we use damped molecular dynamics (IBRION=3) for elemsub structures
    # as recommended when starting from very bad initial guesses? but then how to pick
    # time step and damping factor? https://vasp.at/wiki/index.php/IBRION
    add_modify_incar(
        wf,
        # TODO: figure out how to set ISMEAR = 0 only on first rough relax as suggested
        # by Andrew Rosen
        modify_incar_params={"incar_update": {"ISMEAR": 0}},
        fw_name_constraint="structure optimization",
    )

    add_trackers(wf, ["std_err.txt", "vasp.out", "custodian.json"])

    auto_kpts = Kpoints.automatic_density(row[Key.structure], 3000)
    add_modify_kpoints(
        wf,
        {"kpoints_update": {"kpts": auto_kpts.kpts}},
        fw_name_constraint="static dielectric",
    )

    add_modify_potcar(wf, {"potcar_symbols": {"W": "W_sv"}})
    # W_pv POTCAR available in older releases replaced by W_sv in v5.4
    # https://bit.ly/3z8PETR

    meta_dict = {"series": "airss-from-chris-pickard", Key.mat_id: mat_id}
    for key, val in row.items():
        if val is None:
            continue

        if any(x in key for x in ("_mp", "_wren")) or key == "icsd_ids":
            meta_dict[key] = val
        if "airss" in key:
            meta_dict[key] = val

    if "->" in mat_id:
        assert "elemsub" in meta_dict["series"]
    else:
        assert "elemsub" not in meta_dict["series"]

    # Add metadata dictionary to a workflow and all its Fireworks. meta_dict is merged
    # into WF's "metadata" key and each FWs "spec" key. If FW contains Firetasks ending
    # in "ToDb", e.g. VaspToDb, meta_dict is also merged into "additional_fields" key of
    # these tasks and included in the resulting 'tasks' collection documents.
    add_metadata(wf, meta_dict)
    add_priority(wf, 1)
    # add metadata to DB insertion tasks
    add_additional_fields_to_taskdocs(wf, meta_dict)

    if not dry_run:
        launchpad.add_wf(wf)
    # only add formula at the end for later printing, not needed in launchpad workflow
    meta_dict[Key.formula] = row[Key.formula]
    new_wf_metadata.append(meta_dict)

    print(f"- {mat_id} ({row[Key.formula]})")

print("\n" + "-" * 30)
print(
    f"{'if not for dryrun, would have' if dry_run else ''} added {len(new_wf_metadata)}"
    f" new ones and skipped {len(skipped_ids)} pre-existing workflows"
)

df_new_wfs = pd.DataFrame(new_wf_metadata or [{Key.formula: ""}]).set_index(Key.formula)

nans_per_col = df_new_wfs.isna().sum()
assert not any(
    nans_per_col
), f"some new workflows have missing metadata:\n{nans_per_col}"


# %%
ax = ptable_heatmap(df_new_wfs.index)
ax.set(title="Elemental distribution of new workflows")
