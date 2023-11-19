# Calculation Series Logs

The following list counts successful dielectric calculations for each series of candidates. It also serves as a log of model types and parameters chosen as well as selection criteria used to generate each list of candidates.

```py
# %% display the number of tasks per 'series' field
pd.DataFrame(
    db.tasks.aggregate([{"$group": {"_id": "$series", "count": {"$sum": 1}}}])
).sort_values("count")
```

1. **MP+WBM top 1k Wren-pred FoM EDIFF:1e-7 ENCUT:700**: **10**
     - small rerun of previous calculations to check if higher convergence criteria lead to meaningfully different results. Performed as a result of unexpectedly large discrepancy between ours and MP's results for the ionic dielectric constant, while the electronic part showed near perfect agreement.
2. **CGCNN top 200 - 100 FoM**: **25**
3. **Wren top 100 FoM**: **73**
4. **CGCNN top 100 FoM**: **80**
5. **Petousis Experimental 2016**: **99**
6. **Petousis Experimental 2017**: **175**
7. **Petousis Experimental 2017 old PBE POTCAR**: **176**
8. **MP+WBM top 1k Wren-pred FoM elemsub**: **227**
9. **MP+WBM top 1k Wren-pred FoM**: **422**
10. **MP+WBM top 1k Wren-diel-ens-pred FoM**: **478**
11. **MP+WBM top 1k FoM std-adjusted by Wren diel ens**: **1115**
    - materials predicted by two non-robust Wren ensembles trained on all (believable, i.e. less (abs(total_diel) < 2000)) MP dielectric calculations
    - `FoM = (diel_total_wren - diel_total_wren_std) * bandgap_pbe` where `bandgap_pbe` is either the materials project or WBM band gap
12. **Top MP FoMs elemsub by Wren diel ens**: **998**
    - The best MP structures according to their product of MP bandgap and MP dielectric constants fed into 1k cycles of elemental substitution, then selecting the best candidates based on 4 Wren ensembles:
      - 10 robust formation energy (combined with PatchedPhaseDiagram to estimate thermodynamic stability)
      - 10 non-robust ionic dielectric
      - 10 non-robust electronic dielectric
      - 10 non-robust bandgap dielectric
