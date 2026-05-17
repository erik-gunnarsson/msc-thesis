### Meeting agenda (Rebecka, 15 May 2026) — Q7

**Question:** Switzerland exclusion and robot stock vs robot intensity as the headline regressor.

**Context:** CH excluded because IFR `robot_wrkr_stock_95` denominator is zero across CH sub-industries. Headline regressor is `ln_robots_lag1` (per-worker intensity).

**Sub-questions:** (1) Defend CH exclusion in limitations + document alt-normalisation as infeasible, or pursue CH-inclusive sensitivity with another denominator? (2) Field default on intensity vs log stock — keep intensity as headline (Leibrecht et al. 2023 alignment) and report `ln_robot_stock_lag1` as robustness?

### Live notes

- **Locked (GH #29):** Headline **`ln_robots_lag1`** (Leibrecht comparator). **`ln_robot_stock_lag1`** appendix table pairs Eq. 1 + Eq. 2 coord with CH — `results/tables/wiod_regression_table_appendix_robot_stock_ch_inclusive.*`; cite from §6.2.2 and §6.2.3.

### Decision / next action

- Short §8.1 CH paragraph + footnote where intensity is defined; Bryman & Bell Ch. 7 / 14 framing optional in prose.
