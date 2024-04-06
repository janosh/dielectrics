import os
from datetime import datetime
from enum import StrEnum, unique

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


@unique
class PlotlyHoverData(StrEnum):
    """Frequently used dataframe column names."""

    bandgap_hse = "bandgap_hse"
    bandgap_mp = "bandgap_mp"
    bandgap_pbe = "bandgap_pbe"
    bandgap_us = "bandgap_us"
    bandgap_wren = "bandgap_wren"
    date = "date"
    diel_total = "diel_total"
    diel_total_mp = "diel_total_mp"  # total dielectric constant from MP
    diel_total_pbe = "diel_total_pbe"  # total dielectric constant from PBE DFPT calcs
    diel_total_wren = "diel_total_wren"
    e_above_hull_mp = "e_above_hull_mp"
    e_above_hull_pbe = "e_above_hull_pbe"
    e_above_hull_wren = "e_above_hull_wren"
    fom_pbe = "fom_pbe"
    fom_wren = "fom_wren"
    fom_wren_std_adj = "fom_wren_std_adj"
    formula = "formula"
    selection_status = "selection_status"
    symmetry = "symmetry"


@unique
class Key(StrEnum):
    """Dataframe column names."""

    crystal_sys = "crystal_system"
    diel_elec_mp = "diel_elec_mp"
    diel_elec_pbe = "diel_elec_pbe"
    diel_elec_wren = "diel_elec_wren"
    diel_ionic_mp = "diel_ionic_mp"
    diel_ionic_pbe = "diel_ionic_pbe"
    diel_ionic_wren = "diel_ionic_wren"
    diel_total_exp = "diel_total_exp"  # total dielectric constant from experiment
    diel_total_us = "diel_total_us"  # total dielectric constant from our own DFPT calcs
    e_per_atom = "energy_per_atom"
    energy = "energy (eV)"
    fom = "fom"
    fom_exp = "fom_exp"
    fr_min_e = "(F(R)-E)^1/2"
    freq = "Frequency (Hz)"
    icsd_id = "icsd_id"
    imped = "Impedance (Ohms)"
    mat_id = "material_id"
    n_sites = "n_sites"
    spg = "spacegroup"  # space group number
    structure = "structure"

    # add all PlotlyHoverData (duplication seems unavoidable since Enum can't be
    # subclassed https://stackoverflow.com/q/33679930)
    bandgap = "bandgap"
    bandgap_hse = "bandgap_hse"
    bandgap_mp = "bandgap_mp"
    bandgap_pbe = "bandgap_pbe"
    bandgap_us = "bandgap_us"
    bandgap_wren = "bandgap_wren"
    date = "date"
    diel_total = "diel_total"
    diel_total_mp = "diel_total_mp"  # total dielectric constant from MP
    diel_total_pbe = "diel_total_pbe"  # total dielectric constant from PBE DFPT calcs
    diel_total_wren = "diel_total_wren"
    e_above_hull_mp = "e_above_hull_mp"
    e_above_hull_pbe = "e_above_hull_pbe"
    e_above_hull_wren = "e_above_hull_wren"
    fom_pbe = "fom_pbe"
    fom_wren = "fom_wren"
    fom_wren_std_adj = "fom_wren_std_adj"
    formula = "formula"
    phonon_freqs = "phonon_frequencies"
    min_ph_freq = "min_phonon_frequency"
    max_ph_freq = "max_phonon_frequency"
    selection_status = "selection_status"
    symmetry = "symmetry"
    task_id = "task_id"
    wyckoff = "wyckoff"


small_font = "font-size: 0.9em; font-weight: lighter;"
ev_per_atom = styled_html_tag("(eV/atom)", tag="span", style=small_font)
eV = styled_html_tag("(eV)", tag="span", style=small_font)  # noqa: N816

px.defaults.labels = {
    Key.bandgap_hse: f"E<sub>gap HSE</sub> {eV}",
    Key.bandgap_mp: f"E<sub>gap MP</sub> {eV}",
    Key.bandgap_pbe: f"E<sub>gap PBE</sub> {eV}",
    Key.bandgap_us: f"E<sub>gap us</sub> {eV}",
    Key.bandgap_wren: f"E<sub>gap Wren</sub> {eV}",
    Key.crystal_sys: "Crystal system",
    Key.date: "Date",
    Key.diel_elec_mp: "ε<sub>elec MP</sub>",
    Key.diel_elec_pbe: "ε<sub>elec</sub>",
    Key.diel_ionic_pbe: "ε<sub>ionic</sub>",
    Key.diel_ionic_mp: "ε<sub>ionic MP</sub>",
    Key.diel_total: "ε<sub>total</sub>",
    Key.diel_total_mp: "ε<sub>total MP</sub>",
    Key.diel_total_pbe: "ε<sub>total PBE</sub>",
    Key.diel_total_us: "ε<sub>total us</sub>",
    Key.diel_total_wren: "ε<sub>total Wren</sub>",
    Key.e_above_hull_mp: f"E<sub>hull dist MP</sub> {ev_per_atom}",
    Key.e_above_hull_pbe: f"E<sub>hull dist PBE</sub> {ev_per_atom}",
    Key.e_above_hull_wren: f"E<sub>hull dist Wren</sub> {ev_per_atom}",
    Key.e_per_atom: f"energy {ev_per_atom}",  # usually PBE energy
    Key.fom: "Φ",
    Key.fom_pbe: "Φ<sub>PBE</sub>",  # figure of merit from PBE band gap and eps_total
    Key.fom_wren: "Φ<sub>Wren</sub>",
    Key.fom_wren_std_adj: "Φ<sub>Wren - std</sub>",
    Key.formula: "Formula",
    Key.freq: "Frequency (Hz)",  # electric field in impedance/Keys.reflectance plots
    Key.mat_id: "Material ID",
    Key.imped: "Impedance (Ohms)",
    Key.spg: "Space group",
    Key.structure: "Structure",
    Key.symmetry: "Symmetry",
    Key.selection_status: "Selection status",
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
