# ML-Guided of High-Performance Dielectric Materials

[![Cell Reports Physical Science](https://img.shields.io/badge/Cell%20Reports-Physical%20Science-blue?logo=elsevier&logoColor=white)](https://doi.org/10.1016/j.xcrp.2024.102241)
[![arXiv](https://img.shields.io/badge/arXiv-2401.05848-red?logo=arxiv&logoColor=white)](https://arxiv.org/abs/2401.05848)
[![Zenodo](https://img.shields.io/badge/DOI-10.5281/zenodo.10456384-darkblue?logo=Zenodo&logoColor=white)](https://zenodo.org/records/10456384)
[![Requires Python 3.10+](https://img.shields.io/badge/Python-3.10+-yellow.svg?logo=python&logoColor=white)](https://python.org/downloads)
![GitHub repo size](https://img.shields.io/github/repo-size/janosh/dielectrics?color=darkblue&label=Repo%20Size&logo=github&logoColor=white)
[![Pareto Plot](https://img.shields.io/badge/Plotly-Pareto%20Front-purple?logo=Plotly&logoColor=white)](https://janosh.github.io/dielectrics)

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
  "output.bandgap": { "$gt": 3 },
  "output.epsilon_static.0.0": { "$gt": 10 },
  "output.epsilon_ionic.0.0": { "$gt": 50 },
})
```

## How to Cite

```bib
@article{riebesell_discovery_2024,
  title = {Discovery of high-performance dielectric materials with machine-learning-guided search},
  author = {Riebesell, Janosh and Surta, Todd Wesley and Goodall, Rhys Edward Andrew and Gaultois, Michael William and Lee, Alpha Albert},
  doi = {10.1016/j.xcrp.2024.102241},
  url = {https://cell.com/cell-reports-physical-science/abstract/S2666-3864(24)00546-0},
  journaltitle = {Cell Reports Physical Science},
  issn = {2666-3864},
  volume = {5},
  number = {10},
  date = {2024-10-16},
  note = {Publisher: Elsevier},
}
```
