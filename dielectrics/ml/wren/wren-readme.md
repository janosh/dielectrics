# Wren for Dielectrics Discovery

Total number of trainable parameters: 501,164

## Testing Total vs Electronic + Ionic Dielectric Constant

### Single-task

This command can be used with one of `diel_total`, `diel_ionic` and `diel_elec` as targets.

```sh
python examples/wren.py --train --evaluate --log --data-path datasets/diel/mp-diel-train.json.bz2 --tasks regression --targets diel_total --transfer models/wren-energy-ensemble-from-rhys/checkpoint-r1.pth.tar --robust --model-name wren-diel-test-diel-total --epochs 300
```

```txt
Task: 'diel_total' on Test Set
R2 Score: 0.1656
MAE: 7.0221
RMSE: 27.1014
```

```txt
Task: 'diel_elec' on Test Set
R2 Score: 0.1072
MAE: 1.4837
RMSE: 15.3388
```

```txt
Task: 'diel_ionic' on Test Set
R2 Score: 0.2467
MAE: 5.4612
RMSE: 20.4536
```

Fine-tune for another 300 epochs with lower learning rate (warning: do not use `--resume` flag as that would load the previous learning rate from the optimizer checkpoint and not use the one specified by `--lr/--learning-rate`):

```sh
python examples/wren.py --train --evaluate --log --data-path datasets/diel/mp-diel-train.json.bz2 --tasks regression --targets diel_ionic --robust --fine-tune models/wren-diel-test-diel-ionic/checkpoint-r0.pth.tar --epochs 300 --lr 3e-5 --model-name wren-diel-test-diel-ionic
```

### Multi-task

Training Wren on ionic and electronic contributions to the dielectric constant separately and adding the predictions did a tiny bit better than predicting the total directly. Training two separate models predicting eps_ionic and eps_elec individually did better still though, so we decided (Crystal Meeting 2021-06-11) to use that going forward.

```sh
python examples/wren.py --train --evaluate --log --data-path datasets/diel/mp-diel-train.json.bz2 --tasks regression regression --targets diel_elec diel_ionic --losses L1 L1 --transfer models/wren-energy-ensemble-from-rhys/checkpoint-r1.pth.tar --robust --model-name wren-diel-test-multitask-diel-elec+ionic --epochs 300
```

```txt
diel_elec: Dummy MAE: 5.9664
diel_ionic: Dummy MAE: 13.1950
Validation Baseline - diel_elec: MAE 31.663
Validation Baseline - diel_ionic: MAE 27.229

Task: 'diel_elec' on Test Set
R2 Score: 0.1412
MAE: 1.4737
RMSE: 15.0436

Task: 'diel_ionic' on Test Set
R2 Score: 0.1684
MAE: 5.7283
RMSE: 21.4904
```

## Enrichment Experiment

### Big version taking 100 samples from training set + all stable MP materials

Train without evaluation first to avoid calculating validation set performance on dummy data (all `n = 0`) for large screening set after every epoch:

```sh
python examples/wren.py --train --log --data-path datasets/diel/mp-diel-enrich-big-train.json.bz2 --tasks regression --targets diel_elec --transfer models/wren-energy-ensemble-from-rhys/checkpoint-r1.pth.tar --robust --model-name wren-diel-enrich-expt-big-diel-elec --epochs 300
```

or as a batch job:

```sh
sbatch -J wren-diel-ionic -t 1:0:0 --export CMD='python examples/wren.py --train --log --data-path datasets/diel/mp-diel-enrich-big-train.json.bz2 --tasks regression --targets diel_ionic --transfer models/wren-energy-ensemble-from-rhys/checkpoint-r1.pth.tar --robust --model-name wren-diel-enrich-expt-big-diel-ionic --epochs 300' hpc/gpu_submit
```

To evaluate the model:

```sh
python examples/wren.py --evaluate --data-path datasets/diel/mp-diel-enrich-big-train.json.bz2 --test-path datasets/diel/mp-diel-enrich-big-test.json.bz2 --tasks regression --targets diel_elec --resume --model-name wren-diel-enrich-expt-big-diel-elec --robust
```

```txt
Task: 'diel_total' on Test Set
R2 Score: -0.5921
MAE: 15.1638
RMSE: 27.0262
```

```txt
Task: 'diel_ionic' on Test Set
R2 Score: -0.4578
MAE: 11.0255
RMSE: 22.9379
```

```txt
Task: 'diel_elec' on Test Set
R2 Score: -0.2661
MAE: 4.4996
RMSE: 10.4573
```

## Predict dielectric constant with a checkpointed model

```sh
python examples/wren.py --evaluate --data-path datasets/diel/diffuse-top-1k-wren-diel-mp+wbm.json.bz2 --test-path datasets/diel/diffuse-top-1k-wren-diel-mp+wbm.json.bz2 --tasks regression --targets diel_elec --resume --robust --model-name wren-diel-test-diel-elec
```

```sh
sbatch -J wren-elemsub-bandgap -t 0:30:0 --export CMD='python examples/wren.py --evaluate --data-path datasets/diel/diffuse-top-1k-wren-diel-mp+wbm.json.bz2 --test-path datasets/diel/diffuse-top-1k-wren-diel-mp+wbm.json.bz2 --tasks regression --targets bandgap --resume --robust --model-name wren-bandgap-mp+wbm' hpc/gpu_submit
```

## Bandgap

Unusually, training `--robust` models seems to lead to worse performance on band gap than without. Tested with 1 robust and 2 non-robust models.

Train interactively:

```sh
python examples/wren.py --train --evaluate --log --data-path datasets/bandgap/mp+wbm.json.bz2 --tasks regression --targets bandgap --robust --resume --model-name wren-bandgap-mp+wbm --epochs 300
```

Train with batch job:

```sh
sbatch -J wren-bandgap -t 12:0:0 --export CMD='python examples/wren.py --train --evaluate --log --data-path datasets/bandgap/mp+wbm.json.bz2 --tasks regression --targets bandgap --run-id 3 --model-name wren-bandgap-mp+wbm --epochs 300' hpc/gpu_submit
```

## Formation Energy

Train interactively:

```sh
python examples/wren.py --train --evaluate --log --data-path datasets/bandgap/mp+wbm.json.bz2 --tasks regression --targets bandgap --robust --resume --model-name wren-eform-mp+wbm --epochs 300
```

Evaluate:

```sh
python examples/wren.py --evaluate --data-path datasets/diel/diffuse-top-1k-wren-diel-mp+wbm.json.bz2 --test-path datasets/diel/diffuse-top-1k-wren-diel-mp+wbm.json.bz2 --tasks regression --targets e_form --resume --robust --model-name wren-energy-ensemble-from-rhys
```
