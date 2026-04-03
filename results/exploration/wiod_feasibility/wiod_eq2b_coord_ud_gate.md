# WIOD Eq. 2b Hawk-Dove Gate

Status: **GO**

Exact estimation support:
- Sample: 2356 obs, 227 entities, 23 countries
- Years: 2001-2014
- Controls: ln_va_wiod_qi, ln_k_wiod, gdp_growth

Joint-distribution diagnostics:
- Pearson corr(coord_pre, ud_pre): `0.325`
- UD median used for binary cell split: `42.650`
- Minimum Hawk-Dove cell size: `3` countries
- Max FE-style VIF: `1.380`

Decision notes:
- Gate passed cleanly: moderator spread is workable, all Hawk-Dove cells are populated, and FE-style VIFs are low.

Benchmark check:
- Eq. 2b sample benchmark against current Eq. 2 ud support: matches (Eq. 2b = 23 countries / 227 entities / 2356 obs; Eq. 2 ud = 23 countries / 227 entities / 2356 obs).

Saved artifacts:
- `wiod_eq2b_coord_ud_country_table.csv`
- `wiod_eq2b_coord_ud_cell_counts.csv`
- `wiod_eq2b_coord_ud_vif.csv`
- `wiod_eq2b_coord_ud_scatter.png`
