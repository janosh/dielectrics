# %%
from atomate.vasp.builders.dielectric import DielectricBuilder
from atomate.vasp.builders.tasks_materials import TasksMaterialsBuilder

from dielectrics.db import db as db_rw


# %% Adapted from https://matsci.org/t/extract-dielectric-tensor-from-local-db/3563/2
# set up builders
# (only materials + counter need to be read+write, tasks can be read-only for safety)
task_builder = TasksMaterialsBuilder(db_rw.materials, db_rw.counter, db_rw.tasks)
dielectric_builder = DielectricBuilder(db_rw.materials)

# Doesn't work for bringing the material ID along into the materials collection
# default: ['bandgap', 'energy_per_atom']
# tasks.properties_root = ["bandgap", "energy_per_atom", "material_id"]


# %%
task_builder.reset()
task_builder.run()
dielectric_builder.run()
