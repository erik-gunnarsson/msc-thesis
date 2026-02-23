# Archived Scripts

These scripts are from earlier analysis phases. The active pipeline now uses a
three-channel institutional moderation approach (UD, Coord, AdjCov) with
predetermined (1990-1995 baseline) measures, bucket-based industry heterogeneity,
and full/common sample harmonization. See the main `code/` directory and
`README.md` for the current methodology.

These scripts are superseded and retained for auditability only. They are **not** included in `runall.py`.

## Why archived

- **`6-equation4-industry-heterogeneity-coordination.py`** — Ran separate regressions per NACE industry. Replaced by bucket-based pooled interaction model (`6-equation4-bucket-heterogeneity-coordination.py`) for statistical power.

- **`7-equation5-industry-heterogeneity-coverage.py`** — Same issue; replaced by `7-equation5-bucket-heterogeneity-coverage.py`.

- **`8-equation6-routinetaskintensity.py`** — Stub for a skill-intensity triple interaction. Superseded by the bucket approach, which captures technology-intensity heterogeneity through theory-driven industry groupings.

- **`2-cleaning-data.py`** — Renamed to `2-build_panel.py` in the active pipeline. This is the pre-bucket version retained for reference.
