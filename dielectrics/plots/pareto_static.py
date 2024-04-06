# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns
from matplotlib.patches import Patch
from pymatviz.io import save_fig

from dielectrics import DATA_DIR, PAPER_FIGS, Key, today
from dielectrics.db.fetch_data import df_diel_from_task_coll


__author__ = "Janosh Riebesell"
__date__ = "2022-03-02"


# %%
df_mp = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-train.json.bz2")

# discard negative and unrealistically large dielectric constants
df_mp = df_mp.query(f"0 < {Key.diel_total_mp} < 2000")


# %% qz3 for author last name initials (https://rdcu.be/cCMga)
# unprocessed JSON from https://doi.org/10.6084/m9.figshare.10482707.v2
df_qz3 = pd.read_csv(f"{DATA_DIR}/others/qz3/qz3-diel.csv.bz2")

# Petousis 2017: https://nature.com/articles/sdata2016134
df_petousis = pd.read_csv(f"{DATA_DIR}/others/petousis/exp-petousis.csv").set_index(
    Key.mat_id, drop=False
)

df_petousis[Key.fom_pbe] = (
    df_petousis[Key.bandgap_mp] * df_petousis["diel_total_petousis"]
)
df_qz3[Key.fom_pbe] = df_qz3[Key.bandgap_pbe] * df_qz3[Key.diel_total_pbe]


# %%
df_us = df_diel_from_task_coll({})
assert all(df_us[Key.diel_total_pbe] > 0), "negative dielectric, this shouldn't happen"


# %%
plt.figure(figsize=(8, 5))
mp_kde = False  # whether to plot a kernel density of MP dielectric training data
names: list[str] = []
if mp_kde:
    ax = sns.kdeplot(
        x=df_mp[Key.diel_total_mp],
        y=df_mp[Key.bandgap_mp],
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
        df_us[[Key.diel_total_pbe, Key.bandgap_us]],
        ("us", f"{len(df_us):,} this work"),
    ),
    (  # for SI
        df_qz3[[Key.diel_total_pbe, Key.bandgap_pbe]],
        ("qu", f"{len(df_qz3):,} Qu et al. 2020"),
    ),
    (
        df_petousis[["diel_total_petousis", Key.bandgap_mp]],
        ("petousis", f"{len(df_petousis):,} Petousis et al. 2017"),
    ),
    # (  # splitting by substitution and MP/WBM structures, not used in paper
    #     df_us.query(f"~{Keys.mat_id}.str.contains('->')")[
    #         [Keys.diel_total_pbe, Keys.bandgap_us]
    #     ],
    #     f"{sum(~df_us.index.str.contains('->')):,} MP/WBM structures",
    # ),
    # (
    #     df_us.query(f"{Keys.mat_id}.str.contains('->')")[
    #         [Keys.diel_total_pbe, Keys.bandgap_us]
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
ax.set_ylabel(r"$E_\text{gap\ PBE}$ (eV)")

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

save_fig(ax, f"{PAPER_FIGS}/pareto-{'-vs-'.join(names)}-matplotlib.pdf")

for level in fom_levels:
    n_hits = sum(df_us[Key.fom_pbe] > level)
    print(f"our materials with FoM > {level}: {n_hits:,} ({n_hits / len(df_us):.1%})")


# %%
fom_tresh = max(fom_levels)
fom_count_us = sum(df_us[Key.fom_pbe] > fom_tresh)
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
    high_fom_count = sum(df[Key.fom_pbe] > fom_tresh)
    hit_rate = high_fom_count / len(df)
    print(f" - {name}: {high_fom_count:,} / {len(df):,} = {hit_rate:.1%}")

# on 2022-06-01:
# hit rate of materials with FoM > 240:
# - Petousis et al.: 7 / 139 = 5.0%
# - Qu et al.: 15 / 441 = 3.4%
# - us: 155 / 2,680 = 5.8%
# - us for  band gap > 0.1 eV: 154 / 2,063 = 7.5%


# %% reproduce the above plot with plotly express
col_map = {
    "diel_total_petousis": Key.diel_total_pbe,
    Key.bandgap_mp: Key.bandgap_pbe,
    Key.bandgap_us: Key.bandgap_pbe,
}
src_col = "Source"

df_us[src_col] = f"{len(df_us):,} this work"
df_qz3[src_col] = f"{len(df_qz3):,} Qu et al. 2020"
df_petousis[src_col] = f"{len(df_petousis):,} Petousis et al. 2017"
datasets = [
    df_us[[Key.diel_total_pbe, Key.bandgap_us, src_col]],
    df_qz3[[Key.diel_total_pbe, Key.bandgap_pbe, src_col]],
    df_petousis[["diel_total_petousis", Key.bandgap_mp, src_col]],
]

fig = px.scatter(
    pd.concat(df.rename(columns=col_map) for df in datasets),
    x=Key.diel_total_pbe,
    y=Key.bandgap_pbe,
    color=src_col,
    marginal_x="rug",
    marginal_y="rug",
    color_discrete_sequence=sns.color_palette("tab10").as_hex(),
    log_x=True,
    log_y=True,
    symbol=src_col,  # change markers for each dataset
    opacity=0.7,
)

# make marginals narrower
fig.layout.xaxis1.update(domain=[0, 0.88])
fig.layout.xaxis2.update(domain=[0.9, 1], range=(-0.8, 2))
fig.layout.xaxis3.update(domain=[0, 0.88], mirror=False)
fig.layout.yaxis1.update(domain=[0, 0.83])
fig.layout.yaxis2.update(domain=[0, 0.83], mirror=False)
fig.layout.yaxis3.update(domain=[0.86, 1], range=(-1, 2.5))

# add FoM isolines
xmax, ymax = 1000, 14
fig.layout.xaxis.update(range=[-0.02, np.log10(xmax)])
fig.layout.yaxis.update(range=[-2.1, np.log10(ymax)])
x_range = np.logspace(np.log10(1), np.log10(xmax), 100)
y_range = np.logspace(np.log10(0.015), np.log10(ymax), 100)
xs, ys = np.meshgrid(x_range, y_range)
zs = xs * ys

for level in (30, 60, 120, 240):
    contour_kwds = dict(coloring="lines", showlabels=True, labelfont=dict(size=16))
    fig.add_contour(
        x=x_range,
        y=y_range,
        z=zs,
        colorscale="Blues",
        contours=dict(start=level, end=level, **contour_kwds),
        line=dict(dash="dash", width=2),
        showscale=False,
    )

fig.layout.legend.update(
    x=0, y=0, title=None, itemsizing="constant", bgcolor="rgba(255,255,255,0.5)"
)
fig.layout.margin.update(l=0, r=0, t=0, b=0)

fig.show()
img_path = f"{PAPER_FIGS}/pareto-us-vs-petousis-vs-qu-plotly.pdf"
save_fig(fig, img_path, width=550, height=350)
