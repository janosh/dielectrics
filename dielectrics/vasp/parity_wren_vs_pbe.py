# %%
import os

import matplotlib.pyplot as plt
import pandas as pd
import pymatviz as pmv
import seaborn as sns

from dielectrics import DATA_DIR, PAPER_FIGS, Key
from dielectrics.db.fetch_data import df_diel_from_task_coll


__author__ = "Janosh Riebesell"
__date__ = "2023-12-07"

os.makedirs(f"{PAPER_FIGS}/ml/", exist_ok=True)

bandgap_wren_std_col = "bandgap_wren_std"
diel_elec_wren_std_col = "diel_elec_wren_std"
diel_ionic_wren_std_col = "diel_ionic_wren_std"

df_vasp = df_diel_from_task_coll({}, cache=False)
assert len(df_vasp) == 2552, f"Expected 2552 materials, got {len(df_vasp)}"

# filter out rows with diel_elec > 100 since those seem untrustworthy
# in particular wbm-4-26188 with eps_elec = 515 and mp-865145 with eps_elec = 809
# (see table-fom-pbe-gt-350.pdf)
df_vasp = df_vasp.query(f"{Key.diel_elec_pbe} < 100")
assert len(df_vasp) == 2542, f"Expected 2542 materials, got {len(df_vasp)}"


# %%
bandgap_wren_path = "wren-bandgap-mp+wbm-ensemble"
diel_elec_wren_path = "wren-diel-elec-ens-trained-on-all-mp"
diel_ionic_wren_path = "wren-diel-ionic-ens-trained-on-all-mp"


for wren_csv_path, col, std_col in (
    (diel_elec_wren_path, Key.diel_elec_wren, diel_elec_wren_std_col),
    (diel_ionic_wren_path, Key.diel_ionic_wren, diel_ionic_wren_std_col),
    (bandgap_wren_path, Key.bandgap_wren, bandgap_wren_std_col),
):
    df_wren = pd.read_csv(
        f"{DATA_DIR}/wren/screen/{wren_csv_path}-screen-mp-top1k-fom-elemsub.csv"
    ).set_index(Key.mat_id)
    wren_cols = list(df_wren.filter(regex=rf"{col.replace('_wren', '')}_pred_n\d"))
    assert len(wren_cols) == 10
    df_vasp[col] = df_wren[wren_cols].mean(axis=1)
    df_vasp[std_col] = df_wren[wren_cols].std(axis=1)


# %% dielectric constant parity plot Wren vs PBE
axis_labels = {
    Key.diel_elec_pbe: r"$\epsilon_\text{elec\ PBE}$",
    Key.diel_elec_wren: r"$\epsilon_\text{elec\ Wren}$",
    Key.diel_ionic_pbe: r"$\epsilon_\text{ionic\ PBE}$",
    Key.diel_ionic_wren: r"$\epsilon_\text{ionic\ Wren}$",
    Key.bandgap_us: r"$E_\text{gap\ PBE}$ (eV)",
    Key.bandgap_wren: r"$E_\text{gap\ Wren}$ (eV)",
}


for pbe_col, wren_col, std_col in (
    # (Key.diel_elec_pbe, Key.diel_elec_wren, diel_elec_wren_std_col),
    # (Key.diel_ionic_pbe, Key.diel_ionic_wren, diel_ionic_wren_std_col),
    (Key.bandgap_us, Key.bandgap_wren, bandgap_wren_std_col),
):
    df_plot = df_vasp.sort_values(by=std_col).dropna(subset=[pbe_col, wren_col])
    if pbe_col == Key.diel_elec_pbe:
        df_plot = df_plot.query(f"{wren_col} < 50")
    grid = sns.jointplot(
        x=pbe_col,
        y=wren_col,
        data=df_plot,
        space=0,
        # x=pbe_col, y=wren_col, data=df_plot, space=0, marginal_kws=dict(bins=100)
    )
    ax = grid.ax_joint
    # ax.set_xscale("log")
    # ax.set_yscale("log")
    if pbe_col == Key.diel_elec_pbe:
        ax.set(xlim=(0, 50), ylim=(0, 50))

    scatter = ax.scatter(
        x=pbe_col,
        y=wren_col,
        data=df_plot,
        c=std_col,
        cmap="viridis",
    )

    cbar = plt.colorbar(
        scatter,
        ax=ax,
        label=f"{axis_labels[wren_col]} std",
        shrink=0.6,  # shorten and thin color bar
        orientation="horizontal",
        pad=-0.15,  # move left
        anchor=(0.8, 0.8) if pbe_col == Key.bandgap_us else (0.8, 7.2),
    )
    cbar.ax.xaxis.set_label_position("top")
    pmv.powerups.add_identity_line(ax)

    grid.set_axis_labels(
        axis_labels[pbe_col], axis_labels[wren_col], fontsize=14, labelpad=0
    )

    n_points = len(df_vasp[[pbe_col, wren_col]].dropna())
    # ax.annotate(  # add annotation with number of points
    #     f"n = {n_points:,}", xy=(0.8, 0.4), xycoords="axes fraction", size=11
    # )

    quantity = pbe_col.rsplit("_", 1)[0].replace("_", "-")
    pmv.save_fig(grid.figure, f"{PAPER_FIGS}/ml/parity-wren-vs-pbe-{quantity}.pdf")
