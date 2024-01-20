# ML-Guided Dielectric Materials Discovery

[![arXiv](https://img.shields.io/badge/arXiv-2401.05848-blue?logo=arxiv&logoColor=white)](https://arxiv.org/abs/2401.05848)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/janosh/dielectrics/main.svg)](https://results.pre-commit.ci/latest/github/janosh/dielectrics/main)
[![Requires Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)](https://python.org/downloads)
![GitHub repo size](https://img.shields.io/github/repo-size/janosh/dielectrics?color=darkblue&label=Repo%20Size&logo=github&logoColor=white)
[![Pareto Plot](https://img.shields.io/badge/Plotly-Pareto%20Front-purple?logo=Plotly&logoColor=white)](https://janosh.github.io/dielectrics)
[![Zenodo](https://img.shields.io/badge/DOI-10.5281/zenodo.10456384-blue?logo=Zenodo&logoColor=white)](https://zenodo.org/records/10456384)

This repo implements a dielectric materials discovery workflow that integrates ML as the first filter in a multi-step funnel.
We use surrogate models for band gaps, dielectric constants, and formation energies.
Instead of exact Cartesian coordinates, we use Wyckoff positions as ML inputs for a coordinate-free, coarse-grained crystal structure representation.
This enables rapid generation, stability prediction and property screening of novel structures through elemental substitutions.
Following DFPT validation of the most promising candidates, the last selection step is an expert committee to incorporate human intuition when weighing the risks, precursor availability and ease of experimental synthesis of high-expected-reward materials.
We validate the workflow by feeding it 135k generated structures as well as Materials Project and WBM materials which are ML-screened down to 2.7k DFPT calculations.
Our deployment culminated in making and characterizing two new metastable materials in the process: CsTaTeO<sub>6</sub> and Bi<sub>2</sub>Zr<sub>2</sub>O<sub>7</sub> which partially and fully satisfy our target metrics, respectively.

## Interactive Pareto Front Plot

The most interesting materials in our dataset are viewable in an interactive Plotly scatter plot at

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

Example Python code using `pymongo` to filter our 2.7k DFPT results for all materials with figure or merit $\Phi_\text{M} > 200$ (defined as $\Phi_\text{M} = E_\text{gap} \cdot \epsilon_\text{total}$) and $E_\text{hull-dist} < 0.05\ \text{eV}$:

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

## How to Cite

```bib
@article{riebesell_pushing_2024,
  title = {Pushing the Pareto Front of Band Gap and Permittivity: ML-guided Search for Dielectric Materials},
  author = {Riebesell, Janosh and Surta, T. Wesley and Goodall, Rhys and Gaultois, Michael and Lee, Alpha A.},
  date = {2024-01-11},
  url = {https://arxiv.org/abs/2401.05848v1},
  urldate = {2024-01-12},
}
```
