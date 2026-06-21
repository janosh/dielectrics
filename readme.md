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

## Data Access

All 2.7k DFPT results are published as a release asset and used directly by the analysis code, so no database is required:

[`dielectrics-tasks.json.gz`](https://github.com/janosh/dielectrics/releases/download/v0.1.0/dielectrics-tasks.json.gz)

`df_diel_from_task_coll` downloads the asset on first use, then filters and processes it with pandas. To select all materials with figure of merit $\Phi_\text{M} > 200$ (defined as $\Phi_\text{M} = E_\text{gap} \cdot \epsilon_\text{total}$) and $E_\text{hull-dist} < 0.05\ \text{eV}$:

```py
from dielectrics.db.fetch_data import df_diel_from_task_coll

df = df_diel_from_task_coll({})  # all results, or e.g. {"series": "Wren top 100 FoM"}
close_to_hull_high_fom = df.query("fom_pbe > 200 and e_above_hull_pbe < 0.05")
```

Or load the raw task documents yourself:

```py
import gzip, json, urllib.request

url = "https://github.com/janosh/dielectrics/releases/download/v0.1.0/dielectrics-tasks.json.gz"
urllib.request.urlretrieve(url, "dielectrics-tasks.json.gz")
with gzip.open("dielectrics-tasks.json.gz", mode="rt") as file:
    task_docs = json.load(file)
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
