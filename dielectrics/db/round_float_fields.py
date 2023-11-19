"""Round a list of float fields to given number of decimal places across the fireworks,
workflows and tasks collections.
"""


# %%
from itertools import product

from tqdm import tqdm

from dielectrics.db import db, float_fields, md_field_map


# %%
n_decimals = 4

for idx, (field, (coll, md_key)) in enumerate(
    product(float_fields, md_field_map.items()), 1
):
    path = md_key + field

    cursor = db[coll].aggregate(
        [{"$match": {path: {"$exists": True}}}, {"$project": {path: 1}}]
    )

    n_changed = 0
    for doc in tqdm(list(cursor)):
        old_val = doc[md_key.rstrip(".")][field] if md_key else doc[field]
        try:
            new_val = round(old_val, n_decimals)
            if new_val != old_val:
                result = db[coll].update_one(
                    {"_id": doc["_id"]}, {"$set": {path: new_val}}
                )
                assert result.modified_count == 1
                n_changed += 1
        except Exception as err:
            print(f"\n{field=}\n{coll=}\n{doc=}\n{err=}\n")
            break

    indent = "\t\t" if n_changed == 0 else ""
    print(f"{indent}#{idx}: rounding '{path}' in '{coll}': {n_changed:,} docs updated")
