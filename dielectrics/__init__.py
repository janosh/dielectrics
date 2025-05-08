import os
from datetime import datetime, timezone
from enum import StrEnum, unique
from typing import TYPE_CHECKING

import plotly.express as px
import pymatviz as pmv
from matplotlib import pyplot as plt


if TYPE_CHECKING:

    class Key(StrEnum, pmv.enums.LabelEnum):
        """This is here for mypy's benefit since it doesn't infer Key attributes
        as strings otherwise.
        """


PKG_DIR = os.path.dirname(__file__)
ROOT = os.path.dirname(PKG_DIR)
PAPER_FIGS = f"{ROOT}/paper/figs"
DATA_DIR = f"{ROOT}/data"
SCRIPTS_DIR = f"{ROOT}/scripts"
today = f"{datetime.now(tz=timezone.utc):%Y-%m-%d}"

pmv.set_plotly_template("pymatviz_white")
plt.rcParams["figure.constrained_layout.use"] = True


@unique
class Key(pmv.enums.LabelEnum):  # type: ignore[no-redef]
    """Dataframe column names."""

    bandgap = "bandgap", "Band gap"
    bandgap_exp = "bandgap_exp", "Band gap (exp.)"
    bandgap_hse = "bandgap_hse", "Band gap (HSE)"
    bandgap_mp = "bandgap_mp", "Band gap (MP)"
    bandgap_pbe = "bandgap_pbe", "Band gap (PBE)"
    bandgap_us = "bandgap_us", "Band gap (us)"
    bandgap_wren = "bandgap_wren", "Band gap (Wren)"
    crystal_sys = "crystal_system", "Crystal system"
    date = "date", "Date"
    diel_elec_mp = "diel_elec_mp", "ε<sub>elec MP</sub>"
    diel_elec_pbe = "diel_elec_pbe", "ε<sub>elec PBE</sub>"
    diel_elec_wren = "diel_elec_wren", "ε<sub>elec Wren</sub>"
    diel_ionic_mp = "diel_ionic_mp", "ε<sub>ionic MP</sub>"
    diel_ionic_pbe = "diel_ionic_pbe", "ε<sub>ionic PBE</sub>"
    diel_ionic_wren = "diel_ionic_wren", "ε<sub>ionic Wren</sub>"
    diel_total = (
        "diel_total",
        "ε<sub>total</sub>",
        "total dielectric constant from experiment",
    )
    diel_total_exp = "diel_total_exp", "ε<sub>total exp.</sub>"
    diel_total_mp = (
        "diel_total_mp",
        "ε<sub>total MP</sub>",
        "total dielectric constant from MP",
    )
    diel_total_pbe = (
        "diel_total_pbe",
        "ε<sub>total PBE</sub>",
        "total dielectric constant from PBE DFPT calcs",
    )
    diel_total_us = (
        "diel_total_us",
        "ε<sub>total us</sub>",
        "total dielectric constant from our own DFPT calcs",
    )
    diel_total_wren = (
        "diel_total_wren",
        "ε<sub>total Wren</sub>",
        "total dielectric constant from Wren DFPT calcs",
    )
    dyn_mat_eigen_vals = (
        "dynamical_matrix_eigen_vals",
        "Dynamical matrix eigenvals",
        "eigenvalues of the dynamical matrix",
    )  # atomate: normalmode_eigenvals
    dyn_mat_eigen_vecs = (
        "dynamical_matrix_eigen_vecs",
        "Dynamical matrix eigenvecs",
        "eigenvectors of the dynamical matrix",
    )  # atomate: normalmode_eigenvecs
    e_above_hull_mp = "e_above_hull_mp", "E<sub>hull dist MP</sub>"
    e_above_hull_pbe = "e_above_hull_pbe", "E<sub>hull dist PBE</sub>"
    e_above_hull_wren = "e_above_hull_wren", "E<sub>hull dist Wren</sub>"
    e_form_wren = "e_form_wren", "E<sub>form Wren</sub>"
    e_per_atom = "energy_per_atom", "Energy per atom"
    energy = "energy (eV)", "Energy"
    fom = "fom", "Φ", "figure of merit Phi_M = band gap x eps_total"
    fom_exp = "fom_exp", "Φ<sub>exp</sub>"
    fom_mp = "fom_mp", "Φ<sub>MP</sub>"
    fom_pbe = "fom_pbe", "Φ<sub>PBE</sub>"
    fom_wren = "fom_wren", "Φ<sub>Wren</sub>"
    fom_wren_std_adj = "fom_wren_std_adj", "Φ<sub>Wren - std</sub>"
    force_constants = "force_constants", "Force constants"
    formula = "formula", "Formula"
    fr_min_e = "(F(R)-E)^1/2", "(F(R) - E)<sup>1/2</sup>"
    freq = (
        "Frequency (Hz)",
        "Frequency",
        "frequency of electric field in exp. impedance/reflectance plots",
    )
    icsd_id = "icsd_id", "ICSD ID"
    imped = "Impedance (Ohms)", "Impedance"
    mat_id = "material_id", "Material ID"
    max_ph_freq = "max_phonon_frequency", "Max phonon frequency"
    min_ph_freq = "min_phonon_frequency", "Min phonon frequency"
    n_sites = "n_sites", "Number of sites", "number of sites in the unit cell"
    phonon_freqs = "phonon_frequencies", "Phonon frequencies"
    selection_status = (
        "selection_status",
        "Selection status",
        "synthesis selection status of candidate materials",
    )
    spg = "spacegroup", "Space group", "international space group number"
    structure = "structure", "Structure"
    symmetry = "symmetry", "Symmetry"
    task_id = "task_id", "Task ID"
    wyckoff = "wyckoff", "Wyckoff position"


ev_per_atom = pmv.utils.html_tag("(eV/atom)", tag="span", style="small")
eV = pmv.utils.html_tag("(eV)", tag="span", style="small")  # noqa: N816

px.defaults.labels |= {
    Key.bandgap_hse: f"E<sub>gap HSE</sub> {eV}",
    Key.bandgap_mp: f"E<sub>gap MP</sub> {eV}",
    Key.bandgap_pbe: f"E<sub>gap PBE</sub> {eV}",
    Key.bandgap_us: f"E<sub>gap us</sub> {eV}",
    Key.bandgap_wren: f"E<sub>gap Wren</sub> {eV}",
    Key.crystal_sys: "Crystal system",
    Key.date: "Date",
    Key.diel_elec_pbe: "ε<sub>elec</sub>",
    Key.diel_elec_mp: "ε<sub>elec MP</sub>",
    Key.diel_elec_wren: "ε<sub>elec Wren</sub>",
    Key.diel_ionic_pbe: "ε<sub>ionic</sub>",
    Key.diel_ionic_mp: "ε<sub>ionic MP</sub>",
    Key.diel_ionic_wren: "ε<sub>ionic Wren</sub>",
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


class SelectionStatus(pmv.enums.LabelEnum):
    """Enum for synthesis selection status of candidate materials."""

    # according to literature mention
    confirmed = "confirmed dielectric", "Confirmed dielectric"
    discarded = "discarded", "Discarded"
    # promising candidate for exp. synthesis
    strong_candidate = "strong candidate", "Strong candidate"
    weak_candidate = "weak candidate", "Weak candidate"
    # to be synthesized if time/resources allow
    selected_for_synthesis = "selected for synthesis", "Selected for synthesis"
