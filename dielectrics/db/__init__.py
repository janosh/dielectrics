import re
from collections.abc import Sequence
from datetime import date
from typing import Any

from bson.json_util import dumps, loads
from pymongo import MongoClient
from pymongo.database import Database
from tqdm import tqdm

from dielectrics import Key


MONGO_SRV = "mongodb+srv://janosh:WVX8HtsAJo@atomate-cluster.q8s9p.mongodb.net/atomate"
db = MongoClient(MONGO_SRV).dielectrics

md_field_map = {"fireworks": "spec.", "workflows": "metadata.", "tasks": ""}

float_fields = [
    "bandgap_mp",
    "bandgap_pbe",
    "bandgap_wren_std",
    "bandgap_wren",
    "diel_elec_wren_std",
    Key.diel_elec_wren,
    "diel_ionic_wren_std",
    "diel_ionic_wren",
    "diel_total_wren_std",
    "diel_total_wren",
    "e_above_hull_wren",
    "e_above_hull_wren_std_adj",
    "e_form_pbe",
    "e_form_wren_std",
    "e_form_wren",
    "e_ref",
    "e_hull",
    "fom_cgcnn",
    "fom_wren_std_adj",
    "fom_wren_std",
    "fom_wren",
    "n_cgcnn",
    "n_wren",
]


def update_str_in_collection(
    db: Database,
    collection_name: str,
    replacements: dict[str, str],
    query: dict[str, Any] = None,
    dry_run: bool = True,
    force_clear: bool = False,
    regex: bool = False,
) -> None:
    """Update the text specified in replacements for the documents in a MongoDB
    collection. This can be used to mass-update an outdated value (e.g., a directory
    or tag) in that collection. The algorithm does a text replacement over the
    *entire* BSON document.

    If dry_run=True, no actual changes are made. When False, the original collection is
    backed up with an extension "{collection name}_xiv_{current date}".

    Adapted from https://git.io/JRdTF.

    Args:
        db (Database): MongoDB Database object
        collection_name (str): name of a MongoDB collection to update
        replacements (dict): e.g. {"old_str1": "new_str1", "scratch/":"project/"}
        query (dict): criteria for query, default None if you want all documents to be
            updated.
        dry_run (bool): if True, only a new collection with new strings is created and
            original "collection" is not replaced
        force_clear (bool): careful! If True, the intermediate collection
            f"{coll_name}_tmp_str_replace" is removed!
        regex (bool): Pass each key-value pair as a regular expression to
            re.sub(key, val, str) instead str.replace(key, val).

    Returns:
        None, but if dry_run==False it replaces the collection with the updated one
    """
    tmp_coll_name = f"{collection_name}_tmp_str_replace"
    tmp_coll = db[tmp_coll_name]
    coll = db[collection_name]

    if force_clear:
        tmp_coll.drop()
    elif tmp_coll.find_one():
        raise AttributeError(
            f"The collection '{tmp_coll_name}' already exists! Use force_clear option "
            "to remove."
        )

    all_docs = list(coll.find(query))

    # all docs that were modified; needed if you set "query" parameter
    modified_docs = []
    occurrences = 0

    for doc in tqdm(all_docs):
        # convert BSON to str, perform replacement, convert back to BSON
        stringified_doc = dumps(doc)

        for old_str, new_str in replacements.items():
            if old_str not in stringified_doc:
                continue
            occurrences += stringified_doc.count(old_str)
            if regex:
                stringified_doc = re.sub(old_str, new_str, stringified_doc)
            else:
                stringified_doc = stringified_doc.replace(old_str, new_str)
        m_bson = loads(stringified_doc)
        modified_docs.append(doc["_id"])

        if not dry_run:
            tmp_coll.insert(m_bson)

    prefix = f"if not for {dry_run=}, would have " if dry_run else ""
    print(f"{prefix}replaced {occurrences:,} occurrences of old with new strings.")

    if not dry_run:
        all_docs = list(coll.find({"_id": {"$nin": modified_docs}}))

        print("Transferring unaffected documents (if any).")
        for old_doc in tqdm(all_docs):
            tmp_coll.insert(old_doc)
            modified_docs.append(doc["_id"])

        print("Confirming that all documents were moved.")
        n_docs = coll.count_documents({"_id": {"$nin": modified_docs}})
        if n_docs != 0:
            raise ValueError(
                "Update aborted! Are you sure new documents are not being inserted "
                "into the collection?"
            )

        # archive the old collection
        coll.rename(f"{coll.name}_xiv_{date.today()}")
        # move temp collection to collection
        tmp_coll.rename(coll.name)


def update_str_in_collections(
    db: Database, coll_names: Sequence[str], replacements: dict[str, str], **kwargs: Any
) -> None:
    """Replace a string in multiple collections of a Mongo database. For example, you
    might want to update a directory name like "/scratch/dir" to "/project/dir". The
    algorithm does a text replacement over the *entire* BSON document.

    If dry_run=True, no actual changes are made. When False, the original collection is
    backed up with an extension "{collection name}_xiv_{current date}".

    Example use:
        db = MongoClient(HOST).dielectrics
        update_str_in_collections(
            db, ["fireworks", "workflows", "tasks"], {"foo": "bar"}, dry_run=True
        )

    Args:
        db (Database): PyMongo Database object.
        coll_names (Sequence[str]): List of collection names to update, e.g.
            ["launches", "fireworks", "workflows", "tasks"]
        replacements (dict[str, str]): e.g. {"old_str1": "new_str1",
            "scratch/": "project/"}
        kwargs: Additional arguments accepted by the update_str_in_collection method
    """
    for idx, coll_name in enumerate(coll_names, 1):
        print(f"{idx}/{len(coll_names)} Updating data in collection: {coll_name}")
        update_str_in_collection(db, coll_name, replacements, **kwargs)
        print()

    print(f"String replacement in collections {coll_names} complete")
