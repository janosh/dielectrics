"""Analyze DFPT calcs for dynamic instability based on negative dynamical matrix
eigenvalues corresponding to imaginary phonon modes.
"""

# %%
from collections.abc import Sequence

import numpy as np
import pandas as pd
import plotly.express as px
import pymatviz as pmv
from scipy.constants import milli, tera, value

from dielectrics import PAPER_FIGS, Key
from dielectrics.db.fetch_data import df_diel_from_task_coll


__author__ = "Janosh Riebesell"
__date__ = "2024-04-04"

# following Qu et al. https://www.nature.com/articles/s41597-020-0418-6 allow
# imaginary frequencies up to 1 meV = 0.2417 THz before considering a material unstable
meV_to_THz = value("electron volt-hertz relationship") / tera * milli  # noqa: N816
imaginary_tol = -1 * meV_to_THz


def ph_freqs_from_dyn_mat_evs(dyn_mat_evs: Sequence[float]) -> np.ndarray:
    """Dynamical matrix eigenvalue to phonon frequency conversion.

    Copied from https://github.com/hackingmaterials/amset/blob/92b67a30/amset/tools/phonon_frequency.py#L48
    Thanks to Alex Ganose!
    """
    if dyn_mat_evs:
        phonon_frequencies = -1 * np.sqrt(np.abs(dyn_mat_evs)) * np.sign(dyn_mat_evs)
    else:
        phonon_frequencies = np.array([])
    return phonon_frequencies


# %%
# dyn_mat_keys = ["normalmode_eigenvals", "normalmode_eigenvecs", "force_constants"]
dyn_mat_keys = ["normalmode_eigenvals"]
df_phonon = df_diel_from_task_coll(
    query={},
    fields=[f"calcs_reversed.output.{key}" for key in dyn_mat_keys],
    cache=False,
    drop_dup_ids=True,
)

assert len(df_phonon) == 2532, f"{len(df_phonon)=}"


# %% %
df_tmp = pd.DataFrame(lst[-1]["output"] for lst in df_phonon.calcs_reversed)
df_tmp.index = df_phonon.index
col_map = dict(
    normalmode_eigenvals=Key.dyn_mat_eigen_vals,
    normalmode_eigenvecs=Key.dyn_mat_eigen_vecs,
)
df_tmp = df_tmp.rename(columns=col_map)
df_phonon[list(df_tmp)] = df_tmp

df_phonon[Key.phonon_freqs] = df_phonon[Key.dyn_mat_eigen_vals].map(
    ph_freqs_from_dyn_mat_evs
)

df_phonon.isna().sum()


# %%
# mat_data = dynamical_mats["mp-756175"]
for mat_id in ("mp-756175", "mp-1225854:W->Te"):
    phonon_freqs = df_phonon.loc[mat_id, Key.phonon_freqs]

    fig = px.scatter(
        x=range(len(phonon_freqs)),
        y=phonon_freqs,
        labels={"x": "Eigenvalue Index", "y": "Frequency (THz)"},
    )
    y_min = np.min(phonon_freqs) - 2
    if y_min < imaginary_tol:
        fig.add_hrect(
            y0=imaginary_tol, y1=y_min, line_width=0, fillcolor="red", opacity=0.1
        )
        fig.add_hline(y=imaginary_tol, line_color="red", opacity=0.5)

    n_imag_freqs = np.sum(phonon_freqs < imaginary_tol)
    imag_pct = n_imag_freqs / len(phonon_freqs)
    title = f"{mat_id.replace('->', '→')}"
    fig.layout.title.update(text=title, x=0.5, y=0.98)
    anno_text = f"{n_imag_freqs} imaginary frequencies = {imag_pct:.0%}"
    fig.add_annotation(
        text=anno_text, x=1, y=1, xref="paper", yref="paper", showarrow=False
    )
    fig.layout.margin = dict(l=0, t=30, b=0, r=0)
    fig.show()

    pmv.io.save_fig(
        fig, f"{PAPER_FIGS}/{mat_id}-phonon-freqs.svg", width=300, height=200
    )


# %%
df_phonon[Key.min_ph_freq] = df_phonon[Key.phonon_freqs].map(
    lambda ph_freqs: np.min(ph_freqs) if isinstance(ph_freqs, np.ndarray) else np.nan
)

n_stable = (df_phonon[Key.min_ph_freq] > imaginary_tol).sum()

stable_report = (
    f"{n_stable:,} Stable Materials out of {len(df_phonon):,} = "
    f"{n_stable / len(df_phonon):.1%}"
)
print(stable_report)


# %%
x_min = -10
fig = px.histogram(
    df_phonon.query(f"{x_min} < {Key.min_ph_freq} < {imaginary_tol}")[Key.min_ph_freq],
    nbins=400,
    labels={
        "value": "Minimum Phonon Frequency ω<sub>min</sub> (THz)",
        "count": "Number of Materials",
    },
)
# plot materials with min phonon freq > imaginary_tol as green histogram
fig.add_histogram(
    x=df_phonon.query(f"{Key.min_ph_freq} > {imaginary_tol}")[Key.min_ph_freq],
    marker=dict(color="rgba(10, 200, 120, 0.8)"),
)

anno_text = f"Imaginary Threshold={imaginary_tol:.2f} THz"
anno = dict(
    text=anno_text, x=imaginary_tol, xanchor="right", font=dict(size=14, color="red")
)
fig.add_vline(
    x=imaginary_tol + 0.01,
    line=dict(color="red", width=4, dash="dash"),
    opacity=0.5,
    annotation=anno,
)
# annotate min phonon freqs of synthesized compounds
for mat_id in ("mp-756175", "mp-1225854:W->Te"):
    min_ph_freq = df_phonon.loc[mat_id, Key.min_ph_freq]
    fig.add_annotation(
        x=min_ph_freq,
        y=1,
        text=f"<b>{mat_id.replace('->', '→')}</b><br>{min_ph_freq:.2f} THz",
        showarrow=True,
        arrowhead=1,
        font=dict(size=14),
        # increase the arrow length for one of the annotations
        ay=-70 if mat_id == "mp-756175" else -120,
        ax=-50 if mat_id == "mp-756175" else -90,
    )

fig.layout.xaxis.update(range=(x_min, 0.5))
fig.layout.title.update(text=stable_report, x=0.5, y=0.98)
fig.layout.margin = dict(l=0, t=30, b=0, r=0)
fig.layout.update(showlegend=False)
fig.show()

pmv.io.save_fig(fig, f"{PAPER_FIGS}/min-phonon-freq-hist.svg", width=600, height=400)
