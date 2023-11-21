# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch

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
df_diel_train = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-train.json.bz2")

# discard negative and unrealistically large dielectric constants
df_diel_train = df_diel_train.query(f"0 < {diel_total_mp_col} < 2000")


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
mp_kde = True  # whether to plot a kernel density of MP dielectric training data
names: list[str] = []
if mp_kde:
    ax = sns.kdeplot(
        x=df_diel_train.diel_total_mp,
        y=df_diel_train[bandgap_mp_col],
        # cut=0,  # how far evaluation grid extends, 0 truncates at data limits
        fill=True,
        cmap="Blues",
        zorder=0,
        label=f"KDE of {len(df_diel_train):,} MP DFPT calcs",
    )
else:
    ax = plt.gca()
for df, (name, label), color, marker in (
    (  # for main text
        df_us[[diel_total_pbe_col, bandgap_us_col]],
        ("us", f"{len(df_us):,} this work"),
        "darkorange",
        "o",  # circle
    ),
    # (  # for SI
    #     df_qz3[[diel_total_pbe_col, "bandgap_pbe"]],
    #     ("qu", f"{len(df_qz3):,} Qu et al. 2020"),
    #     "red",
    #     "D",  # diamond
    # ),
    # (
    #     df_petousis[["diel_total_petousis", bandgap_mp_col]],
    #     ("petousis", f"{len(df_petousis):,} Petousis et al. 2017"),
    #     "blue",
    #     "s",  # square
    # ),
    # ( # splitting by substitution and MP/WBM structures, not used in paper
    #     df_us.query(f"~{id_col}.str.contains('->')")[
    #         [diel_total_pbe_col, bandgap_us_col]
    #     ],
    #     f"{sum(~df_us.index.str.contains('->')):,} MP/WBM structures",
    #     "purple",
    #     "x",  # cross
    # ),
    # (
    #     df_us.query(f"{id_col}.str.contains('->')")[
    #         [diel_total_pbe_col, bandgap_us_col]
    #     ],
    #     f"{sum(df_us.index.str.contains('->')):,} substitution structures",
    #     "green",
    #     "P",  # plus
    # ),
):
    x_col, y_col = list(df)
    df.plot.scatter(
        x=x_col, y=y_col, ax=ax, label=label, color=color, marker=marker, alpha=0.5
    )
    names.append(name)


handles = ax.legend().legend_handles
for handle in handles:
    handle.set_sizes([50])
if mp_kde:
    kde_label = f"KDE of {len(df_diel_train):,} MP DFPT calcs"
    kde_handle = Patch(label=kde_label, facecolor="deepskyblue")
    handles = (*handles, kde_handle)
ax.add_artist(ax.legend(handles=handles, loc="upper right", frameon=False))

ax.set_xlabel(r"$\epsilon_\text{total}$")
ax.set_ylabel(r"$E_\text{gap,PBE}$ (eV)")

# ax.set(xlim=[0, xmax := 400], ylim=[0, ymax := 8])
ax.set(xscale="log", yscale="log", xlim=[1, xmax := 1800], ylim=[0.3, ymax := 15])

isoline_label_kwds = dict(inline_spacing=3, fontsize=10, inline=True)

fom_vals = np.outer(np.arange(ymax + 1), np.arange(xmax + 1))
fom_levels = [30, 60, 120, 240]
fom_isolines = ax.contour(
    fom_vals, levels=fom_levels, linestyles="--", colors=["purple"], zorder=0
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


plt.savefig(f"{PAPER_FIGS}/pareto-{'-vs-'.join(names)}.pdf")


# %%

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
