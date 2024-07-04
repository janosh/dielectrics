import os
from datetime import datetime, timezone
from enum import unique

import plotly.express as px
from matplotlib import pyplot as plt
from pymatviz import set_plotly_template
from pymatviz.enums import LabelEnum
from pymatviz.utils import styled_html_tag


PKG_DIR = os.path.dirname(__file__)
ROOT = os.path.dirname(PKG_DIR)
PAPER_FIGS = f"{ROOT}/paper/figs"
DATA_DIR = f"{ROOT}/data"
SCRIPTS_DIR = f"{ROOT}/scripts"
today = f"{datetime.now(tz=timezone.utc):%Y-%m-%d}"

set_plotly_template("pymatviz_white")
plt.rcParams["figure.constrained_layout.use"] = True


@unique
class Key(LabelEnum):
    """Dataframe column names."""

    bandgap = "bandgap"
    bandgap_exp = "bandgap_exp"
    bandgap_hse = "bandgap_hse"
    bandgap_mp = "bandgap_mp"
    bandgap_pbe = "bandgap_pbe"
    bandgap_us = "bandgap_us"
    bandgap_wren = "bandgap_wren"
    crystal_sys = "crystal_system"
    date = "date"
    diel_elec_mp = "diel_elec_mp"
    diel_elec_pbe = "diel_elec_pbe"
    diel_elec_wren = "diel_elec_wren"
    diel_ionic_mp = "diel_ionic_mp"
    diel_ionic_pbe = "diel_ionic_pbe"
    diel_ionic_wren = "diel_ionic_wren"
    diel_total = "diel_total"
    diel_total_exp = "diel_total_exp"  # total dielectric constant from experiment
    diel_total_mp = "diel_total_mp"  # total dielectric constant from MP
    diel_total_pbe = "diel_total_pbe"  # total dielectric constant from PBE DFPT calcs
    diel_total_us = "diel_total_us"  # total dielectric constant from our own DFPT calcs
    diel_total_wren = "diel_total_wren"
    dyn_mat_eigen_vals = "dynamical_matrix_eigen_vals"  # atomate: normalmode_eigenvals
    dyn_mat_eigen_vecs = "dynamical_matrix_eigen_vecs"  # atomate: normalmode_eigenvecs
    e_above_hull_mp = "e_above_hull_mp"
    e_above_hull_pbe = "e_above_hull_pbe"
    e_above_hull_wren = "e_above_hull_wren"
    e_form_wren = "e_form_wren"
    e_per_atom = "energy_per_atom"
    energy = "energy (eV)"
    fom = "fom"  # figure of merit Phi_M = band gap x eps_total
    fom_exp = "fom_exp"
    fom_mp = "fom_mp"
    fom_pbe = "fom_pbe"
    fom_wren = "fom_wren"
    fom_wren_std_adj = "fom_wren_std_adj"
    force_constants = "force_constants"
    formula = "formula"
    fr_min_e = "(F(R)-E)^1/2"
    freq = "Frequency (Hz)"  # of electric field in exp. impedance/reflectance plots
    icsd_id = "icsd_id"
    imped = "Impedance (Ohms)"
    mat_id = "material_id"
    max_ph_freq = "max_phonon_frequency"
    min_ph_freq = "min_phonon_frequency"
    n_sites = "n_sites"  # number of sites in the unit cell
    phonon_freqs = "phonon_frequencies"
    # synthesis selection status of candidate materials
    selection_status = "selection_status"
    spg = "spacegroup"  # international space group number
    structure = "structure"
    symmetry = "symmetry"
    task_id = "task_id"
    wyckoff = "wyckoff"


small_font = "font-size: 0.9em; font-weight: lighter;"
ev_per_atom = styled_html_tag("(eV/atom)", tag="span", style=small_font)
eV = styled_html_tag("(eV)", tag="span", style=small_font)  # noqa: N816

px.defaults.labels |= {
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
    Key.freq: "Frequency (Hz)",  # of electric field in exp. impedance/reflectance plots
    Key.mat_id: "Material ID",
    Key.spg: "Space group",
    Key.structure: "Structure",
    Key.symmetry: "Symmetry",
    Key.selection_status: "Selection status",
}


class SelectionStatus(LabelEnum):
    """Enum for synthesis selection status of candidate materials."""

    confirmed = "confirmed dielectric"  # according to literature mention
    discarded = "discarded"
    strong_candidate = "strong candidate"  # promising candidate for exp. synthesis
    weak_candidate = "weak candidate"
    # to be synthesized if time/resources allow
    selected_for_synthesis = "selected for synthesis"
