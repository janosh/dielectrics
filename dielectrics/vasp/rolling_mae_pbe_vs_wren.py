# %%
import os

import pandas as pd
import plotly.express as px
from pymatviz.io import save_fig

from dielectrics import PAPER_FIGS, Key
from dielectrics.db.fetch_data import df_diel_from_task_coll


__author__ = "Janosh Riebesell"
__date__ = "2023-12-07"

os.makedirs(f"{PAPER_FIGS}/ml/", exist_ok=True)

df_vasp = df_diel_from_task_coll({}, cache=False)
assert len(df_vasp) == 2552, f"Expected 2552 materials, got {len(df_vasp)}"

# filter out rows with diel_elec > 100 since those seem untrustworthy
# in particular wbm-4-26188 with eps_elec = 515 and mp-865145 with eps_elec = 809
# (see table-fom-pbe-gt-350.pdf)
df_vasp = df_vasp.query(f"{Key.diel_elec_pbe} < 100")
assert len(df_vasp) == 2542, f"Expected 2542 materials, got {len(df_vasp)}"


# %% Plot rolling MAE of Wren band gap and dielectric models vs DFT
# swap these to use either Wren or our DFT band gaps as x-axis values
for (x_axis_bandgap, other_bandgap), (x_axis_diel, other_diel) in [
    [
        (Key.bandgap_wren, Key.bandgap_us),
        (Key.diel_total_wren, Key.diel_total_pbe),
    ],
    [
        (Key.bandgap_us, Key.bandgap_wren),
        (Key.diel_total_pbe, Key.diel_total_wren),
    ],
]:
    df_plot = df_vasp.set_index(x_axis_bandgap, drop=False).sort_index()

    # compute MAE and R^2 for dielectric and bandgap line to show in plot annotation
    bandgap_mae = (df_vasp[other_bandgap] - df_vasp[x_axis_bandgap]).abs().mean()
    diel_mae = (df_vasp[Key.diel_total_wren] - df_vasp[Key.diel_total_pbe]).abs().mean()

    window = 300
    # bandgap rolling MAE calculation
    bandgap_rolling_err_col = (
        f"<b>Rolling |E<sub>gap Wren</sub> - E<sub>gap PBE</sub>|</b><br>"
        f"MAE={bandgap_mae:.1f}eV (std={df_vasp[x_axis_bandgap].std():.3})"
    )
    df_plot[bandgap_rolling_err_col] = abs(
        df_plot[x_axis_bandgap] - df_plot[other_bandgap]
    )
    rolling_bandgap_err = (
        df_plot[bandgap_rolling_err_col].dropna().rolling(window=window).mean()
    )

    fig = px.line(
        rolling_bandgap_err,
        color_discrete_sequence=[bandgap_color := "blue"],
        width=500,
        height=300,
    )

    # add rolling MAE of MP band gap w.r.t. our own PBE band gaps into same plot
    # bandgap_mp_err = bandgap_rolling_err.replace("Wren", "MP")
    # df_plot[bandgap_mp_err] = abs(df_plot[bandgap_pbe_col] - df_plot.index)
    # rolling_mp_err = df_plot[bandgap_mp_err].dropna().rolling(window=100).mean()
    # fig.add_scatter(x=rolling_mp_err.index, y=rolling_mp_err, name=bandgap_mp_err)

    diel_rolling_error_col = (
        f"<b>Rolling |ε<sub>total Wren</sub> - ε<sub>total PBE</sub>|</b><br>"
        f"MAE={diel_mae:.1f} (std={df_vasp[Key.diel_total_pbe].std():.3})"
    )

    df_plot = df_plot.set_index(x_axis_diel, drop=False).sort_index()
    df_plot[diel_rolling_error_col] = abs(df_plot[x_axis_diel] - df_plot[other_diel])
    rolling_diel_err = (
        df_plot[diel_rolling_error_col].dropna().rolling(window=window).mean()
    )
    # add rolling MAE of Wren dielectric const into same plot (top x and right y axis)
    fig.add_scatter(
        x=rolling_diel_err.index,
        y=rolling_diel_err,
        name=diel_rolling_error_col,
        yaxis="y2",
        xaxis="x2",
        line=dict(color=(diel_color := "red")),
        marker=dict(symbol="square"),
    )

    x1_title = f"E<sub>gap {'Wren' if 'wren' in x_axis_bandgap else 'PBE'}</sub> (eV)"
    x2_title = f"ε<sub>total {'Wren' if 'wren' in x_axis_diel else 'PBE'}</sub>"
    y1_title = "Rolling E<sub>gap</sub> absolute error (eV)"
    y2_title = "Rolling ε<sub>total</sub> absolute error"

    fig.layout.xaxis = dict(color=bandgap_color, title=x1_title, title_standoff=5)
    fig.layout.yaxis = dict(color=bandgap_color, title=y1_title, title_standoff=5)

    common_kwds = dict(showgrid=False, color=diel_color, title_standoff=5)
    fig.layout.xaxis2 = dict(overlaying="x", side="top", **common_kwds, title=x2_title)
    fig.layout.yaxis2 = dict(
        overlaying="y", side="right", **common_kwds, title=y2_title
    )

    fig.layout.margin = dict(l=20, r=20, t=20, b=20)
    fig.update_traces(marker=dict(size=4), mode="lines+markers")
    if "wren" in x_axis_bandgap:
        fig.update_layout(showlegend=False)
    else:
        fig.layout.legend = dict(x=1, y=0.15, xanchor="right", bgcolor="rgba(0,0,0,0)")

    # set x-min to 0 (can't use None for xmax, has no effect)
    fig.layout.xaxis.update(range=[0, 8.5])
    fig.layout.xaxis2.update(range=[0, 750])

    fig.show()
    assert ("wren" in x_axis_bandgap, "wren" in x_axis_diel) in (
        (True, True),
        (False, False),
    )
    suffix = f"{'wren' if 'wren' in x_axis_bandgap else 'pbe'}-as-x.pdf"
    save_fig(fig, f"{PAPER_FIGS}/ml/rolling-bandgap+diel-error-{suffix}")


# %% plot wren and PBE rolling MAE into same plot
# swap these to use either Wren or our DFT band gaps as x-axis values

for ml_col, pbe_col in [
    # (Keys.diel_total_wren, Keys.diel_total_pbe),
    (Key.bandgap_wren, Key.bandgap_us),
]:
    # compute rolling error as a function of Wren band gap and PBE band gap
    df_ml_idx = (
        df_vasp.dropna(subset=[pbe_col, ml_col])
        .set_index(ml_col, drop=False)
        .sort_index()
    )
    ml_rolling_err = (
        (df_ml_idx[ml_col] - df_ml_idx[pbe_col]).abs().rolling(window=300).mean()
    )
    df_ml_idx["rolling_error"] = ml_rolling_err

    df_dft_idx = df_vasp.set_index(pbe_col, drop=False).sort_index()
    dft_rolling_err = (
        (df_dft_idx[ml_col] - df_dft_idx[pbe_col]).abs().rolling(window=300).mean()
    )
    df_dft_idx["rolling_error"] = dft_rolling_err

    df_plot = pd.DataFrame(
        {
            "Wren": ml_rolling_err,
            "PBE": dft_rolling_err,
        }
    )

    fig = px.line(df_plot, marginal_x="histogram", marginal_y="histogram")
