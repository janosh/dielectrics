# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns
from matplotlib.patches import Patch
from pymatviz.io import save_fig

from dielectrics import (
    DATA_DIR,
    PAPER_FIGS,
    bandgap_mp_col,
    bandgap_us_col,
    diel_total_mp_col,
    diel_total_pbe_col,
    fom_pbe_col,
    id_col,
    today,
)
from dielectrics.db.fetch_data import df_diel_from_task_coll


__author__ = "Janosh Riebesell"
__date__ = "2022-03-02"


# %%
df_mp = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-train.json.bz2")

# discard negative and unrealistically large dielectric constants
df_mp = df_mp.query(f"0 < {diel_total_mp_col} < 2000")


# %% qz3 for author last name initials (https://rdcu.be/cCMga)
# unprocessed JSON from https://doi.org/10.6084/m9.figshare.10482707.v2
df_qz3 = pd.read_csv(f"{DATA_DIR}/others/qz3/qz3-diel.csv.bz2")

# Petousis 2017: https://nature.com/articles/sdata2016134
df_petousis = pd.read_csv(f"{DATA_DIR}/others/petousis/exp-petousis.csv").set_index(
    id_col, drop=False
)

df_petousis[fom_pbe_col] = (
    df_petousis[bandgap_mp_col] * df_petousis["diel_total_petousis"]
)
df_qz3[fom_pbe_col] = df_qz3["bandgap_pbe"] * df_qz3[diel_total_pbe_col]


# %%
df_us = df_diel_from_task_coll({})
df_us = df_us.rename(columns={"fom_pbe": fom_pbe_col})
assert all(df_us[diel_total_pbe_col] > 0), "negative dielectric, this shouldn't happen"


# %%
# plt.figure(figsize=(8, 5))
mp_kde = False  # whether to plot a kernel density of MP dielectric training data
names: list[str] = []
if mp_kde:
    ax = sns.kdeplot(
        x=df_mp[diel_total_mp_col],
        y=df_mp[bandgap_mp_col],
        # cut=0,  # how far evaluation grid extends, 0 truncates at data limits
        fill=True,
        cmap="Blues",
        zorder=0,
        label=f"KDE of {len(df_mp):,} MP DFPT calcs",
    )
else:
    ax = plt.gca()


# other cmap choices: tab20, tab20b, tab20c, Set1, Set2, Set3
color_iter = iter(sns.color_palette("tab10"))
markers = iter(["o", "D", "s", "x", "P"])  # circle, diamond, square, cross, plus

for df, (name, label) in (
    (  # for main text
        df_us[[diel_total_pbe_col, bandgap_us_col]],
        ("us", f"{len(df_us):,} this work"),
    ),
    (  # for SI
        df_qz3[[diel_total_pbe_col, "bandgap_pbe"]],
        ("qu", f"{len(df_qz3):,} Qu et al. 2020"),
    ),
    (
        df_petousis[["diel_total_petousis", bandgap_mp_col]],
        ("petousis", f"{len(df_petousis):,} Petousis et al. 2017"),
    ),
    # (  # splitting by substitution and MP/WBM structures, not used in paper
    #     df_us.query(f"~{id_col}.str.contains('->')")[
    #         [diel_total_pbe_col, bandgap_us_col]
    #     ],
    #     f"{sum(~df_us.index.str.contains('->')):,} MP/WBM structures",
    # ),
    # (
    #     df_us.query(f"{id_col}.str.contains('->')")[
    #         [diel_total_pbe_col, bandgap_us_col]
    #     ],
    #     f"{sum(df_us.index.str.contains('->')):,} substitution structures",
    # ),
):
    color, marker = next(color_iter), next(markers)
    x_col, y_col = list(df)
    ax = df.plot.scatter(
        x=x_col, y=y_col, ax=ax, label=label, color=color, marker=marker, alpha=0.7
    )
    names.append(name)

handles = ax.legend().legend_handles
for handle in handles:
    handle.set_sizes([50])
if mp_kde:
    kde_label = f"KDE of {len(df_mp):,} MP DFPT calcs"
    kde_handle = Patch(label=kde_label, facecolor="deepskyblue")
    handles = (*handles, kde_handle)
ax.add_artist(ax.legend(handles=handles, loc="upper right", frameon=False))

ax.set_xlabel(r"$\epsilon_\text{total}$")
ax.set_ylabel(r"$E_\text{gap,PBE}$ (eV)")

# ax.set(xlim=[0, xmax := 400], ylim=[0, ymax := 8])
ax.set(xscale="log", yscale="log", xlim=(1, xmax := 1800), ylim=(0.3, ymax := 15))

isoline_label_kwds = dict(inline_spacing=3, fontsize=10, inline=True)

fom_vals = np.outer(np.arange(ymax + 1), np.arange(xmax + 1))
fom_levels = (30, 60, 120, 240)
fom_isolines = ax.contour(
    fom_vals, levels=fom_levels, linestyles="--", colors=["darkblue"], zorder=0
)
fom_manual_locations = [(x / (ymax - 4), ymax - 4) for x in fom_levels]
ax.clabel(fom_isolines, manual=fom_manual_locations, **isoline_label_kwds)

show_fitness_isolines = False
if show_fitness_isolines:
    fitness_vals = np.outer(np.arange(ymax + 1), np.sqrt(np.arange(xmax + 1)))
    fitness_levels = [15, 30, 60]
    fitness_isolines = ax.contour(
        fitness_vals,
        levels=fitness_levels,
        linestyles="--",
        colors=["green"],
        zorder=0,
    )
    fitness_manual_locations = [
        ((x / (ymax - 6)) ** 2, ymax - 6) for x in fitness_levels
    ]
    ax.clabel(fitness_isolines, manual=fitness_manual_locations, **isoline_label_kwds)

isoline_handles = [fom_isolines.legend_elements()[0][0]]
labels = [r"$\epsilon_\text{total} \cdot E_g = c$"]
if show_fitness_isolines:
    isoline_handles += [fitness_isolines.legend_elements()[0][0]]
    labels += [r"$\sqrt{\epsilon_\text{total}} \cdot E_g = c$"]
isoline_legend = ax.legend(isoline_handles, labels, loc="lower left")
for handle, text in zip(
    isoline_legend.legend_handles, isoline_legend.get_texts(), strict=True
):
    text.set_color(handle.get_color())


save_fig(ax, f"{PAPER_FIGS}/pareto-{'-vs-'.join(names)}.pdf")


# %%
fom_tresh = max(fom_levels)
fom_count_us = sum(df_us[fom_pbe_col] > fom_tresh)
print(f"on {today}:\nhit rate of materials with FoM > {fom_tresh}:")


for name, df in [
    ("Petousis et al.", df_petousis),
    ("Qu et al.", df_qz3),
    ("us", df_us),
    # 0.1 eV is the same threshold applied in Petousis 2016
    # (https://nature.com/articles/sdata2016134, fig. 2) and QZ3 2020
    # https://rdcu.be/cCMga for materials to be included in their results
    ("us for band gap > 0.1 eV", df_us.query("bandgap_us > 0.1")),
]:
    high_fom_count = sum(df[fom_pbe_col] > fom_tresh)
    hit_rate = high_fom_count / len(df)
    print(f" - {name}: {high_fom_count:,} / {len(df):,} = {hit_rate:.1%}")

# on 2022-06-01:
# hit rate of materials with FoM > 240:
# - Petousis et al.: 7 / 139 = 5.0%
# - Qu et al.: 15 / 441 = 3.4%
# - us: 155 / 2,680 = 5.8%
# - us for  band gap > 0.1 eV: 154 / 2,063 = 7.5%


# %% reproduce the above plot with plotly express
fig = px.scatter(
    df_mp,
    x=diel_total_mp_col,
    y=bandgap_mp_col,
    marginal_x="histogram",
    marginal_y="histogram",
)
fig.data[0].visible = False
# make right marginal narrower
fig.layout.xaxis1.update(matches=None, domain=[0, 0.84])
fig.layout.xaxis2.update(matches=None, domain=[0.85, 1])

markers = ("circle", "diamond", "square", "x", "star")
colors = sns.color_palette("tab10").as_hex()

datasets = [
    (df_us[[diel_total_pbe_col, bandgap_us_col]], f"{len(df_us):,} this work"),
    (df_qz3[[diel_total_pbe_col, "bandgap_pbe"]], f"{len(df_qz3):,} Qu et al. 2020"),
    (
        df_petousis[["diel_total_petousis", bandgap_mp_col]],
        f"{len(df_petousis):,} Petousis et al. 2017",
    ),
]
for idx, (df, label) in enumerate(datasets):
    diel_col, gap_col = list(df)
    fig.add_scatter(
        x=df[diel_col],
        y=df[gap_col],
        mode="markers",
        name=label,
        marker=dict(symbol=markers[idx], color=colors[idx]),
        opacity=0.8,
    )

xmax, ymax = 1000, 14
fig.layout.xaxis.update(range=[-0.25, np.log10(xmax)], type="log")
fig.layout.yaxis.update(range=[-2.2, np.log10(ymax)], type="log")
x_range = np.logspace(np.log10(1), np.log10(xmax), 100)
y_range = np.logspace(np.log10(0.015), np.log10(ymax), 100)
xs, ys = np.meshgrid(x_range, y_range)
zs = xs * ys

# move labels to end of line
for level in (30, 60, 120, 240):
    fig.add_contour(
        x=x_range,
        y=y_range,
        z=zs,
        colorscale="Blues",
        contours=dict(
            start=level,
            end=level,
            coloring="lines",  # rather than "fill"
            showlabels=True,
            labelfont=dict(size=15),
        ),
        line=dict(dash="dash", width=2),
        showscale=False,
    )

fig.update_layout(
    # xaxis2_type="log", # make right marginal y-axis log-scaled
    # yaxis3_type="log",  # make top marginal y-axis log-scaled
)
fig.layout.legend.update(x=0, y=0)
fig.layout.margin.update(l=0, r=0, t=0, b=0)

fig.show()
save_fig(fig, f"{PAPER_FIGS}/pareto-us-vs-petousis-vs-qu-plotly.pdf")
