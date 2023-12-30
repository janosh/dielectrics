import os
from datetime import datetime
from enum import StrEnum

import plotly.express as px
from matplotlib import pyplot as plt
from plotly import io as pio
from pymatviz.utils import styled_html_tag


PKG_DIR = os.path.dirname(__file__)
ROOT = os.path.dirname(PKG_DIR)
PAPER_FIGS = f"{ROOT}/paper/figs"
DATA_DIR = f"{ROOT}/data"
SCRIPTS_DIR = f"{ROOT}/scripts"
today = f"{datetime.now():%Y-%m-%d}"


plt.rcParams["figure.constrained_layout.use"] = True

# frequently used dataframe column names
plotly_hover_cols = {
    bandgap_hse_col := "bandgap_hse",
    bandgap_mp_col := "bandgap_mp",
    bandgap_pbe_col := "bandgap_pbe",
    bandgap_us_col := "bandgap_us",
    bandgap_wren_col := "bandgap_wren",
    date_col := "date",
    diel_total_col := "diel_total",
    diel_total_mp_col := "diel_total_mp",
    # total dielectric constant from PBE DFPT calcs
    diel_total_pbe_col := "diel_total_pbe",
    diel_total_wren_col := "diel_total_wren",
    e_above_hull_mp_col := "e_above_hull_mp",
    e_above_hull_pbe_col := "e_above_hull_pbe",
    e_above_hull_wren_col := "e_above_hull_wren",
    fom_pbe_col := "fom_pbe",
    fom_wren_col := "fom_wren",
    fom_wren_std_adj_col := "fom_wren_std_adj",
    formula_col := "formula",
    symmetry_col := "symmetry",
    selection_status_col := "selection_status",
}
crystal_sys_col = "crystal_system"
diel_elec_mp_col = "diel_elec_mp"
diel_elec_pbe_col = "diel_elec_pbe"
diel_total_exp_col = "diel_total_exp"  # total dielectric constant from experiment
diel_ionic_mp_col = "diel_ionic_mp"
diel_ionic_pbe_col = "diel_ionic_pbe"
diel_total_mp_col = "diel_total_mp"  # total dielectric constant from MP
diel_total_us_col = "diel_total_us"  # total dielectric constant from our own DFPT calcs
e_per_atom_col = "energy_per_atom"
energy_col = "energy (eV)"
energy_per_atom_col = "energy_per_atom"
fom_col = "fom"
fom_exp_col = "fom_exp"
fr_min_e_col = "(F(R)-E)^1/2"
freq_col = "frequency (Hz)"
icsd_id_col = "icsd_id"
id_col = "material_id"
imped_col = "Impedance (Ohms)"
n_sites_col = "n_sites"
spg_col = "spacegroup"  # space group number
structure_col = "structure"

small_font = "font-size: 0.9em; font-weight: lighter;"
ev_per_atom = styled_html_tag("(eV/atom)", tag="span", style=small_font)
eV = styled_html_tag("(eV)", tag="span", style=small_font)

px.defaults.labels = {
    bandgap_hse_col: f"E<sub>gap HSE</sub> {eV}",
    bandgap_mp_col: f"E<sub>gap MP</sub> {eV}",
    bandgap_pbe_col: f"E<sub>gap PBE</sub> {eV}",
    bandgap_us_col: f"E<sub>gap us</sub> {eV}",
    bandgap_wren_col: f"E<sub>gap Wren</sub> {eV}",
    crystal_sys_col: "Crystal system",
    date_col: "Date",
    diel_elec_mp_col: "ε<sub>elec MP</sub>",
    diel_elec_pbe_col: "ε<sub>elec</sub>",
    diel_ionic_pbe_col: "ε<sub>ionic</sub>",
    diel_ionic_mp_col: "ε<sub>ionic MP</sub>",
    diel_total_col: "ε<sub>total</sub>",
    diel_total_mp_col: "ε<sub>total MP</sub>",
    diel_total_pbe_col: "ε<sub>total PBE</sub>",
    diel_total_us_col: "ε<sub>total us</sub>",
    diel_total_wren_col: "ε<sub>total Wren</sub>",
    e_above_hull_mp_col: f"E<sub>hull dist MP</sub> {ev_per_atom}",
    e_above_hull_pbe_col: f"E<sub>hull dist PBE</sub> {ev_per_atom}",
    e_above_hull_wren_col: f"E<sub>hull dist Wren</sub> {ev_per_atom}",
    e_per_atom_col: f"energy {ev_per_atom}",  # usually PBE energy
    fom_col: "Φ",
    fom_pbe_col: "Φ<sub>PBE</sub>",  # figure of merit from PBE band gap and eps_total
    fom_wren_col: "Φ<sub>Wren</sub>",
    fom_wren_std_adj_col: "Φ<sub>Wren - std</sub>",
    formula_col: "Formula",
    freq_col: "Frequency (Hz)",  # electric field in impedance/reflectance plots
    id_col: "Material ID",
    imped_col: "Impedance (Ohms)",
    spg_col: "Space group",
    structure_col: "Structure",
    symmetry_col: "Symmetry",
    selection_status_col: "Selection status",
}

px.defaults.template = "plotly_white"
pio.templates.default = "plotly_white"
axis_template = dict(
    mirror=True,
    showline=True,
    ticks="outside",
    zeroline=True,
    linewidth=1,
    linecolor="black",
    gridcolor="lightgray",
)
pio.templates["plotly_white"].update(
    layout=dict(xaxis=axis_template, yaxis=axis_template)
)


class SelectionStatus(StrEnum):
    """Enum for synthesis selection status of candidate materials."""

    confirmed = "confirmed dielectric"
    discarded = "discarded"
    strong_candidate = "strong candidate"
    weak_candidate = "weak candidate"
    selected_for_synthesis = "selected for synthesis"
