# CGCNN for Dielectrics Discovery

## Enrichment Experiment

Using CGCNN pretrained by Rhys as energy model on MP seems to pay off. Training MAE on refractive index starts off much lower than dummy:

```txt
Use material_nn from 'models/cgcnn-energy-ensemble-from-rhys/checkpoint-r0.pth.tar' as a starting point and train the output_nn from scratch
Total Number of Trainable Parameters: 505473
Dummy MAE: 0.6672
Epoch: [1/200]
Train           : n - Loss 0.271        MAE 0.369       RMSE 0.965
Epoch: [2/200]
Train           : n - Loss 0.175        MAE 0.238       RMSE 0.823
Epoch: [3/200]
Train           : n - Loss 0.165        MAE 0.224       RMSE 0.779
```

### Small version taking 1000 samples from training set

Given a screening set of 100 top n materials + 900 random examples from the remaining ~7000 samples from the training set, can CGCNN identify a sufficiently high number of the top 100 candidates to be a viable model for finding new hihg refractive index materials.

CGCNN command used to run enrichment experiment:

```sh
python examples/cgcnn.py --train --evaluate --data-path datasets/diel/mp-diel-enrich-small-train.json.bz2 --test-path datasets/diel/mp-diel-enrich-small-test.json.bz2 --tasks regression --targets diel_total --transfer models/cgcnn-energy-ensemble-from-rhys/checkpoint-r0.pth.tar --radius 5.5 --n-graph 6 --elem-fea-len 128 --model-name diel-enrich-expt-small
```

Logs

```txt
Epoch: [100/100]
Train           : n - Loss 0.068        MAE 0.067       RMSE 0.190
Validation      : n - Loss 0.428        MAE 0.425       RMSE 2.421
Evaluating Model
Task: 'n' on Test Set
R2 Score: 0.2236
MAE: 0.4247
RMSE: 2.4215
```

Result for top 100 by refractive index (n): CGCNN top 100 predictions contained 61 of the top 100 materials from the screening set of 1000 candidates.

### Big version taking 100 samples from training set + all stable MP materials

Train without evaluation first to avoid calculating validation set performance on dummy data (all `n = 0`) for large screening set after every epoch:

```sh
python examples/cgcnn.py --train --log --data-path datasets/diel/mp-diel-enrich-big-train.json.bz2 --tasks regression --targets diel_total --transfer models/cgcnn-energy-ensemble-from-rhys/checkpoint-r0.pth.tar --model-name diel-enrich-expt-big --radius 5.5 --n-graph 6 --elem-fea-len 128 --epochs 200
```

```sh
python examples/cgcnn.py --evaluate --data-path datasets/diel/mp-diel-enrich-big-train.json.bz2 --test-path datasets/diel/mp-diel-enrich-big-test.json.bz2 --tasks regression --targets diel_total --resume --radius 5.5 --n-graph 6 --elem-fea-len 128 --model-name diel-enrich-expt-big
```

Result for top 100 by refractive index (n): CGCNN top 100 predictions contained 4 of the top 100 materials from the screening set of 1000 candidates.

## Screening Experiment

No test or validation set. We validate CGCNN predictions with VASP calculations.

Train command

```sh
python examples/cgcnn.py --train --log --data-path datasets/diel/mp-diel-train.json.bz2 --val-size 0.05 --tasks regression --targets diel_total --transfer models/cgcnn-energy-ensemble-from-rhys/checkpoint-r0.pth.tar --radius 5.5 --n-graph 6 --elem-fea-len 128 --model-name diel-screen-bg-0.5 --epochs 200
```

Screen command

```sh
python examples/cgcnn.py --evaluate --data-path datasets/diel/mp-diel-train.json.bz2 --test-path datasets/diel/mp-diel-screen.csv.bz2 --tasks regression --targets diel_total --resume --model-name diel-screen-bg-0.5 --radius 5.5 --n-graph 6 --elem-fea-len 128
```
