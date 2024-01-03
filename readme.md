# ML-Guided Dielectric Materials Discovery

This repo implements a dielectric materials discovery workflow that integrates ML as the first filter in a multi-step funnel.
We use surrogate models for band gaps, dielectric constants, and formation energies.
Instead of exact Cartesian coordinates, we use Wyckoff positions as ML inputs for a coordinate-free, coarse-grained crystal structure representation.
This enables rapid generation, stability prediction and property screening of novel structures through elemental substitutions.
Following DFPT validation of the most promising candidates, the last selection step is an expert committee to incorporate human intuition when weighing the risks, precursor availability and ease of experimental synthesis of high-expected-reward materials.
We validate the workflow by feeding it 135k generated structures as well as Materials Project and WBM materials which are ML-screened down to 2.7k DFPT calculations.
Our deployment culminated in making and characterizing two new metastable materials in the process: CsTaTeO<sub>6</sub> and Bi<sub>2</sub>Zr<sub>2</sub>O<sub>7</sub> which partially and fully satisfy our target metrics, respectively.

## Interactive Pareto Front Plot

<https://janosh.github.io/dielectrics>

## Database Access

Read-only credentials for MongoDB Atlas M2 instance holding 2.7k DFPT results:

```yml
host: mongodb+srv://atomate-cluster.q8s9p.mongodb.net
port: 27017
database: dielectrics
collection: tasks
readonly_user: readonly
readonly_password: kHsBcWwTb4
```

As an example, Python code using `pymongo` to get all materials with $\fom > 200$ and $E_\text{hull-dist} < \SI{0.05}{eV}$ would be:

```py
from pymongo import MongoClient

cluster = "atomate-cluster.q8s9p.mongodb.net/atomate"
server = f"mongodb+srv://readonly:kHsBcWwTb4@{cluster}"
db = MongoClient(server).dielectrics
close_to_hull_high_fom = db.tasks.find({
  "e_above_hull_pbe": {"$lt": 0.1},
  "fom_pbe": {"$gt": 200},
})
```

The most interesting materials in our dataset are also viewable in the interactive Plotly scatter plot at <https://janosh.github.io/dielectrics>.
