"""Script to collect and analyze statistics on dielectric materials candidates.

Specifically, this script calculates statistics on observed dielectric constants,
bandgaps, and figures of merit (FOM) from different sources including:
- Materials Project (mp-)
- Materials Virtual Lab (mvc-)
- WBM database (wbm-)
- Generated substitution candidates (containing "->")

The script applies the following thresholds for analysis:
- Dielectric constant: < 100
- PBE bandgap: > 0.1 eV
- Figure of merit: > 240

It prints:
- Total counts of materials from each source
- Hit rates for materials meeting various threshold combinations from each source
- Generates histograms comparing different bandgap calculation methods
"""

# %%
from __future__ import annotations

from dielectrics import Key
from dielectrics.db.fetch_data import df_diel_from_task_coll


# %% see db/readme.md for details on how candidates in each df were selected
df_all = df_diel_from_task_coll({}, cache=False).round(3)


# %%
diel_elec_threshold = 100
pbe_bandgap_threshold = 0.1
fom_threshold = 240

diel_elec_mask = df_all[Key.diel_elec_pbe] < diel_elec_threshold
# pbe_bandgap_mask = df_all[Key.bandgap_pbe] > pbe_bandgap_threshold
# pbe_bandgap_mask = df_all[Key.bandgap_us] > pbe_bandgap_threshold
pbe_bandgap_mask = df_all["bandgap_pbe_best"] > pbe_bandgap_threshold
fom_mask = df_all[Key.fom_pbe] > fom_threshold
sub_mask = df_all[Key.mat_id].str.contains("->")
mp_source_mask = df_all[Key.mat_id].str.contains("mp-") & ~sub_mask
mvc_source_mask = df_all[Key.mat_id].str.contains("mvc-") & ~sub_mask
wbm_source_mask = df_all[Key.mat_id].str.contains("wbm-") & ~sub_mask

diel_bandgap_mask = diel_elec_mask & pbe_bandgap_mask
diel_fom_mask = diel_elec_mask & fom_mask
bandgap_fom_mask = pbe_bandgap_mask & fom_mask
all_mask = diel_elec_mask & pbe_bandgap_mask & fom_mask


print(f"Total number of candidates: {len(df_all)}")
print(f"Number of generated candidates: {sub_mask.sum()}")
print(f"Number from all sources: {len(df_all) - sub_mask.sum()}")
print(f"\tNumber of mp candidates: {mp_source_mask.sum()}")
print(f"\tNumber of mvc candidates: {mvc_source_mask.sum()}")
print(f"\tNumber of wbm candidates: {wbm_source_mask.sum()}")
if len(df_all) != sum(sub_mask) + sum(mp_source_mask) + sum(mvc_source_mask) + sum(
    wbm_source_mask
):
    raise ValueError("Sum of masks does not equal total number of candidates")

print(f"\nUsing dielectric constant threshold: {diel_elec_threshold}")
print(f"Using bandgap threshold: {pbe_bandgap_threshold}")
print(f"Using FOM threshold: {fom_threshold}")

print(
    f"\nNumber with dielectric constant < {diel_elec_threshold}: {diel_elec_mask.sum()}"
)
print(f"Number with bandgap > {pbe_bandgap_threshold} eV: {pbe_bandgap_mask.sum()}")
print(f"Number with FOM > {fom_threshold}: {fom_mask.sum()}")

print(
    "\nNumber of generated candidates with dielectric constant < "
    f"{diel_elec_threshold}: {(diel_elec_mask & sub_mask).sum()}"
)
n_all_sources = diel_elec_mask.sum() - (diel_elec_mask & sub_mask).sum()
print(f"Number from all sources: {n_all_sources}")
print(
    f"\tNumber of mp candidates with dielectric constant < {diel_elec_threshold}: "
    f"{(diel_elec_mask & mp_source_mask).sum()}"
)
print(
    f"\tNumber of mvc candidates with dielectric constant < {diel_elec_threshold}: "
    f"{(diel_elec_mask & mvc_source_mask).sum()}"
)
print(
    f"\tNumber of wbm candidates with dielectric constant < {diel_elec_threshold}: "
    f"{(diel_elec_mask & wbm_source_mask).sum()}"
)
if len(diel_elec_mask) != sum(sub_mask) + sum(mp_source_mask) + sum(
    mvc_source_mask
) + sum(wbm_source_mask):
    raise ValueError("Sum of masks does not equal total number of candidates")

print(
    f"\nNumber with dielectric constant < {diel_elec_threshold} and "
    f"bandgap > {pbe_bandgap_threshold} eV: {diel_bandgap_mask.sum()}"
)
print(
    f"Number with dielectric constant < {diel_elec_threshold} and "
    f"FOM > {fom_threshold}: {diel_fom_mask.sum()}"
)
print(
    f"Number with bandgap > {pbe_bandgap_threshold} eV and "
    f"FOM > {fom_threshold}: {bandgap_fom_mask.sum()}"
)
print(
    f"Number with dielectric constant < {diel_elec_threshold}, "
    f"bandgap > {pbe_bandgap_threshold} eV, and FOM > {fom_threshold}: {all_mask.sum()}"
)

print(f"\nHit rate all: {diel_fom_mask.sum() / diel_elec_mask.sum():.2%}")
print(
    f"Hit rate bandgap > {pbe_bandgap_threshold}: "
    f"{all_mask.sum() / diel_bandgap_mask.sum():.2%}"
)


# %%
all_mp_source_mask = mp_source_mask + mvc_source_mask
mp_hit_rate_all = sum(all_mp_source_mask & diel_fom_mask) / sum(
    all_mp_source_mask & diel_elec_mask
)
print(f"\nMP Hit rate all: {mp_hit_rate_all:.2%}")
mp_hit_rate_bandgap = sum(all_mp_source_mask & all_mask) / sum(
    all_mp_source_mask & diel_bandgap_mask
)
print(f"MP Hit rate bandgap > {pbe_bandgap_threshold}: {mp_hit_rate_bandgap:.2%}")

wbm_hit_rate_all = sum(wbm_source_mask & diel_fom_mask) / sum(
    wbm_source_mask & diel_elec_mask
)
print(f"\nWBM Hit rate all: {wbm_hit_rate_all:.2%}")
wbm_hit_rate_bandgap = sum(wbm_source_mask & all_mask) / sum(
    wbm_source_mask & diel_bandgap_mask
)
print(f"WBM Hit rate bandgap > {pbe_bandgap_threshold}: {wbm_hit_rate_bandgap:.2%}")

elem_sub_hit_rate_all = sum(sub_mask & diel_fom_mask) / sum(sub_mask & diel_elec_mask)
print(f"\nSUB Hit rate all: {elem_sub_hit_rate_all:.2%}")
elem_sub_hit_rate_bandgap = sum(sub_mask & all_mask) / sum(sub_mask & diel_bandgap_mask)
print(
    f"SUB Hit rate bandgap > {pbe_bandgap_threshold}: {elem_sub_hit_rate_bandgap:.2%}"
)


# %%
ax = df_all[(~sub_mask) & diel_elec_mask][Key.bandgap_pbe].hist(bins=100, alpha=0.5)
df_all[(~sub_mask) & diel_elec_mask][Key.bandgap_us].hist(bins=100, alpha=0.5)
df_all[(~sub_mask) & diel_elec_mask]["bandgap_pbe_best"].hist(bins=100, alpha=0.5)
ax.legend(["PBE", "US", "PBE best"])


# %%
assert all(
    x in df_all[diel_bandgap_mask][Key.mat_id].to_list()
    for x in ["mp-756175", "mp-1225854:W->Te"]
)

# print(df_all.loc["mp-756175"])
# print(df_all.loc["mp-1225854:W->Te"])
