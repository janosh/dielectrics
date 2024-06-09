"""This module provides functions for cleaning Fireworks launch directories. They should
be run on the same HPC filesystem where the fireworks ran.
"""

import os
import subprocess
import time
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from glob import glob
from os.path import isfile
from shutil import rmtree
from typing import Any

import pandas as pd
import yaml
from pymongo import MongoClient
from tqdm import tqdm

from dielectrics.db import MONGO_SRV


def round_floats_in_csvs(glob_pat: str = "**/*.csv") -> dict[str, Exception]:
    """Decrease floating point precision in CSV files matching provided glob pattern.

    Args:
        glob_pat (str, optional): Defaults to "**/*.csv".

    Returns:
        dict[str, Exception]: CSV paths that couldn't be handled mapped to errors.
    """
    csvs = glob(glob_pat, recursive=True)
    errors = {}

    for csv in tqdm(csvs):
        try:
            df_csv = pd.read_csv(csv)
            id_cols = df_csv.filter(like="id").columns
            if len(id_cols) > 0:
                df_csv = df_csv.set_index(id_cols[0])
            df_csv.round(4).to_csv(csv)
        except (ValueError, KeyError, Exception) as err:
            errors[csv] = err

    return errors


def _validate_sub_launchdir(ldir: str) -> None:
    *_, parent_ldir, child_ldir = ldir.split("/")
    for folder in (parent_ldir, child_ldir):
        assert folder.startswith("launcher_")
        assert "@" in folder, f"got invalid {folder=}"


def _validate_launchdir(ldir: str) -> None:
    _, dirname, _ = ldir.split("/")
    assert dirname.startswith("launcher_")
    assert "@" in dirname, f"got invalid {dirname=}"


def du(paths: list[str]) -> str:
    """Disk usage in human readable format (e.g. '2,1GB')."""
    if not paths:
        return ""
    return subprocess.check_output(["du", "-sh", *paths]).split()[0].decode("utf-8")  # noqa: S603


def ldir_is_recent(ldir: str, n_days: int) -> bool:
    """Check whether the date in a launch directories name is less than (True) or more
    than (False) n_days in the past.
    """
    date_str = ldir[: ldir.rindex("-")].replace("launcher_", "")

    ldir_date = datetime.strptime(date_str, r"%Y-%m-%d-%H-%M-%S").replace(
        tzinfo=timezone.utc
    )
    # return True if the date is less than n_days in the past
    return datetime.now(tz=timezone.utc) - timedelta(days=n_days) > ldir_date


def rm_never_started_launch_dirs(block_dir: str) -> None:
    """Delete launch directories that contain only a slurm submission script
    (FW_submit.script) and  possibly log (FW_job-49907998.out) and error
    (FW_job-49907998.error) files but no actual output files.
    """
    for ldir in glob(f"{block_dir}/*/"):
        _validate_launchdir(ldir)
        files = sorted(os.listdir(ldir))

        if files == ["FW_submit.script"]:
            os.remove(f"{ldir}/FW_submit.script")
            os.rmdir(ldir)
            print(f"deleted {ldir}")
        elif (
            len(files) == 3
            and files[0].startswith("FW_job-")
            and files[1].startswith("FW_job-")
            and files[2] == "FW_submit.script"
        ):
            print(f"deleted {ldir}")
            for file in files:
                os.remove(f"{ldir}/{file}")
            os.rmdir(ldir)


def rm_launch_dirs_missing_stderr(block_dir: str) -> None:
    """Delete launch directories that contain no std_err.txt or std_err.txt.gz file."""
    # trailing slash ensures we only glob directories
    for ldir in glob(f"{block_dir}/*/*/"):
        _validate_sub_launchdir(ldir)
        if len(os.listdir(ldir)) == 0:
            # if the directory is empty, delete and move on
            os.rmdir(ldir)
            continue

        has_stderr = isfile(f"{ldir}/std_err.txt") or isfile(f"{ldir}/std_err.txt.gz")

        if not has_stderr:
            print(f"would have deleted '{ldir}'")
            # rmtree(f"{full_path}")
            # with open(f"{ldir}FW.yaml") as file:
            #     for line in file.readlines():
            #         if line.startswith("fw_id: "):
            #             print(line)


TOP_LEVEL_CALC_DIR = "dfpt-calcs/"


def rm_launchdirs(
    launch_dirs: Sequence[str], *, write_log: bool = True, dry_run: bool = True
) -> None:
    """Delete launch directories and optionally write a log file with the deleted
    directories.

    Args:
        launch_dirs (Sequence[str]): List of launch directories to delete.
        write_log (bool, optional): Whether to write a log file. Defaults to True.
        dry_run (bool, optional): Whether to actually delete the directories or
            just check that they exist. Defaults to True.
    """
    n_dirs = len(launch_dirs)
    dirs_removed, dirs_not_found = [], []
    for ldir in tqdm(launch_dirs):
        # prevent deleting anything not inside the directory holding all calculations
        # (assuming its name is unique)
        assert TOP_LEVEL_CALC_DIR in ldir, f"'{TOP_LEVEL_CALC_DIR}' not in path {ldir=}"
        _validate_sub_launchdir(ldir)
        try:
            if not dry_run:
                rmtree(ldir)
            else:
                assert os.path.isdir(ldir)
            dirs_removed.append(ldir)
        except (FileNotFoundError, AssertionError):
            dirs_not_found.append(ldir)

    n_removed, n_not_found = len(dirs_removed), len(dirs_not_found)

    space_gained = du(dirs_removed)

    msg = f"Deleted {n_removed} of {n_dirs} dirs ({n_removed / n_dirs:.1%})."
    if space_gained:
        msg += f" {space_gained=}."
    if n_removed < n_dirs:
        msg += f" {n_not_found} could not be deleted due to FileNotFoundError"

    print(msg)
    dic = {"msg": msg, "dirs_removed": dirs_removed, "dirs_not_found": dirs_not_found}

    if write_log:
        utc_time = datetime.now(tz=timezone.utc)
        with open(f"deleted_dirs_{utc_time:%Y-%m-%d@%H:%M}.yaml", "w") as file:
            file.write(yaml.dump(dic, sort_keys=False))


def rm_launchdirs_by_fw_query(
    query: dict[str, Any], *, archived_only: bool = True, sleep: int = 2
) -> None:
    """Delete a set of launch dirs in which fireworks matching the provided query were
    run.

    Args:
        query (dict[str, Any]): Pymongo search criteria.
        archived_only (bool, optional): Only consider archived launches.
            Defaults to True.
        sleep (int, optional): Number of seconds to sleep before deleting.
            Defaults to 2.
    """
    db = MongoClient(MONGO_SRV).dielectrics

    n_matches = db.fireworks.count_documents(query)
    print(f"{n_matches} fireworks matching {query=}", flush=True)
    if sleep > 0:
        print(f"Sleeping {sleep} sec to abort if this seems off", flush=True)
        time.sleep(sleep)

    fws = db.fireworks.find(query, ["launches", "archived_launches", "fw_id"])
    potential_launch_ids = []
    launch_ids = []
    fw_ids = []
    for fw in fws:
        if archived_only:
            potential_launch_ids += fw["archived_launches"]
        else:
            potential_launch_ids += fw["launches"] + fw["archived_launches"]
        fw_ids.append(fw["fw_id"])

    print(f"Number of matching launches: {len(potential_launch_ids)}")

    # only remove launches if no other FWs refer to them
    for launch_id in potential_launch_ids:
        filters = {
            "$or": [{"launches": launch_id}, {"archived_launches": launch_id}],
            "fw_id": {"$nin": fw_ids},
        }
        if not db.fireworks.find_one(filters):
            launch_ids.append(launch_id)

    launch_dirs = []
    for launch_id in launch_ids:
        ldir = db.launches.find_one({"launch_id": launch_id}, ["launch_dir"])[
            "launch_dir"
        ]
        launch_dirs.append(ldir)

    rm_launchdirs(launch_dirs)


def rm_launchdirs_by_launches_query(
    query: dict[str, Any],
    *,
    delete_launches_in_db: bool = False,
    sleep: int = 2,
    dry_run: bool = True,
) -> None:
    """Delete launch directories by Mongo query on the HPC to save storage.

    Args:
        query (dict[str, Any]): Pymongo search criteria.
        delete_launches_in_db (bool): If True all the launch directories associated with
            the firework will be deleted as well, if possible.
        sleep (int): Number of seconds to wait before deleting. This is to give the
            user a chance to abort if the query seems off. Defaults to 2.
        dry_run (bool): If True, don't actually delete anything. Defaults to True.
    """
    db = MongoClient(MONGO_SRV).dielectrics

    n_matches = db.launches.count_documents(query)
    print(f"{n_matches} launches matching {query=}", flush=True)
    if sleep > 0:
        print(f"Sleeping {sleep} sec to abort if this seems off", flush=True)
        time.sleep(sleep)

    launches = db.launches.find(query, ["launch_dir"])

    rm_launchdirs([launch["launch_dir"] for launch in launches], dry_run=dry_run)

    if dry_run:  # don't modify DB on a dry run
        return

    if delete_launches_in_db:
        print(f"Now deleting {n_matches} items in 'launches' collection")
        result = db.launches.delete_many(query).raw_result
        print(f"Successfully deleted {result['nModified']} items")
    else:
        result = db.launches.update_many(
            query, {"$set": {"launchdir_deleted": True}}
        ).raw_result
        print(f"Set 'launchdir_deleted': True on {result['nModified']} items")


"""
Dec 1, 2021: Deleting 505 fizzled launch directories with
rm_launchdirs_by_launches_query(
    {"state": "FIZZLED", "launchdir_deleted": {"$exists": False}},
)
freed up 10.7 GB of CSD3 RDS storage, i.e. 21.2 MB per fizzled launch directory.
"""

if __name__ == "__main__":
    rm_launchdirs_by_launches_query(
        # {"state": "FIZZLED", "launchdir_deleted": {"$exists": False}},
        {"launch_dir": {"$regex": "dfpt-calcs"}, "state": "FIZZLED"},
        delete_launches_in_db=False,
        dry_run=True,
    )
