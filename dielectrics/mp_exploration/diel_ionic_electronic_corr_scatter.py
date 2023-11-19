# %%
import pandas as pd
import plotly.express as px
from matplotlib.offsetbox import AnchoredText
from pymatviz.io import save_fig
from sklearn.metrics import r2_score

from dielectrics import PAPER_FIGS, bandgap_mp_col
from dielectrics.plots import plt


# %%
df_diel_mp = pd.read_json("data/mp-diel-train.json.bz2")

df_diel_mp = df_diel_mp.query("0 < diel_total_mp < 2000")

ax_title = f"MP dielectric constants ({len(df_diel_mp):,})"


# %% no correlation between electronic and ionic dielectric constants
x_col, y_col = "diel_ionic_mp", "diel_elec_mp"
color_map = "viridis"
ax = (
    df_diel_mp.sort_values(by=bandgap_mp_col).plot.scatter(
        x=x_col, y=y_col, c=bandgap_mp_col, alpha=0.5, cmap=color_map
    )
    # for smaller file size can also plot as hexbin but looses color for band gap info
    # .plot.hexbin(x=x_col, y=y_col, cmap=cmap, yscale="log", xscale="log", mincnt=1)
)

ax.set(yscale="log", xscale="log", xlim=[0.1, None])
ax.set(xlabel=r"$\epsilon_\mathrm{ionic}$", ylabel=r"$\epsilon_\mathrm{electronic}$")
ax.axline([10, 10], [11, 11], c="black", linestyle="dashed", alpha=0.5, zorder=0)
cbar_ax = plt.gcf().get_axes()[-1]
cbar_ax.set_ylabel(r"$E_\mathrm{gap}$")

R2 = r2_score(df_diel_mp[x_col], df_diel_mp[y_col])
text_box = AnchoredText(f"$R^2 = {R2:.2f}$", loc="lower right", frameon=False)
ax.add_artist(text_box)

ax.set_title(ax_title, fontsize=15)

# path_ionic_electronic_corr = f"{PAPER_FIGS}/diel-ionic-vs-electronic-corr-mp.pdf"
# plt.savefig(path_ionic_electronic_corr)


# %% same plot but with plotly
fig = px.scatter(
    df_diel_mp.query(f"1 < {x_col} < 2000").sort_values(by=bandgap_mp_col),
    x=x_col,
    y=y_col,
    color=bandgap_mp_col,  # This automatically creates a color bar
    log_x=True,  # Set x-axis to log scale
    log_y=True,  # Set y-axis to log scale
    color_continuous_scale=color_map,  # Set the colormap to 'viridis'
    opacity=0.5,
)

R2 = r2_score(df_diel_mp[x_col], df_diel_mp[y_col])
fig.add_annotation(
    x=0.95,
    y=0.05,
    xref="paper",
    yref="paper",
    text=f"R<sup>2</sup> = {R2:.2f}",
    showarrow=False,
    font=dict(size=16),
)
fig.layout.coloraxis.colorbar = dict(
    orientation="h", x=0.85, y=0.98, yanchor="top", len=0.3, thickness=12
)
fig.layout.coloraxis.colorbar.title = dict(  # type: ignore[attr-defined]
    text="E<sub>gap</sub>&nbsp;", font=dict(size=16)
)

axes_kwds = dict(
    dtick=1, showline=True, linewidth=1, mirror=True, title_font=dict(size=18)
)
fig.layout.xaxis.update(**axes_kwds)
fig.layout.yaxis.update(**axes_kwds)
fig.layout.margin = dict(t=40, l=10, r=10, b=10)
fig.layout.title = dict(text=ax_title, x=0.5)

fig.show()
save_fig(fig, f"{PAPER_FIGS}/diel-ionic-vs-electronic-corr-mp.pdf")
