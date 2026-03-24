# MSc Thesis: Industrial Robots, Labour Input, and Collective Bargaining Institutions

This repository contains the empirical code for an MSc thesis on how collective bargaining institutions condition the relationship between industrial robot adoption and labour input across European manufacturing industries.

The codebase currently supports two connected workflows:

- a **mainline KLEMS panel** for the original thesis specification
- a **WIOD labour extension** that expands country coverage using `H_EMPE` from WIOD Socio-Economic Accounts and compares bucket heterogeneity with an exposed/sheltered alternative

## Research Focus

The thesis studies whether country-level bargaining institutions moderate the labour-market effects of robots, and whether that moderation differs across industries.

Active institutional channels:

- `ud`: union density
- `coord`: bargaining coordination
- `adjcov`: adjusted collective-bargaining coverage

Active heterogeneity designs:

- **Buckets (main design)**: five operational manufacturing buckets
- **Exposure (comparison design)**: exposed vs sheltered industries using WIOD trade intensity

## Active Data Sources

Expected raw inputs live under `data/` in the local workspace.

- `IFR_karol.csv`: robot intensity / stock data
- `klems_growth_accounts_basic.csv`: KLEMS labour and control variables
- `ictwss_institutions.csv`: institutional moderators
- `eurostata_gdp_nama_10_gdp.csv`: GDP series
- `eurostat_employment_une_rt_a.csv`: unemployment series
- `WIOTS_in_EXCEL/WIOT{year}_Nov16_ROW.xlsb`: WIOD trade tables
- `WIOTS_SEA/Socio_Economic_Accounts.xlsx`: WIOD Socio-Economic Accounts

The repository does **not** depend on the old `testing/` sandbox or archived scripts anymore.

## Main Workflows

### 1. KLEMS Mainline Panel

This remains the original thesis pipeline built around KLEMS labour input and controls.

Core scripts:

- [code/00_run_pipeline.py](code/00_run_pipeline.py)
- [code/01_data_check.py](code/01_data_check.py)
- [code/02_build_klems_panel.py](code/02_build_klems_panel.py)
- [code/03_ictwss_moderator_triage.py](code/03_ictwss_moderator_triage.py)
- [code/04_klems_baseline.py](code/04_klems_baseline.py)
- [code/05_klems_institution_moderation.py](code/05_klems_institution_moderation.py)
- [code/06_klems_adjcov_moderation.py](code/06_klems_adjcov_moderation.py)
- [code/07_klems_bucket_moderation.py](code/07_klems_bucket_moderation.py)
- [code/08_klems_bucket_adjcov_continuous.py](code/08_klems_bucket_adjcov_continuous.py)

Shared helpers:

- [code/_klems_utils.py](code/_klems_utils.py)
- [code/_wiod_panel_utils.py](code/_wiod_panel_utils.py)
- [code/_wiod_model_utils.py](code/_wiod_model_utils.py)

### 2. WIOD Feasibility And Labour Extension

This branch of work lives under [analysis/trade_feasibility](analysis/trade_feasibility) and in the new WIOD scripts under [code](code).

It has three parts:

- trade/sample-size feasibility audit
- regression-readiness audit
- WIOD labour panel with bucket-vs-exposure comparison

Key files:

- [analysis/trade_feasibility/README.md](analysis/trade_feasibility/README.md)
- [analysis/trade_feasibility/01_data_availability_audit.py](analysis/trade_feasibility/01_data_availability_audit.py)
- [analysis/trade_feasibility/02_merge_feasibility.py](analysis/trade_feasibility/02_merge_feasibility.py)
- [analysis/trade_feasibility/03_sample_size_report.py](analysis/trade_feasibility/03_sample_size_report.py)
- [analysis/trade_feasibility/regression_ready_audit.py](analysis/trade_feasibility/regression_ready_audit.py)
- [analysis/trade_feasibility/04_wiod_labour_design_comparison.py](analysis/trade_feasibility/04_wiod_labour_design_comparison.py)
- [code/09_build_wiod_panel.py](code/09_build_wiod_panel.py)
- [code/10_wiod_baseline.py](code/10_wiod_baseline.py)
- [code/11_wiod_institution_moderation.py](code/11_wiod_institution_moderation.py)
- [code/12_wiod_bucket_models.py](code/12_wiod_bucket_models.py)
- [code/13_wiod_exposure_models.py](code/13_wiod_exposure_models.py)

## Current Empirical Position

The repo now reflects the following working stance:

- The thesis outcome remains **labour input**, not exports.
- WIOD is used in two ways:
  - `H_EMPE` as a broader-coverage labour-input measure
  - trade tables only for exposure classification
- The **bucket design remains the main heterogeneity specification**.
- Exposed/sheltered is implemented as a **parsimonious comparison**, not a replacement.

The current WIOD labour audit shows:

- base WIOD labour panel: `24 countries / 236 entities / 2283 observations / 2001-2014`
- `EQ4_UD_BUCKET`: `21 countries / 2068 observations`
- `EQ4_COORD_BUCKET`: `23 countries / 2212 observations`

The pooled bucket models are estimable, but bucket 2 and bucket 3 are the thinner contrasts and should be interpreted more cautiously.

## Inference Conventions

The repo currently uses two inference regimes:

- **KLEMS scripts**: entity-clustered baseline, with existing robustness options where implemented
- **WIOD scripts**: country-clustered headline inference, wild cluster bootstrap p-values for key interaction terms, and secondary entity-clustered / Driscoll-Kraay comparisons

This matters because the institutional moderators vary at the country level.

## Repository Layout

```text
.
├── .github/workflows/ci.yml
├── analysis/trade_feasibility/
├── code/
├── streamlit/
├── README.md
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

Active code directories:

- [code](code): panel building and regression scripts
- [analysis/trade_feasibility](analysis/trade_feasibility): audit scripts and branch-specific outputs
- [streamlit](streamlit): dashboard/prototype app

## Setup

Using `uv`:

```bash
uv sync
```

Using `pip`:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## How To Run

Smoke test:

```bash
uv run python code/00_run_pipeline.py --smoke
```

Full KLEMS pipeline:

```bash
uv run python code/00_run_pipeline.py
```

WIOD audit workflow:

```bash
uv run python analysis/trade_feasibility/01_data_availability_audit.py
uv run python analysis/trade_feasibility/02_merge_feasibility.py
uv run python analysis/trade_feasibility/03_sample_size_report.py
uv run python analysis/trade_feasibility/regression_ready_audit.py
uv run python analysis/trade_feasibility/04_wiod_labour_design_comparison.py
```

WIOD labour model workflow:

```bash
uv run python code/09_build_wiod_panel.py
uv run python code/10_wiod_baseline.py
uv run python code/11_wiod_institution_moderation.py --moderator coord
uv run python code/11_wiod_institution_moderation.py --moderator ud
uv run python code/12_wiod_bucket_models.py --mode eq4 --moderator coord
uv run python code/12_wiod_bucket_models.py --mode eq4 --moderator ud
uv run python code/13_wiod_exposure_models.py --mode eq5b --moderator coord
uv run python code/13_wiod_exposure_models.py --mode eq5b --moderator ud
```

## Notes

- `outputs/`, most of `data/`, and figures are ignored or regenerated locally.
- The trade-feasibility branch outputs that matter for documentation live under [analysis/trade_feasibility/output](analysis/trade_feasibility/output).
- Greece is harmonized as `GR -> EL` in the new WIOD/trade audit code.
