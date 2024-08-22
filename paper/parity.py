# %%
import os

import pandas as pd
import pymatviz as pmv

from dielectrics import DATA_DIR, PAPER_FIGS, Key


os.makedirs(f"{PAPER_FIGS}/parity/", exist_ok=True)


# %%
df_bandgap = pd.read_csv(f"{DATA_DIR}/wren/bandgap/wren-bandgap-mp+wbm-ensemble.csv")
df_bandgap = df_bandgap.rename(columns={"bandgap_target": Key.bandgap_pbe})
df_bandgap[Key.bandgap_wren] = df_bandgap.filter(like="pred_n").mean(axis=1)
df_bandgap["bandgap_wren_std"] = df_bandgap.filter(like="pred_n").std(axis=1)

fig = pmv.density_scatter_plotly(
    df_bandgap, x=Key.bandgap_pbe, y=Key.bandgap_wren, best_fit_line=False, n_bins=1000
)
fig.show()
pdf_path = f"{PAPER_FIGS}/parity/parity-wren-bandgap-mp+wbm-ensemble.pdf"
pmv.io.save_fig(fig, pdf_path, width=400, height=300)


# %%
df_bandgap_non_metal = df_bandgap[df_bandgap[Key.bandgap_pbe] > 0.01]
fig = pmv.density_scatter_plotly(
    df_bandgap_non_metal,
    x=Key.bandgap_pbe,
    y=Key.bandgap_wren,
    best_fit_line=False,
    n_bins=1000,
)
fig.show()
pdf_path = f"{PAPER_FIGS}/parity/parity-wren-bandgap-mp+wbm-ensemble_non-metal.pdf"
pmv.io.save_fig(fig, pdf_path, width=400, height=300)


# %%
df_bandgap_metal = df_bandgap[df_bandgap[Key.bandgap_pbe] <= 0.01]
fig = pmv.density_scatter_plotly(
    df_bandgap_metal,
    x=Key.bandgap_pbe,
    y=Key.bandgap_wren,
    best_fit_line=False,
    n_bins=1000,
)

# Check if range is None
if fig.layout.yaxis.range is None:
    # Get the full figure with auto-calculated properties
    full_fig = fig.full_figure_for_development(warn=False)
    y_min, y_max = full_fig.layout.yaxis.range
else:
    y_min, y_max = fig.layout.yaxis.range

# Update both x and y axis ranges to be the same
fig.update_layout(
    xaxis_range=[y_min, y_max],
)

fig.show()
pdf_path = f"{PAPER_FIGS}/parity/parity-wren-bandgap-mp+wbm-ensemble_metal.pdf"
pmv.io.save_fig(fig, pdf_path, width=400, height=300)


# %%
df_elec = pd.read_csv(f"{DATA_DIR}/wren/diel/wren-mp-diel-elec-ensemble-robust.csv")
bad_mpids = df_elec[df_elec["diel_elec_target"] < 0][Key.mat_id]
df_elec = df_elec[~df_elec[Key.mat_id].isin(bad_mpids)]
df_elec = df_elec.rename(columns={"diel_elec_target": Key.diel_elec_pbe})

df_elec[Key.diel_elec_wren] = df_elec.filter(like="pred_n").mean(axis=1)
df_elec["diel_elec_wren_std"] = df_elec.filter(like="pred_n").std(axis=1)
fig = pmv.density_scatter_plotly(
    df_elec,
    x=Key.diel_elec_pbe,
    y=Key.diel_elec_wren,
    best_fit_line=False,
    n_bins=1000,
    hover_data=[Key.formula],
)
fig.show()
pdf_path = f"{PAPER_FIGS}/parity/parity-wren-mp-diel-elec-ensemble-robust.pdf"
pmv.io.save_fig(fig, pdf_path, width=400, height=300)


# %%
df_ionic = pd.read_csv(f"{DATA_DIR}/wren/diel/wren-mp-diel-ionic-ensemble-robust.csv")
df_ionic = df_ionic[~df_ionic[Key.mat_id].isin(bad_mpids)]
df_ionic = df_ionic.rename(columns={"diel_ionic_target": Key.diel_ionic_pbe})
df_ionic[Key.diel_ionic_wren] = df_ionic.filter(like="pred_n").mean(axis=1)
df_ionic["diel_ionic_wren_std"] = df_ionic.filter(like="pred_n").std(axis=1)

fig = pmv.density_scatter_plotly(
    df_ionic,
    x=Key.diel_ionic_pbe,
    y=Key.diel_ionic_wren,
    best_fit_line=False,
    n_bins=1000,
    hover_data=[Key.formula],
)
fig.show()
pdf_path = f"{PAPER_FIGS}/parity/parity-wren-mp-diel-ionic-ensemble-robust.pdf"
pmv.io.save_fig(fig, pdf_path, width=400, height=300)
