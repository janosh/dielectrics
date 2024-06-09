# %%
from __future__ import annotations

import pandas as pd
from pymatgen.core import Composition
from tqdm import tqdm

from dielectrics import Key
from dielectrics.db import db, md_field_map


# %%
print("Collections")
for coll in db.list_collection_names():
    docs = db[coll].count_documents({})
    print(f"- {coll}: {docs:,} docs")


print("\n--- DB Stats ---")
for key, val in db.command("dbstats").items():
    if isinstance(val, float):
        val = round(val, 2)
    print(f"{key}: {val:{',' if isinstance(val, int | float) else ''}}")


# %% display the number of tasks per 'series' field
pd.DataFrame(
    db.tasks.aggregate([{"$group": {"_id": "$series", "count": {"$sum": 1}}}])
).sort_values("count")


# %%
# the metadata field is named 'spec' for fireworks, 'metadata' for workflows and
# simply top-level ('') for tasks
for coll, md_key in md_field_map.items():
    filters: dict[str, str | dict[str, str | bool]] = {
        f"{md_key}source": {"$exists": True},
        # f"{md_key}series": {"$regex": "elemsub"},
        # f"{md_key}composition": {"$regex": " "},
    }
    n_docs = db[coll].count_documents(filters)

    print(f"\n'{coll}' collection has {n_docs = } matching {filters = }")

    # str replacement to turn H2 C O4 into H2CO4, apply repeatedly since it only
    # replaces first occurrence
    replace_op = {
        "$replaceOne": {"input": "$composition", "find": " ", "replacement": ""}
    }

    update_op: dict[str, str | dict[str, str | bool]] = {
        "$set": {f"{md_key}series": "Top MP FoMs elemsub by Wren diel ens"},
        "$unset": {f"{md_key}source": ""},
        # "$set": {f"{md_key}rank_size": 76506},
        # "$set": {f"{md_key}composition": replace_op},
    }
    result = db[coll].update_many(filters, update_op)
    print(f"{update_op=} modified {result.modified_count:,} docs")
    assert result.modified_count == n_docs, coll


# %%
filters = {"spec.series": "MP+WBM top 1k FoM std-adjusted by Wren diel ens"}
df_fws = pd.DataFrame(db.fireworks.find(filters))

metadata_df = pd.json_normalize(df_fws.pop("spec"))

df_fws[list(metadata_df)] = metadata_df


# %%
df_fws[["state", "nsites"]].hist(by="state", bins=50, figsize=(12, 8))

df_fws.groupby("state").nsites.mean()


# %% count occurrences of each task label in 'tasks' collection
pd.DataFrame(
    db.tasks.aggregate([{"$group": {"_id": "$task_label", "count": {"$sum": 1}}}])
)


# %% count occurrences of each material_id in 'tasks' collection. duplicates expected
# due to different task labels (structure optimization/static dielectric)
# or series (stuff may appear in both Wren selection and Petousis reproduction)
fields = ["$material_id", "$series", "$task_label"]
agg = db.tasks.aggregate([{"$group": {"_id": fields, "count": {"$sum": 1}}}])
id_counts = pd.DataFrame(agg).set_index("_id").sort_values("count")
print(f"{id_counts=}")


# %% delete dup material_ids with same task_label and series
n_del = 0
for row in tqdm(id_counts.query("count > 1").itertuples()):
    material_id, series, task_label = row.Index
    docs = db.tasks.find(
        {Key.mat_id: material_id, "series": series, "task_label": task_label},
        ["_id", Key.task_id],
    )
    df_tasks = pd.DataFrame(docs).set_index("_id")
    # remove the earliest duplicate task, presumably later ones are usually better
    min_task_id = df_tasks.idxmin().to_numpy()[0]
    n_del += 1
    # db.tasks.delete_one({"_id": min_task_id})

print(f"{n_del=}")


# %% display the list of WBM materials for a given 'series' field
pd.DataFrame(
    db.tasks.find({"series": "MP+WBM top 1k Wren-pred FoM elemsub"}, [Key.mat_id])
).set_index(Key.mat_id).filter(like="wbm", axis=0)


# %% fix elemsub material IDs missing element replacement descriptor
elem_diffs = [
    dict(
        Composition(x, allow_negative=True).reduced_composition
        - Composition(y).reduced_composition
    )
    for x, y in zip(df_fws.orig_formula, df_fws[Key.formula], strict=True)
]

assert all(
    len(diff) == 2 and sum(diff.values()) == 0 for diff in elem_diffs
), "there's something wrong about this element replacement"

elem_replacements = ["->".join(str(el) for el in diff) for diff in elem_diffs]

df_fws[Key.mat_id] = [
    mat_id + f":{el_repl}"
    for mat_id, el_repl in zip(df_fws[Key.mat_id], elem_replacements, strict=True)
]

for _id, mat_id in zip(df_fws["_id"], df_fws[Key.mat_id], strict=True):
    print(f"{_id=}, {mat_id=}")
    res = db.tasks.update_one({"_id": _id}, {"$set": {Key.mat_id: mat_id}}).raw_result
    print(f"{res=}")


# %% get a list of all metadata fields in 'fireworks' collection
aggregation = [
    {"$project": {"fields": {"$objectToArray": "$$ROOT.spec"}}},
    {"$unwind": "$fields"},
    {"$group": {"_id": "null", "all_fields": {"$addToSet": "$fields.k"}}},
]
fields_in_tasks_coll = next(db.fireworks.aggregate(aggregation))["all_fields"]
print(f"{fields_in_tasks_coll=}")


# %% change the value of a field inside an array only on those items where it exists
# in this example, change the gzip_output field on RunVaspCustodian _tasks items to True
search = {"spec._tasks": {"$elemMatch": {"_trackers": True}}}
coll = "fireworks"
n_docs = db[coll].count_documents(search)

print(f"\n'{coll}' collection has {n_docs = } matching {search = }")

update_op = {"$set": {"spec._tasks.$.gzip_output": True}}
result = db.fireworks.update_many(search, update_op)

print(f"{update_op=} modified {result.modified_count:,} docs")
assert result.modified_count == n_docs


# %% sync 'additional_fields' of VaspToDb _tasks items with fireworks 'spec' field
# e.g. used after renaming the 'source' field to 'series'
updated_ids = {}

fws = db.fireworks.find(
    {"spec._tasks": {"$elemMatch": {"additional_fields.source": {"$exists": True}}}},
    ["spec._tasks", "spec.series"],
)

fws = list(fws)

for idx, doc in tqdm(enumerate(fws)):
    assert (
        doc["spec"]["_tasks"][-1]["_fw_name"]
        == "{{atomate.vasp.firetasks.parse_outputs.VaspToDb}}"
    )

    doc["spec"]["_tasks"][-1]["additional_fields"]["series"] = doc["spec"]["series"]
    try:
        del doc["spec"]["_tasks"][-1]["additional_fields"]["source"]
    except KeyError:
        pass
    updated_ids[idx] = doc["_id"]
    db.fireworks.update_one(
        {"_id": doc["_id"]}, {"$set": {"spec._tasks": doc["spec"]["_tasks"]}}
    )

assert len(updated_ids) == len(fws)


# %%
db.launches.count_documents(
    {"state": "FIZZLED", "launch_dir_deleted": {"$exists": False}}
)
