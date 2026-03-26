# WIOD Eq. 2b Hawk-Dove Gate

Status: **GO**

Exact estimation support:
- Sample: 2068 obs, 206 entities, 21 countries
- Years: 2001-2014
- Controls: ln_va_wiod_qi, ln_k_wiod, gdp_growth

Joint-distribution diagnostics:
- Pearson corr(coord_pre, ud_pre): `0.297`
- UD median used for binary cell split: `42.650`
- Minimum Hawk-Dove cell size: `3` countries
- Max FE-style VIF: `1.387`

Decision notes:
- Gate passed cleanly: moderator spread is workable, all Hawk-Dove cells are populated, and FE-style VIFs are low.

Benchmark check:
- Eq. 2b sample benchmark against current Eq. 2 ud support: matches (Eq. 2b = 21 countries / 206 entities / 2068 obs; Eq. 2 ud = 21 countries / 206 entities / 2068 obs).

Saved artifacts:
- `wiod_eq2b_coord_ud_country_table.csv`
- `wiod_eq2b_coord_ud_cell_counts.csv`
- `wiod_eq2b_coord_ud_vif.csv`
- `wiod_eq2b_coord_ud_scatter.png`
