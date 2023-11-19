# Some Tips and Links for Config/Debugging

## Config Files

Note the `authsource` in [`fireworks-config/db.json`](fireworks-config/db.json) and [`fireworks-config/my_launchpad.yaml`](fireworks-config/my_launchpad.yaml) (plus `ssl: true` in the latter) are missing from the docs but [important for connecting to a MongoDB Atlas database](https://github.com/hackingmaterials/atomate/issues/635).

Another important config file not part of this repo is [`~/.pmgrc.yaml`](https://pymatgen.org/change_log.html?highlight=pmgrc#v4-5-1) with fields like:

```yml
MAPI_DB_VERSION:
  LAST_ACCESSED: "2020_09_08"
  LOG:
    { "2020_09_08": 88, "2021_02_08": 18, "2021_03_22": 61, "2021_05_13": 204 }
PMG_MAPI_KEY: <YOUR_API_KEY>
PMG_DEFAULT_FUNCTIONAL: PBE_54
PMG_VASP_PSP_DIR: /home/jr769/rds/hpc-work/vasp/pseudo-potentials
```

## Debugging/Warnings

### `UnknownPotcarWarning`

[See here](https://workshop.materialsproject.org/lessons/05_automated_dft/Lesson/#vasp-inputs) about

> `pymatgen/io/vasp/inputs.py:1793`: `UnknownPotcarWarning`: POTCAR with symbol Si has metadata that does not match any VASP POTCAR known to pymatgen. The data in this POTCAR is known to match the following functionals: ['Perdew-Zunger81']

### `SSL: CERTIFICATE_VERIFY_FAILED`

When getting errors like

```py
SSL: CERTIFICATE_VERIFY_FAILED unable to get local issuer certificate (_ssl.c:1129)
```

that means Python can't find the SSL CA file provided by `pip install certifi`. Can be fixed by copying the file into the location, the standard lib `ssl` package expects to find it as described [here](https://stackoverflow.com/a/61294657). A [quick and dirty fix](https://stackoverflow.com/a/55517653) is to append `?ssl=true&ssl_cert_reqs=CERT_NONE` to the Mongo host URL.

### `ServerSelectionTimeoutError`

When getting errors like

```py
pymongo.errors.ServerSelectionTimeoutError: localhost:27017: [Errno 111] Connection refused, Timeout: 30s, Topology Description: <TopologyDescription id: 611cd83d34af1028025b7553, topology_type: Single, servers: [<ServerDescription ('localhost', 27017) server_type: Unknown, rtt: None, error=AutoReconnect('localhost:27017: [Errno 111] Connection refused')>]>
```

or

```py
Traceback (most recent call last):
  File "/home/jr769/.venv/py38/bin/qlaunch", line 8, in <module>
    sys.exit(qlaunch())
  File "/home/jr769/.venv/py38/lib/python3.8/site-packages/fireworks/scripts/qlaunch_run.py", line 224, in qlaunch
    do_launch(args)
  File "/home/jr769/.venv/py38/lib/python3.8/site-packages/fireworks/scripts/qlaunch_run.py", line 62, in do_launch
    queueadapter = load_object_from_file(args.queueadapter_file)
  File "/home/jr769/.venv/py38/lib/python3.8/site-packages/fireworks/utilities/fw_serializers.py", line 391, in load_object_from_file
    f_format = filename.split('.')[-1]
AttributeError: 'NoneType' object has no attribute 'split'
```

it means `qlaunch` or `rlaunch` are not accessing their config files correctly. Make sure you pass the `-c` flag the directory that contains _all_ firework config files or specify `-l LAUNCHPAD_FILE`, `-q QUEUEADAPTER_FILE`, `-w FWORKER_FILE` but don't omit some of them.

Alternatively `export CONFIG_FILE_DIR=/home/jr769/rds/hpc-work/dielectrics/fireworks-config` in `~/.bashrc` and use default names for all config files (`my_{fworker,launchpad,qadapter}.yaml`) in that directory.

### `GLIBCXX not found`

Errors like

```sh
lib64/libstdc++.so.6: version GLIBCXX_3.4.21 not found
```

indicate that the necessary partition environment e.g. `module load rhel8/default-icl` for Icelake is not loaded.
