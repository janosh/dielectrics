# %% exploratory data analysis of Yin et al. dielectric materials
from itertools import combinations

import numpy as np
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
from pymatgen.core import Structure
from pymatgen.ext.matproj import MPRester
from pymatviz import annotate_bars, spacegroup_sunburst
from pymatviz.utils import add_identity_line, crystal_sys_from_spg_num
from tqdm import tqdm

from dielectrics import DATA_DIR, Key
from dielectrics.plots import plt


# %%
df_yim = pd.read_json(f"{DATA_DIR}/others/yim/dielectrics.json.bz2")
df_yim.index.name = Key.icsd_id

df_yim[Key.structure] = [
    Structure.from_str(x, fmt="json") if x else None for x in df_yim.structure
]


for row in tqdm(df_yim.itertuples(), total=len(df_yim)):
    try:
        cols = ["spg_symbol", Key.spg]
        if struct := row.structure:
            df_yim.loc[row.Index, cols] = _, spg_num = struct.get_space_group_info()
            df_yim.loc[row.Index, Key.crystal_sys] = crystal_sys_from_spg_num(spg_num)
    except TypeError:  # 'NoneType' object is not subscriptable
        continue

df_yim = df_yim.dropna(subset=Key.crystal_sys)


# %%
fig = px.scatter(
    df_yim.reset_index(),
    x=Key.diel_total_pbe,
    y=Key.diel_total_mp,
    color=Key.crystal_sys,
    hover_data=[Key.icsd_id, Key.spg],
    hover_name=Key.formula,
)

xy_range = [0.2, 3]
fig.layout.xaxis.update(range=xy_range, type="log")
fig.layout.yaxis.update(range=xy_range, type="log")
fig.layout.margin = dict(t=10, b=10, l=10, r=10)
fig.layout.legend.update(x=1, y=0, xanchor="right", yanchor="bottom")
add_identity_line(fig)


# %%
labels = {"bandgap_hse": "HSE", "bandgap_gga": "GGA", "bandgap_mp": "MP"}

corr_mat = df_yim[list(labels)].corr() ** 2
keep = np.triu(np.ones(corr_mat.shape, dtype=bool), 1).reshape(corr_mat.size)
titles = [f"{R2=:.2f}" for R2 in corr_mat.melt()[keep].value]

fig = make_subplots(
    rows=1, cols=3, shared_xaxes=True, shared_yaxes=True, subplot_titles=titles
)
xy_max = 9
for idx, (xcol, ycol) in enumerate(combinations(labels, 2), 1):
    sub_fig = px.scatter(
        df_yim.reset_index(),
        x=xcol,
        y=ycol,
        hover_data=[Key.icsd_id, Key.spg],
        hover_name=Key.formula,
        color=Key.crystal_sys,
    )
    # don't show repeated legend labels, only show those of first subplot
    sub_fig.update_traces(showlegend=idx == 1)

    fig.layout[f"xaxis{idx}"].title = xcol
    fig.layout[f"yaxis{idx}"].title = ycol

    for trace in sub_fig.data:
        fig.add_trace(trace, row=1, col=idx)
    fig = add_identity_line(fig, row=1, col=idx)

fig.layout.margin = dict(t=40, b=10, l=10, r=10)
# fig.layout.width = 1500
fig.show()


# %%
fig = spacegroup_sunburst(df_yim[Key.spg], show_counts="percent")
title = "Space distribution of Yin et al. dielectric materials"
fig.layout.title.update(text=title, x=0.5, font=dict(color="lightgray"))
fig.show()


# %%
df_no_nan = df_yim.dropna(subset=[Key.diel_total_pbe, Key.crystal_sys])
fig = px.strip(
    df_no_nan.reset_index(),
    color=Key.crystal_sys,
    x=Key.crystal_sys,
    y=Key.diel_total_pbe,
    hover_data=[Key.icsd_id, Key.spg],
    hover_name=Key.formula,
    labels=labels,
    log_y=True,
    title="Dielectric constant by crystal system",
)

fig.update_layout(showlegend=False)

x_ticks = [
    f"{key}<br>points: {val:,} ({val / len(df_no_nan):.0%})"
    for key, val in df_yim[Key.crystal_sys].value_counts().items()
]
fig.layout.xaxis.update(tickvals=list(range(7)), ticktext=x_ticks)
fig.show()


# %%
mp_ids = {}
mpr = MPRester()
for row in tqdm(df_yim.itertuples()):
    mp_ids[row.Index] = mpr.find_structure(row.structure)

df_yim[mp_ids_col := "likely_mp_ids"] = pd.Series(mp_ids)


# %%
df_yim[mp_ids_col].map(len).value_counts().plot(kind="bar", log=True)
annotate_bars()
plt.savefig(f"{mp_ids_col}_lens.pdf")


# %% where there are several mp_ids, pick the one with lowest energy above convex hull
# since these are ICSD structures and lowest lying polymorph is the one most likely to
# be stable
df_yim[Key.e_above_hull_mp] = df_yim[mp_ids_col].map(
    lambda ids: [mpr.query(mp_id, ["e_above_hull"])["e_above_hull"] for mp_id in ids]
)

df_yim["likely_mp_id"] = df_yim.map(
    lambda row: row[mp_ids_col][np.argmin(row.e_above_hull)], axis=1
)
