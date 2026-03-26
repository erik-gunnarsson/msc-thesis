# Trade Feasibility And Readiness Archive

This directory stores the retained outputs and reporting material from the exploratory audits that shaped the WIOD branch.

These materials are **not** part of the live thesis run sequence. They are here to document:

- the original WIOD trade-feasibility check
- the regression-readiness audit
- the Hawk-Dove gate for the exploratory `Eq. 2b` extension

The active thesis workflow now lives under:

- `code/core/`
- `code/secondary/`
- `results/core/`
- `results/secondary/`

## Scripts

Exploration scripts now live in:

- `code/exploration/wiod_feasibility/01_data_availability_audit.py`
- `code/exploration/wiod_feasibility/02_merge_feasibility.py`
- `code/exploration/wiod_feasibility/03_sample_size_report.py`
- `code/exploration/wiod_feasibility/regression_ready_audit.py`
- `code/exploration/wiod_feasibility/05_wiod_eq2b_hawk_dove_gate.py`

The earlier WIOD labour design-comparison script and the bucket-model exploration are no longer active in this branch.

## What These Audits Established

### Phase 1: Trade Feasibility

The original feasibility question was whether replacing KLEMS-side trade support with WIOD materially expanded usable country coverage.

Headline findings:

- `A: IFR x WIOD (max)` = 24 countries
- `B: IFR x WIOD x ICTWSS (coord + ud)` = 21 countries
- `C: IFR x WIOD x ICTWSS (adjcov)` = 14 countries
- `D: Current (IFR x KLEMS x ICTWSS)` = 14 countries

This established that the WIOD-side country expansion was real and worth pursuing.

### Phase 2: Regression Readiness

The readiness audit checked whether WIOD SEA could replace KLEMS-side controls without collapsing the sample.

Headline findings:

- WIOD SEA support is complete across the relevant manufacturing sectors
- the SEA-backed base panel is 24 countries over 2001-2014
- `coord` models remain above the main-country threshold
- `adjcov` remains usable only on a restricted sample
- unemployment is too incomplete to be a default robustness control

### Phase 3: Hawk-Dove Gate

The gate checks whether `coord` and `ud` vary enough jointly to justify the exploratory `Eq. 2b` three-way interaction.

Saved gate outputs show:

- 21-country joint support
- moderate `coord` / `ud` correlation rather than near-collinearity
- populated Hawk-Dove diagnostic cells
- low FE-style VIFs for the joint interaction regressors

That is why `Eq. 2b` remains in the active branch as an exploratory extension.

## Output Locations

Current exploration artifacts are written here:

- `results/exploration/wiod_feasibility/`

Active WIOD results are written elsewhere:

- `results/core/`
- `results/secondary/`

The pre-cleanup snapshot of the old structure is preserved in:

- `results/archive/legacy_migration_20260326T205521Z/`

## Key Current Files

Examples of retained exploration outputs:

- `sea_coverage_matrix.csv`
- `sample_attrition_table.csv`
- `regression_ready_summary.txt`
- `wiod_trade_panel.csv`
- `wiod_eq2b_coord_ud_gate.md`
- `wiod_eq2b_coord_ud_country_table.csv`
- `wiod_eq2b_coord_ud_cell_counts.csv`
- `wiod_eq2b_coord_ud_vif.csv`
- `wiod_eq2b_coord_ud_scatter.png`

## Important Boundary

This directory is historical and diagnostic.

It should be read as:

- branch history
- feasibility evidence
- readiness evidence
- theory-gate documentation

It should **not** be read as the current execution guide for the thesis workflow.
