"""Supplemental Material (https://bit.ly/3DHHX9P) from Petousis et al.
https://journals.aps.org/prb/abstract/10.1103/PhysRevB.93.115151.

Title: "Benchmarking density functional perturbation theory to enable high-throughput
screening of materials for dielectric constant and refractive index"
Dated: March 8, 2016

Calculated and experimental (found in literature) values for the dielectric constants
and refractive indices. More specifically, the distinct eigenvalues of the total and
electronic dielectric tensors.

References can be resolved on page 4 of the SI linked above.
"""


# %%
import numpy as np
import pandas as pd
import plotly.express as px
from adjustText import adjust_text
from aviary.wren.utils import get_aflow_label_from_spglib
from mp_api.client import MPRester
from pymatviz import annotate_metrics, ptable_heatmap_plotly
from pymatviz.io import df_to_pdf
from pymatviz.utils import add_identity_line

from dielectrics import (
    DATA_DIR,
    PAPER_FIGS,
    diel_exp_col,
    diel_total_us_col,
    formula_col,
    id_col,
    n_sites_col,
    spg_col,
)
from dielectrics.db.fetch_data import df_diel_from_task_coll
from dielectrics.plots import plt


# %%
df_exp = pd.read_csv(f"{DATA_DIR}/others/petousis/exp-petousis.csv").set_index(
    id_col, drop=False
)

df_exp.index.name = id_col
struct_col = "structure_mp"
# 3 mp-id's appear in both Petousis 2016/17: mp-2964, mp-5238, mp-5342
df_exp[df_exp.index.duplicated(keep=False)].sort_index()
df_exp = df_exp.drop_duplicates(keep="first", subset=id_col)
df_exp = df_exp.sort_values(diel_exp_col, ascending=False)
assert len(df_exp) == 136


# %%
mp_data = []
for depr in (True, False):
    mp_data += MPRester(use_document_model=False).materials.summary.search(
        deprecated=depr, material_ids=list(df_exp.index)
    )
    # mp_data += MPRester(use_document_model=False).materials.search(
    #     deprecated=depr, task_ids=list(df_exp.index)
    # )

assert len(df_exp) == len(mp_data), f"{len(df_exp)=} != {len(mp_data)=}"


# %%
df_mp = pd.DataFrame(mp_data).set_index(id_col, drop=False)

df_mp = df_mp.rename(columns={"band_gap": "bandgap"})
cols = "material_id structure bandgap e_total e_ionic e_electronic n".split()
df_exp[
    df_mp[cols].add_suffix("_mp").columns.str.replace("^e_", "diel_", regex=True)
] = df_mp[cols]


# %%
df_us = df_diel_from_task_coll(
    {"series": {"$regex": "^Petousis Experimental 201(6|7)$"}}, col_suffix="_us"
)

df_us = df_us[~df_us.index.duplicated()]

df_exp[diel_total_us_col] = df_us[diel_total_us_col]


# %%
df_exp[n_sites_col] = df_exp[struct_col].map(len)
df_exp["formula"] = df_exp[struct_col].map(lambda x: x.composition.reduced_formula)
df_exp["n_elems"] = df_exp[struct_col].map(lambda x: len(x.composition))
df_exp[n_sites_col] = df_exp[struct_col].map(len)
df_exp[spg_col] = df_exp[struct_col].map(lambda x: x.get_space_group_info())

df_exp["wyckoff"] = [
    get_aflow_label_from_spglib(struct) for struct in df_exp[struct_col]
]


# %%
n_overlap_exp_mp = len(df_exp[~df_exp.index.duplicated()].eps_electronic_mp.dropna())
print(
    f"{n_overlap_exp_mp}/{len(df_exp)} = {n_overlap_exp_mp/len(df_exp):.1%} of "
    "experimental dataset was already in training set. Not a good test for dielectric "
    "model performance!"
)


# %% only needed one
def diel_tensor_to_const(csv: str) -> float:
    """Parse anisotropic dielectric tensors into arrays and take the mean."""
    diel_xyz = np.fromstring(csv, sep=",")
    n_dim = len(diel_xyz)

    if n_dim == 2:
        return (2 * diel_xyz[0] + diel_xyz[1]) / 3
    if n_dim in (1, 3):
        return diel_xyz.mean()
    raise ValueError(f"unexpected number of components in dielectric tensor: {n_dim}")


# for col in ("total_petousis", "elec_petousis", "total_exp"):
#     df_exp[f"diel_{col}"] = df_exp[f"diel_{col}"].fillna(
#         df_exp[f"eps_{col}"].map(diel_tensor_to_const)
#     )


# %%
ptable_heatmap_plotly(
    df_exp[formula_col],
    color_bar=dict(title="Element count"),
    count_mode="occurrence",
    fmt=".0f",
)


# %%
ax = df_exp.plot.scatter(x="n_exp", y="n_petousis", s=40, backend="matplotlib")

ax.autoscale(False)
ax.axline([0, 0], slope=1, color="black", ls="dashed", alpha=0.5, zorder=0, lw=2)
ax.axline([0, 0], slope=1.25, color="red", ls="dotted", alpha=0.5, zorder=0, lw=2)
ax.axline([0, 0], slope=0.75, color="red", ls="dotted", alpha=0.5, zorder=0, lw=2)

ax.annotate("+25%", xy=(0.5, 0.7), xycoords="axes fraction", color="red")
ax.annotate("-25%", xy=(0.6, 0.3), xycoords="axes fraction", color="red")

ax.set(xlabel=r"$n_\mathrm{exp}$", ylabel=r"$n_\mathrm{Petousis}$")
n_points = len(df_exp.dropna(subset=["n_exp", "n_petousis"]))
title = f"Experimental vs Petousis DFT refractive index ({n_points:,} samples)"
ax.set_title(title, y=1.03, fontsize=14)

annotate_metrics(df_exp.n_exp, df_exp.n_petousis, loc="upper left")

# plt.savefig("plots/refractive-index-exp-petousis.pdf")


# %%
n_points = len(df_exp[["diel_total_petousis", diel_exp_col]].dropna())

fig = px.scatter(
    df_exp,
    x=diel_exp_col,
    y="diel_total_petousis",
    hover_data=[id_col, "formula", "n_petousis", "n_exp", "polycrystalline"],
    color="n_exp",
    height=700,
    width=1000,
    log_x=(log_log := True),
    log_y=log_log,
    labels={
        diel_exp_col: "Experimental Permittivity",
        "diel_total_petousis": "Petousis Permittivity",
        "n_exp": "refractive<br>index <i>n<i>",
    },
)

fig.layout.title = dict(
    text=f"Experimental vs Petousis Permittivity ({n_points:,} points)", x=0.5
)
# use marker_sizeref to apply scaling factor to marker sizes defined by column value
fig.update_traces(marker={"size": 15})
if log_log:
    fig.layout.xaxis.range = [0.7, 3]
    fig.layout.yaxis.range = [0.7, 3]
add_identity_line(fig)


# %%
def ceil_div(a: float, b: float) -> int:
    """Return the ceiling of an integer division, i.e. always round up."""
    return int(-(a // -b))


# sources = ["exp", "us", "petousis"]
# sources = ["exp", "us", "petousis", "mp"]
# xy_pairs = list(itertools.combinations(sources, 2))
xy_pairs = [("exp", "us"), ("exp", "petousis"), ("exp", "mp")]
n_rows = 1  # ceil_div(len(xy_pairs), len(sources))
n_cols = len(xy_pairs)  # len(sources)
fig_height = n_rows * 4
fig_width = n_cols * 5

fig, axs = plt.subplots(n_rows, n_cols, figsize=(fig_width, fig_height))

super_title = "Blue points from Petousis 2017, red ones from Petousis 2016"
fig.suptitle(super_title, y=1.15)

outlier_tresh = 0.5  # 50%
lb, ub = 1 - outlier_tresh, 1 + outlier_tresh  # lower and upper bounds


for ax, (src1, src2) in zip(axs.flat, xy_pairs, strict=True):
    col_name1, col_name2 = f"diel_total_{src1}", f"diel_total_{src2}"
    col1, col2 = df_exp[col_name1], df_exp[col_name2]
    cs = df_exp.series.map({"Petousis 2017": "red", "Petousis 2016": "blue"})

    df_exp.plot.scatter(x=col_name1, y=col_name2, color=cs, ax=ax, backend="matplotlib")

    ax.set(yscale="log", xscale="log")
    ax.set_xlabel(f"$\\epsilon_\\mathrm{{total}}^\\mathrm{{{src1}}}$", fontsize=15)
    ax.set_ylabel(f"$\\epsilon_\\mathrm{{total}}^\\mathrm{{{src2}}}$", fontsize=15)

    points = len(df_exp[[col_name1, col_name2]].dropna())
    labels = {"petousis": "Petousis", "exp": "Experiment", "mp": "MP", "us": "Us"}
    title = f"$\\bf {labels[src1]}$ vs $\\bf {labels[src2]}$ ({points:,} points)"
    ax.set_title(label=title, y=1.03, fontsize=16)

    weak_outliers = (col1 * lb > col2) | (col1 * ub < col2)
    far_outliers = (col1 * lb / 2 > col2) | (col1 * ub * 2 < col2)
    outliers = sum(weak_outliers) / len(df_exp)  # fraction of weak outliers
    annotate_metrics(
        col1,
        col2,
        ax=ax,
        suffix=f"{outliers = :.1%}",
        fmt=".3",
        prop={"size": 13},
        loc="upper left",
    )

    # annotate outliers with formula
    annos = []
    for tupl in df_exp[far_outliers].itertuples():
        row = tupl._asdict()
        formula, x_pos, y_pos = row["formula"], row[col_name1], row[col_name2]
        anno = ax.annotate(
            formula,
            xy=(x_pos, y_pos),
            ha="center",
            fontsize=12,
        )
        annos.append(anno)
    adjust_text(annos, ax=ax, arrowprops=dict(arrowstyle="-", color="black", lw=0.5))

    ax.autoscale(False)
    ax.axline([0, 0], [1, 1], c="black", ls="dashed", alpha=0.5, zorder=0)
    ax.fill_between([0, 1e4], [0, lb * 1e4], [0, ub * 1e4], color="purple", alpha=0.1)

axs[0].annotate(
    f"+{outlier_tresh:.0%}", xy=(0.42, 0.8), xycoords="axes fraction", fontsize=10
)
axs[0].annotate(
    f"-{outlier_tresh:.0%}", xy=(0.6, 0.6), xycoords="axes fraction", fontsize=10
)


fig.suptitle("")  # remove suptitle in saved figure
plt.savefig(f"{PAPER_FIGS}/exp-vs-us-vs-petousis-vs-mp-diel-total.pdf")


# %%
color_cols = {
    diel_exp_col: "ε<sub>exp</sub>",
    diel_total_us_col: "ε<sub>us</sub>",
    "diel_total_petousis": "ε<sub>Petousis</sub>",
    "diel_total_mp": "ε<sub>MP</sub>",
    n_sites_col: "n<sub>sites</sub>",
    "n_elems": "n<sub>elems</sub>",
}
info_cols = {
    "material_id": "Material ID",
    "formula": "Formula",
    # "polycrystalline": "Polycrystalline",
    spg_col: "Spacegroup",
}
if "spacegroup symbol" not in df_exp:
    spg_dict = zip(
        ["spacegroup symbol", spg_col],
        zip(*df_exp[spg_col], strict=True),
        strict=True,
    )
    df_exp = df_exp.assign(**dict(spg_dict))

df_exp[[*info_cols, *color_cols]].to_csv(
    f"{DATA_DIR}/others/petousis/exp-vs-dfpt-diel-const.csv", index=False
)

vmin, vmax = df_exp[list(color_cols)].min(), df_exp[list(color_cols)].max()

# split dataframes into two tables for and write each to a separate PDF
for idx, sub_df in enumerate(np.array_split(df_exp.reset_index(drop=True), 2), 1):
    sub_df.index += 1  # start index at 1, must come after reset_index
    styler = (
        sub_df[[*info_cols, *color_cols]]
        .rename(columns=color_cols | info_cols)
        .style.format(precision=1)
    )
    for key, col in color_cols.items():
        styler = styler.background_gradient(
            subset=col, cmap="viridis", axis=None, vmin=vmin[key], vmax=vmax[key]
        )
    df_to_pdf(styler, f"{PAPER_FIGS}/table-exp-data-{idx}.pdf")
