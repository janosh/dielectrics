# ruff: noqa: PLW0602 Using global but no assignment is done
# %%
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import crystal_toolkit.components as ctc
import dash
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
from bson import ObjectId
from bson.objectid import InvalidId
from crystal_toolkit.settings import SETTINGS as CTK_SETTINGS
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from plotly.validators.scatter.marker import SymbolValidator

from dielectrics import (
    DATA_DIR,
    SelectionStatus,
    bandgap_mp_col,
    bandgap_us_col,
    diel_total_pbe_col,
    id_col,
    plotly_hover_cols,
    selection_status_col,
    today,
)
from dielectrics.db import db
from dielectrics.db.fetch_data import df_diel_from_task_coll


if TYPE_CHECKING:
    from pymatgen.core import Structure


module_dir = os.path.dirname(__file__)


# %% see db/readme.md for details on how candidates in each df were selected
df_all = df_diel_from_task_coll({}, cache=True).round(3)

df_diel_mp = pd.read_json(f"{DATA_DIR}/mp-exploration/mp-diel-train.json.bz2")
# discard negative and unrealistically large dielectric constants
df_diel_mp = df_diel_mp.query("0 < diel_total_mp < 2000").round(3)

# qz3 for author last name initials (https://rdcu.be/cCMga)
# unprocessed JSON from https://doi.org/10.6084/m9.figshare.10482707.v2
df_qz3 = pd.read_csv(f"{DATA_DIR}/others/qz3/qz3-diel.csv.bz2").round(3)

df_yim = pd.read_json(f"{DATA_DIR}/others/yim/dielectrics.json.bz2")
df_yim = df_yim.query(f"0 < {diel_total_pbe_col} < 1000").rename(
    columns={"possible_mp_id": id_col, "bandgap_gga": "bandgap_pbe"}
)
df_yim = df_yim.dropna(subset=[id_col, "formula"])
for accu in ["pbe", "hse"]:
    df_yim = df_yim.eval(f"fom_{accu} = bandgap_{accu} * {diel_total_pbe_col};")

df_yim = df_yim.nlargest(500, "fom_pbe")


# %%
def get_mp_link(data: str, text: str | None = None) -> str:
    """Generate link to MP details or search page depending if data is MP ID or formula.

    Args:
        data (str): material's MP ID or formula if not from MP.
        text (str, optional): Link text. Defaults to None.

    Returns:
        str: Possibly invisible link if text=None but still clickable.
    """
    # link to MP details page if MP ID is available, else link to MP search page
    # with material's formula
    if not data:
        raise ValueError(f"get_mp_link() got {data=} with {text=}")
    if data.startswith(("mp-", "mvc-")):
        # handle IDs of materials from elemental substitution
        data = data.split(":")[0]
        href = f"https://materialsproject.org/materials/{data}"
    else:
        query_params = f'{{"reduced_cell_formula":"{data}"}}'
        href = f"https://materialsproject.org/#search/materials/{query_params}"

    # make link invisible if no text so data point itself becomes the link
    style = "color: black;" if text else "opacity: 0;"  # white if dark
    # default text = 'x' so click area is roughly square
    return f"<a {href=} {style=}>{text or 'x'}</a>"


def create_text_col(df: pd.DataFrame, annotate_min_fom: float = 150) -> list[str]:
    """Insert a 'text' column into df with the materials's formula which when clicked
    links to its Materials Project details page if an MP ID is available.

    Args:
        df (pd.DataFrame): DataFrame with a 'formula' column.
        annotate_min_fom (float): minimum figure of merit to annotate a data point.
    """
    if id_col not in df:
        df[id_col] = ""

    # prioritize VASP over Wren over MP FoM, throw error if none found
    try:
        fom_col = next(filter(lambda c: c in df, fom_cols := ["fom_pbe", "fom_mp"]))
    except StopIteration:
        raise ValueError(f"None of {fom_cols} found in df") from None
    # only show formula as link text if material's FoM is > annotate_min_fom, else
    # scatter point will be clickable but without text
    text_col = df.formula.where(df[fom_col] > annotate_min_fom, None)
    mat_id_col = df.material_id.where(
        df.material_id.str.startswith(("mp-", "mvc-")), df.formula
    )
    return [
        get_mp_link(mat_id, text)
        for mat_id, text in zip(mat_id_col, text_col, strict=True)
    ]


def scatter(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    legend_name: str | None = None,
    **kwargs: Any,
) -> go.Figure:
    """Plotly express scatter plot which auto-picks unique marker colors and symbols
    by iterating through px.colors.qualitative.Dark24 and plotly's scatter marker
    validator. Also adds hover data with nicer labels and text annotations linking to
    MP detail pages where MP IDs are available.
    Can be used on its own but mostly called by scatter_with_quiver().
    """
    df["text"] = create_text_col(df, kwargs.pop("annotate_min_fom", 150))

    # drop cols with > 90% missing data
    df = df.dropna(thresh=0.1 * len(df), axis=1)
    df = df.fillna("n/a")  # fill remaining NaNs to avoid %{customdata[idx]}

    hover_keys = plotly_hover_cols & set(df)
    # hover_keys = sorted(hover_keys, key=list(pretty_col_names.values()).index)
    hover_keys = sorted(hover_keys)
    hover_data = dict.fromkeys(hover_keys, True)
    hover_data["text"] = False  # don't show text value in hover tooltip that's why
    # hover_data needs to be dict so we can set text to False, else could be list[str]

    global color_iter
    kwargs["color_discrete_sequence"] = [next(color_iter)]
    # use formula as default tooltip title
    kwargs["hover_name"] = kwargs.get("hover_name", id_col)
    if "_id" in df:
        # pass MongoDB object ID to dash callbacks, not user-visible but included in
        # events emitted by the figure
        kwargs["custom_data"] = ["_id"]

    visible = kwargs.pop("visible", "legendonly")  # default trace to hidden
    scatter_plot = px.scatter(
        df, x=x_col, y=y_col, hover_data=hover_data, text="text", **kwargs
    )

    global symbol_iter
    scatter_plot.update_traces(
        marker=dict(size=10, symbol=next(symbol_iter)), textposition="top center"
    )

    scatter_plot.data[0]["visible"] = visible
    scatter_plot.data[0]["showlegend"] = True
    scatter_plot.data[0]["name"] = legend_name

    return scatter_plot


def scatter_with_quiver(
    dfs: list[pd.DataFrame] | pd.DataFrame,
    scatter_1: dict[str, Any],
    scatter_2: dict[str, Any],
    legend_labels: tuple[str, str, str],
    lax_nan: bool = False,
) -> tuple[go.Figure, go.Figure, go.Figure]:
    """Create two scatter plots connected by quiver arrows, all in one legend group,
    initially hidden but can be individually activated by clicking their legend labels.
    """
    if isinstance(dfs, list) and len(dfs) == 2:
        df1, df2 = dfs
    elif isinstance(dfs, pd.DataFrame):
        df1 = df2 = dfs
    else:
        raise ValueError(f"Expected dataframe or list of 2 dfs, got {dfs}")

    x1, y1 = scatter_1.pop("x"), scatter_1.pop("y")
    x2, y2 = scatter_2.pop("x"), scatter_2.pop("y")

    for col, df in zip((x1, y1, x2, y2), (df1, df1, df2, df2), strict=True):
        if lax_nan:
            continue
        n_nans = df[col].isna().sum()
        assert n_nans == 0, f"{n_nans} NaNs in {col=} of label '{legend_labels[0]}'"

    delta_x = df2[x2] - df1[x1]
    delta_y = df2[y2] - df1[y1]

    scatter_1 = scatter(df1, x_col=x1, y_col=y1, **scatter_1)
    scatter_2 = scatter(df2, x_col=x2, y_col=y2, **scatter_2)

    quiver = ff.create_quiver(
        *[df1[x1], df1[y1], delta_x, delta_y],
        arrow_scale=0.02,
        scale=1,
        angle=3.14 * 0.01,  # smaller = steeper arrow head angle
        hoverinfo="skip",
    )

    traces = quiver.data + scatter_1.data + scatter_2.data

    for label, trace in zip(legend_labels, traces, strict=True):
        trace["showlegend"] = True

        trace["name"] = label

        trace["legendgroup"] = legend_labels[0]
        trace["legendgrouptitle"] = dict(text=legend_labels[0])

    quiver.data[0]["visible"] = "legendonly"
    quiver.data[0]["name"] = f"{len(df1):,} quiver"

    global fig
    if fig:
        fig.add_traces(traces)

    return scatter_1, scatter_2, quiver


# recreate symbol and color iterators every time we plot
symbol_iter = iter(SymbolValidator().values[2::6])  # noqa: PD011
color_iter = iter(px.colors.qualitative.Dark24)

fig = go.Figure()
fig.add_histogram2dcontour(
    x=df_diel_mp.diel_total_mp,
    y=df_diel_mp.bandgap_mp,
    name=f"KDE of {len(df_diel_mp):,} Materials Project<br>dielectric training points",
    showlegend=True,
    colorscale=[[0, "rgba(0, 0, 0, 0)"], [1, "red"]],
    showscale=False,
    hoverinfo="skip",
)


known_diels = [
    # formulas taken from fig. 4 in 2nd atomate dielectric paper https://rdcu.be/cBCqt
    *["AlTlF4", "Bi2SO2", "BiCl3", "BiF3", "HfO2", "SiO2", "SnCl2", "Tl2SnCl6"],
    *["Tl2TiF6", "Tl2SnF6", "TlF"],
    # commercial dielectrics https://rdcu.be/cClNr
    *["ZrO2", "Al2O3", "Y2O3", "SrTiO", "BaTiO3"],
]

# mp-557118 seems like a DFPT calc gone wrong (https://matsci.org/t/40913)
df_petousis = (
    df_diel_mp.query("formula in @known_diels & material_id != 'mp-557118'")
    .sort_values("fom_mp")  # only plot highest FoM polymorph for each formula
    .drop_duplicates("formula", keep="last")
)
petousis_mp = scatter(
    df_petousis,
    x_col="diel_total_mp",
    y_col=bandgap_mp_col,
    legend_name=f"{len(df_petousis):,} Best Petousis 2017 Candidates (MP data)",
)
petousis_mp.update_traces(marker=dict(size=15, symbol="star", color="teal"))
petousis_mp.data[0]["visible"] = True
fig.add_traces(data=petousis_mp.data)

n_top_fom = 200
best_fom_mp = scatter(
    df_diel_mp.query("index not in @df_petousis.index").nlargest(200, "fom_mp"),
    x_col="diel_total_mp",
    y_col=bandgap_mp_col,
    legend_name=f"Top {n_top_fom:,} MP Training Points",
)
fig.add_traces(data=best_fom_mp.data)


qz3_points = scatter(
    df_qz3,
    x_col="diel_total_pbe",
    y_col="bandgap_pbe",
    legend_name=f"{len(df_qz3):,} Qu et al. 2020 Ternary Oxides",
)
fig.add_traces(data=qz3_points.data)

selected_for_synth_points = scatter(
    df_synth := df_all.query(
        f"selection_status == '{SelectionStatus.selected_for_synthesis}'"
    ),
    x_col="diel_total_pbe",
    y_col=bandgap_us_col,
    legend_name=f"{len(df_synth):,} Selected for synthesis",
    annotate_min_fom=0,
)
selected_for_synth_points.update_traces(
    marker=dict(size=15, symbol="cross", color="gold")
)
selected_for_synth_points.data[0]["visible"] = True
fig.add_traces(data=selected_for_synth_points.data)

# reassign df_all to exclude synth selected from all other groups
df_unselected = df_all.query(
    f"selection_status != '{SelectionStatus.selected_for_synthesis}'"
)

df_our_best = df_unselected.query(
    "e_above_hull_pbe < 0.1 & fom_pbe > 200 & nelements == 3"
)

scatter_with_quiver(
    df_best_elemsub := df_unselected.query('material_id.str.contains("->")')
    .query("e_above_hull_pbe < 0.1")
    .nlargest(top_n := 100, "fom_pbe"),
    scatter_1=dict(x="diel_total_wren", y=bandgap_us_col),
    # make VASP scatter points visible by default
    scatter_2=dict(x="diel_total_pbe", y=bandgap_us_col, visible=True),
    legend_labels=(
        f"Top {top_n} elemental substitution structures",
        f"Wren mean FoM = {df_best_elemsub.fom_wren.mean():.0f}",
        f"VASP mean FoM = {df_best_elemsub.fom_pbe.mean():.0f}",
    ),
)
# get the VASP mean FoM trace
trace = next(t for t in fig.data if t.name.startswith("VASP mean FoM"))
trace["marker"]["color"] = "rgba(0, 100, 255, 0.8)"

airss_points = scatter(
    df_airss := df_unselected.query('material_id.str.startswith("airss")'),
    x_col="diel_total_pbe",
    y_col=bandgap_us_col,
    legend_name=f"{len(df_airss):,} AIRSS structures mean FoM = "
    f"{df_airss.fom_pbe.mean():.0f}",
)
fig.add_traces(data=airss_points.data)

scatter_with_quiver(
    df_our_best,
    scatter_1=dict(x="diel_total_wren", y=bandgap_us_col),
    scatter_2=dict(x="diel_total_pbe", y=bandgap_us_col),
    legend_labels=(
        "Best from all Series",
        f"Wren mean FoM = {df_our_best.fom_wren.mean():.0f}",
        f"VASP mean FoM = {df_our_best.fom_pbe.mean():.0f}",
    ),
    lax_nan=True,
)


scatter_with_quiver(
    df_2022 := df_unselected.query(
        "completed_at > '2022-01-01' & e_above_hull_pbe < 0.1"
    ),
    scatter_1=dict(x="diel_total_wren", y=bandgap_us_col),
    scatter_2=dict(x="diel_total_pbe", y=bandgap_us_col),
    legend_labels=(
        "2022 calcs < 0.1 eV above hull",
        f"Wren mean FoM = {df_2022.fom_wren.mean():.0f}",
        f"VASP mean FoM = {df_2022.fom_pbe.mean():.0f}",
    ),
    lax_nan=True,
)

scatter_with_quiver(
    df_yim,
    scatter_1=dict(x=diel_total_pbe_col, y="bandgap_pbe"),
    scatter_2=dict(x=diel_total_pbe_col, y="bandgap_hse"),
    legend_labels=(
        "Yim et al. 2015",
        f"GGA mean FoM = {df_yim.fom_pbe.mean():.0f}",
        f"HSE mean FoM = {df_yim.fom_hse.mean():.0f}",
    ),
)


# contour: figure of merit surface
fom_contour = np.outer(np.arange(20), np.arange(2000))

fig.add_contour(
    z=fom_contour,
    hoverinfo="skip",
    name="FoM Contour",
    showlegend=True,
    line_width=2,
    contours_coloring="lines",
    contours=dict(
        showlabels=True,
        labelfont=dict(size=12, color="gray"),
        start=100,
        end=3000,
        size=200,
    ),
    showscale=False,  # remove color bar
)

# set mirror + showline to True to outline plot area on top and right
fig.update_xaxes(range=[0, 500], mirror=True, showline=True)
fig.update_yaxes(range=[0, 7], mirror=True, showline=True)


fig.layout.margin = dict(l=80, r=30, t=80, b=60)
bgcolor = "rgba(255, 255, 255, 0.8)"  # dark: rgba(0, 0, 0, 0.4)
fig.layout.legend = dict(
    x=1, y=1, xanchor="right", yanchor="top", bgcolor=bgcolor, groupclick="toggleitem"
)
fig.layout.height = 1200
fig.layout.width = 1200
fig.layout.title = (
    f"<b>Pareto Front of Dielectric Constant and Band Gap</b> - data as of {today}"
)
fig.layout.xaxis.title = "Total dielectric constant"
fig.layout.yaxis.title = "Band gap / eV"
fig.layout.legend_groupclick = "toggleitem"
legend_toggle = dict(
    args=["showlegend", True],
    args2=["showlegend", False],
    label="Toggle legend",
    method="relayout",
)
fig.layout.updatemenus = [
    dict(type="buttons", buttons=[legend_toggle], showactive=True)
]

# draw ellipses indicating regions of desirable material properties for widely used
# electronic devices
for xs, ys, clr, txt in [
    [(230, 430), (1.5, 3.5), "rgba(0, 0, 255, 0.6)", "RAM"],
    [(120, 320), (2.8, 4.8), "rgba(0, 255, 0, 0.6)", "CPU"],
    [(70, 250), (4.5, 6.5), "rgba(255, 0, 0, 0.6)", "Flash storage"],
]:
    fig.add_shape(
        type="circle",
        **dict(x0=xs[0], x1=xs[1], y0=ys[0], y1=ys[1]),
        line=dict(width=2, dash="dot", color=clr),
    )
    fig.add_annotation(
        text=f"<b>{txt}</b>",
        font=dict(color=clr, size=15),
        x=sum(xs) / 2,  # type: ignore
        y=sum(ys) / 2,  # type: ignore
        showarrow=False,
    )


fig.write_html(f"{module_dir}/pareto-plotly.html", include_plotlyjs="cdn")
# fig.write_image(f"{module_dir}/pareto-plotly.pdf")
fig.show()


# %%
app = Dash(prevent_initial_callbacks=True, assets_folder=CTK_SETTINGS.ASSETS_PATH)
app.title = "Dielectric Pareto Front"  # browser tab title

graph = dcc.Graph(
    id="pareto-plot",
    figure=fig,
    responsive=True,
    style=dict(
        # height="min(800px, 60vw)",
        maxHeight="90vh",
        maxWidth="1200px",
        width="100%",
        aspectRatio="1.5",
    ),
)
textarea = dcc.Textarea(
    id="textarea",
    style=dict(
        width="clamp(20vw, 300px, 500px)",
        minHeight="20vw",
        padding="1ex 1em",
    ),
    placeholder="Start writing notes...",
)
save_btn = html.Button("Save", id="save-button")
span = html.Span(id="status", style={"color": "green"})

status_dd = dcc.Dropdown(
    id="status-dropdown",
    options=[dict(label=stat, value=stat) for stat in SelectionStatus],
    style=dict(display="inline-block", width="15em", lineHeight="0em"),
    placeholder="Selection status",
)

h1 = html.H1(
    app.title,
    id="selected-info",
    style=dict(textAlign="center", margin="2em 0 1em", fontSize=24, fontWeight="bold"),
)

flex_css = dict(display="flex", gap="1em", margin="1em auto", placeContent="center")

control_div = html.Div(
    [status_dd, save_btn, span],
    style=dict(**flex_css, placeItems="center"),
)
structure_component = ctc.StructureMoleculeComponent(id="structure")


side_components_style = dict(
    display="flex", flexDirection="column", gap="1em", alignItems="center"
)
main_layout = html.Main(
    [
        html.Div([control_div, textarea], style=side_components_style),
        graph,
        html.Div(
            [structure_component.layout(size="clamp(30vw, 400px, 800px)")],
            style=side_components_style,
        ),
    ],
    style=dict(
        display="flex",
        justifyContent="center",
        alignItems="center",
        gap="1em",
        margin="0 2em 2em",
    ),
)

app.layout = html.Div([h1, main_layout])
ctc.register_crystal_toolkit(app=app, layout=app.layout)


@app.callback(
    Output(textarea, "value"),
    Output(status_dd, "value"),
    Output(h1, "children"),
    Input(graph, "clickData"),
)
def fetch_notes(click_data: dict[str, list[dict[str, Any]]]) -> tuple[str, str, str]:
    """Fetch notes and selection status from Mongo database for selected material."""
    try:
        # get Mongo ObjectID from clickData
        mongo_id = ObjectId(click_data["points"][0]["customdata"][0])
    except (InvalidId, TypeError):
        return "", "", ""

    fields = ["notes", "selection_status", "formula_pretty", id_col]
    doc: dict[str, str] = db.tasks.find_one({"_id": mongo_id}, fields) or {}
    notes, status, formula, mat_id = (doc.get(key, "") for key in fields)
    return notes, status, f"{formula} ({mat_id})".replace("->", "→")


@app.callback(
    Output(span, "children"),
    Input(save_btn, "n_clicks"),
    Input(textarea, "value"),
    Input(graph, "clickData"),
    Input(status_dd, "value"),
)
def update_notes(
    n_clicks: int,  # unused but needed so the callback triggers on button click
    notes: str,
    click_data: dict[str, list[dict[str, Any]]],
    status_value: str = "",
) -> str | None:
    """Update MongoDB task collection entry with notes and selection status entered via
    dcc.Textarea and dcc.sDropdown resp.
    """
    context = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    # if callback was triggered by click on graph and not on save_btn click,
    # ignore it
    if context != save_btn.id:
        return None

    data = click_data["points"][0]
    mongo_id = ObjectId(data.get("customdata", ["missing _id"])[0])

    try:
        payload = {"notes": notes}
        if status_value:
            payload[selection_status_col] = status_value
        db.tasks.update_one({"_id": mongo_id}, {"$set": payload})
    except Exception as err:
        print(f"{err=}")
        return f"{err}"

    return "saved"


@app.callback(Output(structure_component.id(), "data"), Input(graph, "clickData"))
def update_structure(
    click_data: dict[str, list[dict[str, Any]]],
) -> Structure | None:
    """Update StructureMoleculeComponent with pymatgen structure from MongoDB task
    collection when user clicks on new scatter point.
    """
    data = click_data["points"][0]
    _id = data.get("customdata", ["missing _id"])[0]

    try:
        if _id.startswith("mp"):
            from pymatgen.ext.matproj import MPRester

            structure = MPRester().get_structure_by_material_id(_id)
        else:
            dct = db.tasks.find_one({"_id": ObjectId(_id)}, ["output.structure"]) or {}
            structure = dct["output"]["structure"]
    except Exception as err:
        # if we can't fetch a structure in try block, print error and return None to
        # empty scene
        print(f"{err=}")
        return None

    return structure


app.run(debug=False, port=8000, jupyter_mode="external")
