"""Fix the data type of fields in a across the fireworks, workflows and tasks
collections.
"""

# %%
from collections import defaultdict
from itertools import product

from tqdm import tqdm

from dielectrics.db import db, float_fields, md_field_map


# %% convert all float_fields to type float (sth turns them into strings, need to
# investigate)
for coll, md_key in md_field_map.items():
    paths = [md_key + field for field in float_fields]

    filters = {"$or": [{x: {"$type": "string"}} for x in paths]}
    docs = list(db[coll].find(filters, paths))

    n_changed: dict[str, int] = defaultdict(int)
    for doc in tqdm(docs):
        metadata = doc[md_key.rstrip(".")] if md_key else doc
        try:
            new_vals = {
                md_key + k: round(float(v), 4)
                for k, v in metadata.items()
                if isinstance(v, str)
            }
            result = db[coll].update_one({"_id": doc["_id"]}, {"$set": new_vals})
            for key in new_vals:
                n_changed[key] += 1
        except Exception as err:
            print(f"\n{coll=}\n{doc=}\n{err=}\n")
            break

    print(f"count of fields converted in '{coll}': {dict(n_changed)}")


# %% unset remaining fields that could not be converted due to being empty strings
for idx, (field, (coll, md_key)) in enumerate(
    product(float_fields, md_field_map.items()), 1
):
    print(f"{idx:>3}: {field}")
    field = md_key + field
    data = db[coll].find({field: ""})

    ids = [doc["_id"] for doc in data]

    if len(ids) > 0:
        print(f"unset {len(ids):,} {field=} in {coll=}")

    result = db[coll].update_many(
        {"_id": {"$in": ids}},
        {"$unset": {field: ""}},
    )
    assert len(ids) == result.modified_count
