# WIOD Feasibility And Readiness Archive

This directory stores the retained outputs and reporting material from the exploratory audits that shaped the WIOD branch.

These materials are **not** part of the live thesis run sequence. They are here to document:

- the original WIOD trade-feasibility check
- the regression-readiness audit
- the Hawk-Dove gate for the exploratory `Eq. 2b` extension
- the broader Europe-candidate availability audit

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

Headline findings after broadening the country universe from EU-only to the wider Europe-candidate scope:

- `A: IFR x WIOD (max)` = 26 countries
- `B: IFR x WIOD x ICTWSS (coord + ud)` = 23 countries
- `C: IFR x WIOD x ICTWSS (adjcov)` = 15 countries
- `D: Current (IFR x KLEMS x ICTWSS)` = 14 countries

This established that the WIOD-side country expansion was real and worth pursuing.

### Phase 1b: Europe-Candidate Availability Audit

The exploration layer now also audits the broader European candidate universe that is visible in the currently downloaded WIOD, IFR, ICTWSS, and Eurostat files.

This audit distinguishes:

- countries that are present in the raw downloaded sources
- countries that make it into the raw WIOD panel
- countries that survive the active Eq. 1 / Eq. 2 / Eq. 2b regression requirements

Current broad-scope headline counts:

- candidate universe audited: 33 countries
- four-way raw overlap across WIOD SEA, IFR, ICTWSS, and GDP: 27 countries
- active WIOD Eq. 1 support: 26 countries
- active WIOD Eq. 2 coord support: 25 countries
- active WIOD Eq. 2 ud support: 23 countries
- active WIOD Eq. 2 adjcov support: 15 countries
- active WIOD Eq. 2b support: 23 countries

With the current files, the practical non-EU additions that actually survive into the active regressions are `UK` and `NO`, while `CH` remains audit-only because the IFR extract does not currently yield usable lagged robot support there.

### Phase 2: Regression Readiness

The readiness audit checked whether WIOD SEA could replace KLEMS-side controls without collapsing the sample.

This historical audit predates the broader Europe-candidate expansion and should be read as a legacy readiness check on the earlier narrower sample.

Headline findings:

- WIOD SEA support is complete across the relevant manufacturing sectors
- the SEA-backed base panel is 24 countries over 2001-2014
- `coord` models remain above the main-country threshold
- `adjcov` remains usable only on a restricted sample
- unemployment is too incomplete to be a default robustness control

### Phase 3: Hawk-Dove Gate

The gate checks whether `coord` and `ud` vary enough jointly to justify the exploratory `Eq. 2b` three-way interaction.

Saved gate outputs now show:

- 23-country joint support
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

- `europe_country_availability_matrix.csv`
- `europe_country_availability_summary.csv`
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
