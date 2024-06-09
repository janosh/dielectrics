import matplotlib.pyplot as plt
import plotly.express as px
import plotly.io as pio
from pymatviz import pmv_dark_template


px.defaults.labels |= dict(
    n_atoms="Atom Count",
    n_elems="Element Count",
    crystal_sys="Crystal system",
    n="Refractive index n",
    spg_num="Space group number",
    n_sites="Number of unit cell sites",
    energy_per_atom="Energy (eV/atom)",
    e_above_hull_pbe="PBE hull distance (eV)",
    diel_total="Total dielectric constant",
    diel_elec="Electronic dielectric constant",
    diel_ionic="Ionic dielectric constant",
    bandgap_us="E<sub>gap Us</sub> (eV)",
    bandgap_mp="E<sub>gap MP</sub> (eV)",
    bandgap_pbe="E<sub>gap PBE</sub> (eV)",
    bandgap_wren="E<sub>Wren</sub> (eV)",
)

# https://github.com/plotly/Kaleido/issues/122#issuecomment-994906924
try:
    pio.kaleido.scope.mathjax = None
except AttributeError:
    # if kaleido is not installed, the linked GH issue doesn't apply
    pass

crystal_sys_order = (
    "cubic hexagonal trigonal tetragonal orthorhombic monoclinic triclinic".split()
)


pio.templates.default = pmv_dark_template
px.defaults.template = pmv_dark_template


plt.rc("font", size=16)
plt.rc("savefig", bbox="tight", dpi=200)
plt.rc("figure", dpi=200, titlesize=18)
plt.rcParams["figure.constrained_layout.use"] = True
