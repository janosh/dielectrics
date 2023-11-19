# ML-Guided Dielectric Materials Discovery

Developing novel materials with high dielectric constant and low current leakage is required for further miniaturization and optimization of modern electronics. Previous searches for high-$\kappa$ dielectrics tended to be limited to known materials. We chart an extensive search for new dielectrics across unknown material space by combining coarse-grained symmetry features of crystal structures with message-passing neural networks to predict stability as well as material properties. We ran over 2,000 DFPT calculations to verify our model predictions from which we selected xxx candidates for synthesis. xxx were selected for experimental synthesis and xxx confirmed as high-$\kappa$ dielectrics amenable to electronics applications. We believe our approach is transferable to other material properties and brings us a step closer to rational design of functional materials by combining machine learning, ab-initio simulation and experimental synthesis.

## Interactive Pareto Front Plot

<https://janosh.github.io/dielectrics>

## Database Access

The read-only credentials for our MongoDB Atlas M2 instance are:

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

## Born Charges

Good explanation of Born effective charges from [VASP docs](https://vasp.at/wiki/index.php/Dielectric_properties_of_SiC).

> Roughly speaking, the Born effective tensors provide a measure of how much charge effectively moves with an atom when you displace it.

It applies to insulators where the Born Charge of an atom describes the electrical polarization induced by the displacement of this individual atom.
