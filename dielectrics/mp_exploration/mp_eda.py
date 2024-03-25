"""Exploratory data analysis of dielectric materials in Materials Project.
Mostly to confirm our initial hypothesis that there's 1/x relationship between
band gap and refractive index which could yield an interesting optimization/discovery
problem of finding materials that push beyond this Pareto front.

Lee group meeting presentation 7 Jun 2021:
https://docs.google.com/presentation/d/1yDkW4ml_FSdwlWxCpNMz-1oxdkeScDRVZgZQAScsgSs
"""

# %% from https://colab.research.google.com/drive/131MZKKeOhoseoVTJmPuOXVJvDoNes1ge
import numpy as np
import pandas as pd
import plotly.express as px
from matplotlib.patches import Ellipse
from pymatgen.util.string import latexify
from pymatviz import ptable_heatmap, spacegroup_hist
from pymatviz.io import save_fig

from dielectrics import PAPER_FIGS, Key
from dielectrics.plots import plt


# %%
df_diel_mp = pd.read_json("data/mp-diel-train.json.bz2")

df_diel_mp = df_diel_mp.query("0 < diel_total_mp < 2000")
# df_diel_mp[Keys.crystal_sys] = df_diel_mp.pop("spacegroup.crystal_system")


# %% Band gap vs different parts of dielectric constant
height = (n_rows := 1) * 7
width = (n_cols := 3) * 8

fig, axs = plt.subplots(n_rows, n_cols, figsize=(width, height))


x_max, y_max = 400, 8
fom_vals = np.outer(np.arange(y_max + 1), np.arange(x_max + 1))

for ax, x_col in zip(
    axs.flat, ("diel_total_mp", "diel_ionic_mp", "diel_elec_mp"), strict=True
):
    df = df_diel_mp.query(f"0 < {x_col} < {x_max}")
    *_, mappable = ax.hist2d(
        df[x_col], df[Key.bandgap_mp], bins=(150, 150), cmin=1, cmap="Blues_r"
    )

    diel_part = x_col.split("_")[1]  # "diel_total_mp" -> "total"
    exponent = {"elec": r"\infty", "ionic": "0"}.get(diel_part, diel_part)
    diel_part = {"elec": "electronic"}.get(diel_part, diel_part)  # elec -> electronic
    x_label = rf"{diel_part} permittivity $\epsilon^\mathrm{{{exponent}}}$"

    ax.set(xlim=[0, x_max], xlabel=x_label)
    ax.set(ylim=[0, y_max], ylabel="$E_\\mathrm{gap}$ (eV)")

    fom_levels = (30, 120, 240)
    fom_iso_lines = ax.contour(
        fom_vals,
        levels=fom_levels,
        linestyles="--",
        linewidths=3,
        colors=["red", "orange", "green"],
    )
    ax.clabel(
        fom_iso_lines,
        manual=[(0.9 * x_max, x / (0.95 * x_max)) for x in fom_levels],
        inline=True,  # interrupt contour lines to place labels
        inline_spacing=3,  # how much whitespace to leave around label
        fontsize=14,
    )

    # Annotation of scatter points with fom_level > 240
    for row in df.to_dict(orient="records"):
        fom_row = row[x_col] * row[Key.bandgap_mp]
        if "total" in x_col and fom_row > 600:
            continue  # don't overwrite the 'Flash storage'/'CPU'/'RAM' bubbles
        if fom_row > (50 if "elec" in x_col else 500):
            anno = latexify(row["formula"])  # make numbers in formula subscript
            ax.annotate(anno, (row[x_col], row[Key.bandgap_mp]), ha="right", va="top")


handles, labels = fom_iso_lines.legend_elements()
labels = [r"$\epsilon \cdot E_\mathrm{gap}$ isolines"]
for ax in axs[::2]:  # exclude middle Axes
    cb_ax = ax.inset_axes([0.57, 0.92, 0.4, 0.03])
    cbar = fig.colorbar(mappable, cax=cb_ax, orientation="horizontal")
    # place colorbar title 'Hist density' left of colorbar
    cbar.ax.set_title("Hist density", loc="left", fontsize=14)
    ax.legend(handles, labels, frameon=False, loc=(0.65, 0.8))

# plt.colorbar(mappable)  # looks too tall, prefer inset_axes

high_k_ell = Ellipse(
    xy=(220, 4.2),
    width=300,
    height=4.5,
    angle=-0.8,
    facecolor="None",
    edgecolor="gray",
    alpha=0.4,
)
axs[0].add_patch(high_k_ell)

axs[0].annotate(
    "ideal high-$\\kappa$\ndielectrics",
    xy=(0.65, 0.65),
    xycoords=high_k_ell,
    ha="center",
    va="center",
    rotation=-38,
).set(color="gray", fontsize=16)


for (x1, x2), (y1, y2), clr, txt in (
    ((150, 300), (6, 7.5), "blue", "Flash storage"),
    ((200, 350), (4.2, 6.2), "teal", "CPU"),
    ((280, 430), (2.5, 4), "orange", "RAM"),
):
    ellipse = Ellipse(
        xy=(x1, y1), width=x2 - x1, height=y2 - y1, angle=-0.3, color=clr, alpha=0.2
    )
    axs[0].add_patch(ellipse)

    ha = va = "center"  # horizontal and vertical alignment
    axs[0].annotate(
        txt, rotation=-0.3 * 45, xy=(0.5, 0.5), xycoords=ellipse, ha=ha, va=va
    )


# file_part = "total"  # for introduction
file_part = "parts"  # for SI
if file_part == "total":
    axs[1].remove()
    axs[2].remove()
else:
    axs[0].remove()

save_fig(fig, f"{PAPER_FIGS}/diel-{file_part}-vs-bandgap-mp.pdf")


# %%
plt.figure(figsize=(10, 8))

plt.title(f"{len(df_diel_mp):,} MP materials with computed dielectric properties")

plt.hexbin(
    # squared refractive index n^2 = electronic dielectric constant epsilon_r
    df_diel_mp.query("n_mp < 4").n_mp ** 2,
    df_diel_mp.query("n_mp < 4")[Key.bandgap_mp],
    mincnt=1,
)


epsilon = np.linspace(0.1, 16, 50)
for num in [4, 9, 16]:
    plt.plot(epsilon, num / epsilon, "r--", lw=3)

plt.colorbar(label="Density")
plt.xlabel(r"Electronic Dielectric Constant $\epsilon_\infty$")
plt.ylabel(r"PBE Band Gap $E_\mathrm{gap}$ / eV")

plt.legend()

plt.xlim((0, 16))
plt.ylim((0, 9.5))
# # plt.savefig("plots/diel-elec-vs-bandgap-front-hexbin.pdf")


# %%
plt.figure(figsize=(10, 8))

plt.title(f"{len(df_diel_mp):,} MP materials with computed dielectric properties")

plt.hexbin(np.log(df_diel_mp.diel_ionic_mp), df_diel_mp[Key.bandgap_mp], mincnt=1)


# epsilon = np.linspace(0.1, 16, 50)
# for num in [4, 9, 16]:
#     plt.plot(epsilon, num / epsilon, "r--", lw=3)

plt.colorbar(label="Density")
plt.xlabel(r"log dielectric constant $\log(\epsilon)$")
plt.ylabel(r"PBE Bandgap $E_\mathrm{gap}$ / eV")


plt.xlim((None, 8))
plt.ylim((-0.1, 9.5))
# plt.savefig("plots/diel-elec-vs-bandgap.pdf")


# %%
ptable_heatmap(df_diel_mp.formula, log=True)
plt.title("Elemental Prevalence among MP Dielectric Training Materials")
# plt.savefig("plots/mp-diel-train-elements-log.pdf")


# %%
spacegroup_hist(df_diel_mp["spacegroup.number"])
plt.title("Spacegroup distribution among MP Dielectric Training Materials")
# plt.savefig("plots/mp-diel-train-spacegroup-hist.pdf")


# %%
df_diel_screen = pd.read_csv("data/mp-diel-screen.csv.bz2")


# %%
ptable_heatmap(df_diel_screen.formula, log=True)
plt.title("Elemental Prevalence among MP Dielectric Screening Materials")
# plt.savefig("plots/mp-diel-screen-elements-log.pdf")


# %%
spacegroup_hist(df_diel_screen["spacegroup_mp"])
plt.title("Spacegroup distribution among MP Dielectric Screening Materials")
# plt.savefig("plots/mp-diel-screen-spacegroup-hist.pdf")


# %%
df_diel_mp[["diel_elec_mp", "diel_ionic_mp"]].hist(bins=100, log=True, figsize=[18, 4])


# %% recreate figure 3 from Atomate Dielectric paper https://rdcu.be/clY2X with MP
# dielectric data
df_diel_mp = df_diel_mp.query("0 < diel_total_mp < 1000")

df_melted = df_diel_mp.melt(
    id_vars=[Key.crystal_sys, "material_id", "formula"],
    value_vars=["diel_elec_mp", "diel_ionic_mp"],
    var_name="component",
    value_name="dielectric constant",
    ignore_index=False,
)

df_melted["component"] = df_melted.component.map(
    {"diel_elec_mp": "electronic", "diel_ionic_mp": "ionic"}
)
cry_sys_order = (
    "cubic hexagonal trigonal tetragonal orthorhombic monoclinic triclinic".split()
)

fig = px.strip(
    df_melted,
    x=Key.crystal_sys,
    y="dielectric constant",
    color="component",
    color_discrete_map={"electronic": "blue", "ionic": "green"},
    hover_data={"material_id": True, "formula": True, Key.crystal_sys: False},
    # sort strips from high to low spacegroup number
    category_orders={Key.crystal_sys: cry_sys_order},
    height=500,
    width=1000,
).update_traces(jitter=1)
fig.layout.margin.update(l=30, r=30, t=30, b=30)
fig.layout.legend.update(x=1, y=1, xanchor="right")


def rgb_color(val: float, max: float) -> str:  # noqa: A002
    """Convert a value between 0 and max to a color between red and blue."""
    return f"rgb({255 * val / max:.1f}, 0, {255 * (max - val) / max:.1f})"


n_top, x_ticks = 30, dict.fromkeys(cry_sys_order, "")
for cry_sys, df_group in df_diel_mp.groupby(Key.crystal_sys):
    ionic_top = df_group.diel_ionic_mp.nlargest(n_top).mean()
    elec_top = df_group.diel_elec_mp.nlargest(n_top).mean()
    ionic_clr = rgb_color(ionic_top, 212)
    elec_clr = rgb_color(elec_top, 124)
    x_ticks[cry_sys] = (
        f"<b>{cry_sys}</b><br>{len(df_group):,} = {len(df_group) / len(df_diel_mp):.0%}"
        f"<br><span style='color:{elec_clr}'><b>{elec_top:.0f}</b></span>      "
        f"<span style='color:{ionic_clr}'><b>{ionic_top:.0f}</b></span>"
    )

fig.layout.xaxis.update(tickvals=list(range(7)), ticktext=list(x_ticks.values()))

# fig.write_image("plots/mp-diel-elec-vs-ionic-strip.pdf")
fig.show()
