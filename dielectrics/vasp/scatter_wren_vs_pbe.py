# %%
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pymatviz.io import save_fig
from pymatviz.utils import add_identity_line

from dielectrics import (
    DATA_DIR,
    PAPER_FIGS,
    bandgap_us_col,
    bandgap_wren_col,
    diel_elec_pbe_col,
    diel_ionic_pbe_col,
    id_col,
)
from dielectrics.db.fetch_data import df_diel_from_task_coll


__author__ = "Janosh Riebesell"
__date__ = "2023-12-07"

bandgap_wren_std_col = "bandgap_wren_std"
diel_elec_wren_std_col = "diel_elec_wren_std"
diel_ionic_wren_std_col = "diel_ionic_wren_std"
diel_elec_wren_col = "diel_elec_wren"
diel_ionic_wren_col = "diel_ionic_wren"

df_vasp = df_diel_from_task_coll({})


# %%
bandgap_wren_path = "wren-bandgap-mp+wbm-ensemble"
diel_elec_wren_path = "wren-diel-elec-ens-trained-on-all-mp"
diel_ionic_wren_path = "wren-diel-ionic-ens-trained-on-all-mp"


for wren_csv_path, col, std_col in (
    (diel_elec_wren_path, diel_elec_wren_col, diel_elec_wren_std_col),
    (diel_ionic_wren_path, diel_ionic_wren_col, diel_ionic_wren_std_col),
    (bandgap_wren_path, bandgap_wren_col, bandgap_wren_std_col),
):
    df_wren = pd.read_csv(
        f"{DATA_DIR}/wren/screen/{wren_csv_path}-screen-mp-top1k-fom-elemsub.csv"
    ).set_index(id_col)
    wren_cols = list(df_wren.filter(regex=rf"{col.replace('_wren', '')}_pred_n\d"))
    assert len(wren_cols) == 10
    df_vasp[col] = df_wren[wren_cols].mean(axis=1)
    df_vasp[std_col] = df_wren[wren_cols].std(axis=1)


# %% dielectric constant parity plot Wren vs PBE
axis_labels = {
    diel_elec_pbe_col: r"$\epsilon_\text{electronic,PBE}$",
    diel_elec_wren_col: r"$\epsilon_\text{electronic,Wren}$",
    diel_ionic_pbe_col: r"$\epsilon_\text{ionic,PBE}$",
    diel_ionic_wren_col: r"$\epsilon_\text{ionic,Wren}$",
    bandgap_us_col: r"$E_\text{gap,PBE}$ (eV)",
    bandgap_wren_col: r"$E_\text{gap,Wren}$ (eV)",
}

for pbe_col, wren_col, std_col in (
    (diel_elec_pbe_col, diel_elec_wren_col, diel_elec_wren_std_col),
    (diel_ionic_pbe_col, diel_ionic_wren_col, diel_ionic_wren_std_col),
    (bandgap_us_col, bandgap_wren_col, bandgap_wren_std_col),
):
    grid = sns.jointplot(
        x=pbe_col, y=wren_col, data=df_vasp, space=0, marginal_kws=dict(bins=60)
    )
    ax = grid.ax_joint
    # ax.set_xscale("log")
    # ax.set_yscale("log")
    if pbe_col == diel_elec_pbe_col:
        ax.set(xlim=(0, 50), ylim=(0, 50))
    scatter = ax.scatter(
        x=pbe_col,
        y=wren_col,
        data=df_vasp.sort_values(by=std_col),
        c=std_col,
        cmap="viridis",
    )

    cbar = plt.colorbar(
        scatter,
        ax=ax,
        label=f"std. dev. of {axis_labels[wren_col]}",
        shrink=0.6,  # shorten and thin color bar
        orientation="horizontal",
        pad=-0.15,  # move left
        anchor=(0.8, 0.8) if pbe_col == bandgap_us_col else (0.8, 7.2),
    )
    cbar.ax.xaxis.set_label_position("top")
    add_identity_line(ax)
    grid.set_axis_labels(
        axis_labels[pbe_col], axis_labels[wren_col], fontsize=14, labelpad=0
    )

    n_points = len(df_vasp[[pbe_col, wren_col]].dropna())
    ax.annotate(  # add annotation with number of points
        f"n = {n_points:,}", xy=(0.8, 0.4), xycoords="axes fraction", size=11
    )

    quantity = pbe_col.rsplit("_", 1)[0].replace("_", "-")
    save_fig(grid.fig, f"{PAPER_FIGS}/wren-vs-pbe-{quantity}-scatter.pdf")
