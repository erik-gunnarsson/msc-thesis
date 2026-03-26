# MSc Thesis: Industrial Robots, Labour Input, and Collective Bargaining Institutions

This repository contains the empirical code for an MSc thesis on how collective bargaining institutions condition the relationship between industrial robot adoption and labour input across European manufacturing industries.

The codebase currently supports two connected workflows:

- a **mainline WIOD labour workflow** for the revised thesis specification
- a **KLEMS legacy workflow** used as a robustness and overlap comparison

## Research Focus

The thesis studies whether country-level bargaining institutions moderate the labour-market effects of robots, and whether that moderation differs across industries.

Active institutional channels:

- `coord`: bargaining coordination — primary focal channel
- `adjcov`: adjusted collective-bargaining coverage — secondary focal channel, restricted sample
- `ud`: union density — reference benchmark, non-focal

Current empirical hierarchy:

- **Eq. 1-2 (headline)**: robots -> labour input, then robots x institutions
- **Eq. 3-4 (exploratory / appendix)**: bucket heterogeneity and bucket x institution contrasts
- **Exposure models (archived)**: retained in the repo as a historical comparison, not part of the active thesis workflow

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

### 1. WIOD Mainline Labour Workflow

This is now the primary empirical workflow for the thesis. It keeps labour input as the outcome, uses WIOD SEA to expand country coverage, and treats institutional moderation as the headline contribution.

Core scripts:

- [code/14_wiod_first_results.py](code/14_wiod_first_results.py)
- [code/09_build_wiod_panel.py](code/09_build_wiod_panel.py)
- [code/10_wiod_baseline.py](code/10_wiod_baseline.py)
- [code/11_wiod_institution_moderation.py](code/11_wiod_institution_moderation.py)
- [code/12_wiod_bucket_models.py](code/12_wiod_bucket_models.py)

Shared helpers:

- [code/_wiod_panel_utils.py](code/_wiod_panel_utils.py)
- [code/_wiod_model_utils.py](code/_wiod_model_utils.py)

Supporting audit material lives under [analysis/trade_feasibility](analysis/trade_feasibility):

- trade/sample-size feasibility audit
- regression-readiness audit
- WIOD labour design audit and archived exposure comparison

### 2. KLEMS Legacy / Robustness Workflow

This remains the original thesis pipeline built around KLEMS labour input and controls, and now serves as a legacy specification and overlap robustness check.

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

Key files:

- [analysis/trade_feasibility/README.md](analysis/trade_feasibility/README.md)
- [analysis/trade_feasibility/01_data_availability_audit.py](analysis/trade_feasibility/01_data_availability_audit.py)
- [analysis/trade_feasibility/02_merge_feasibility.py](analysis/trade_feasibility/02_merge_feasibility.py)
- [analysis/trade_feasibility/03_sample_size_report.py](analysis/trade_feasibility/03_sample_size_report.py)
- [analysis/trade_feasibility/regression_ready_audit.py](analysis/trade_feasibility/regression_ready_audit.py)
- [analysis/trade_feasibility/04_wiod_labour_design_comparison.py](analysis/trade_feasibility/04_wiod_labour_design_comparison.py)
- [code/13_wiod_exposure_models.py](code/13_wiod_exposure_models.py) (archived comparison)

## Current Empirical Position

The repo now reflects the following working stance:

- The thesis outcome remains **labour input**, not exports.
- WIOD is now the **mainline workflow**, with KLEMS retained as a robustness / legacy comparison.
- WIOD is used in two ways:
  - `H_EMPE` as a broader-coverage labour-input measure
  - trade tables only for archived exposure diagnostics, not the active thesis workflow
- Institutional channel hierarchy:
  - `coord` = headline institutional result
  - `adjcov` = secondary focal restricted-sample result
  - `ud` = reference benchmark only
- **Eq. 2 institutional moderation** is the headline contribution.
- **Eq. 3-4 bucket models** remain in the workflow as exploratory / appendix material.

The current WIOD labour audit shows:

- base WIOD labour panel: `24 countries / 236 entities / 2283 observations / 2001-2014`
- `EQ4_COORD_BUCKET`: `23 countries / 2212 observations`
- `EQ4_UD_BUCKET`: `21 countries / 2068 observations`

The pooled bucket models are estimable, but bucket 2 and bucket 3 are the thinner contrasts and should be interpreted more cautiously.

## Empirical Specification

The active empirical design is a country x industry x year panel with
country-industry fixed effects and year fixed effects.

### Mainline WIOD equations

Headline equations:

```text
Eq. 1 (baseline)
ln(H_EMPE)_ijt
  = beta1 * ln(Robots)_{ij,t-1}
  + gamma1 * ln(VA_QI)_{ijt}
  + gamma2 * ln(K)_{ijt}
  + gamma3 * GDPGrowth_it
  + alpha_ij + delta_t + eps_ijt

Eq. 2 (institutional moderation)
ln(H_EMPE)_ijt
  = beta1 * ln(Robots)_{ij,t-1}
  + beta2 * [ln(Robots)_{ij,t-1} x M_c]
  + gamma1 * ln(VA_QI)_{ijt}
  + gamma2 * ln(K)_{ijt}
  + gamma3 * GDPGrowth_it
  + alpha_ij + delta_t + eps_ijt
```

Exploratory / appendix equations:

```text
Eq. 3 (bucket heterogeneity)
ln(H_EMPE)_ijt
  = beta1 * ln(Robots)_{ij,t-1}
  + sum_(b != 5) beta2b * [ln(Robots)_{ij,t-1} x Bucket_bj]
  + gamma1 * ln(VA_QI)_{ijt}
  + gamma2 * ln(K)_{ijt}
  + gamma3 * GDPGrowth_it
  + alpha_ij + delta_t + eps_ijt

Eq. 4 (bucket x institution, exploratory)
ln(H_EMPE)_ijt
  = beta1 * ln(Robots)_{ij,t-1}
  + sum_(b != 5) beta2b * [ln(Robots)_{ij,t-1} x Bucket_bj]
  + beta3 * [ln(Robots)_{ij,t-1} x M_c]
  + sum_(b != 5) beta4b * [ln(Robots)_{ij,t-1} x M_c x Bucket_bj]
  + gamma1 * ln(VA_QI)_{ijt}
  + gamma2 * ln(K)_{ijt}
  + gamma3 * GDPGrowth_it
  + alpha_ij + delta_t + eps_ijt
```

### Variable legend

- `i`: country
- `j`: manufacturing industry
- `t`: year
- `ln(H_EMPE)_ijt`: log labour input from WIOD SEA (`H_EMPE`)
- `ln(Robots)_{ij,t-1}`: one-year-lagged log robot intensity from IFR, implemented as `ln_robots_lag1`
- `ln(VA_QI)_{ijt}`: log real value added from WIOD SEA, implemented as `ln_va_wiod_qi`
- `ln(K)_{ijt}`: log capital stock proxy from WIOD SEA, implemented as `ln_k_wiod`
- `GDPGrowth_it`: country-level GDP growth, implemented as `gdp_growth`
- `M_c`: baseline-frozen institutional moderator for country `c`
- `coord_pre_c`: bargaining coordination, centered around the sample mean
- `adjcov_pre_c`: adjusted collective-bargaining coverage, centered around the sample mean
- `ud_pre_c`: union density, centered around the sample mean
- `Bucket_bj`: industry bucket dummy for non-reference bucket `b`
- `alpha_ij`: country-industry fixed effects
- `delta_t`: year fixed effects
- `eps_ijt`: idiosyncratic error term

### Bucket mapping

The bucket specification uses bucket 5 as the omitted reference category.

- Bucket 1: `C29-C30` — transport equipment
- Bucket 2: `C26-C27`, `C28` — electro-mechanical capital goods
- Bucket 3: `C24-C25` — metals
- Bucket 4: `C19`, `C20-C21`, `C22-C23` — process and materials
- Bucket 5: `C10-C12`, `C13-C15`, `C16-C18`, `C31-C33` — low-tech / traditional

### Identification note

The institutional moderators are country-level and baseline-frozen, so their
standalone main effects are absorbed by the country-industry fixed effects.
Likewise, bucket main effects are absorbed by the country-industry fixed
effects. What is identified in Eq. 2 and Eq. 4 is the way institutional or
bucket structure changes the slope on robot adoption.

### KLEMS legacy mapping

The KLEMS legacy workflow uses the same model structure, but with a different
labour-input and control set:

- outcome: `ln_hours` from KLEMS `LAB_QI`
- output control: `ln_va`
- capital control: `ln_cap`
- optional macro controls: `ln_gdp`, `unemployment`

## Control Comparability

The WIOD and KLEMS specifications are intentionally comparable, but they are not identical:

- `LAB_QI` vs `H_EMPE`: same labour-input family, different measurement
- `VA_PYP` vs `VA_QI`: reasonably comparable real-output controls
- `CAP_QI` vs `K` / `CAP`: not directly equivalent

That means the KLEMS-WIOD comparison should be interpreted as a **joint measurement-and-controls robustness check**, not as a pure outcome-only swap.

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

Mainline WIOD workflow:

```bash
uv run python code/14_wiod_first_results.py
```

This first-results runner freezes the mainline specification and produces the
headline WIOD package in review order:

- `Eq. 1` baseline
- `Eq. 2 coord` (primary focal)
- `Eq. 2 adjcov --sample common` (secondary focal restricted-sample)
- `Eq. 2 ud` (reference benchmark)

Read these outputs first:

- `outputs/wiod_first_results_summary.csv`
- `outputs/wiod_first_results_overview.md`
- `outputs/wiod_eq1_baseline_*`
- `outputs/primary_contribution_eq2_wiod_coord_*`
- `outputs/secondary_focal_eq2_wiod_adjcov_*`
- `outputs/reference_benchmark_eq2_wiod_ud_*`

Not part of the initial first-results package:

- exploratory bucket models from [code/12_wiod_bucket_models.py](code/12_wiod_bucket_models.py)
- KLEMS legacy workflow from [code/00_run_pipeline.py](code/00_run_pipeline.py)
- archived exposure comparison from [code/13_wiod_exposure_models.py](code/13_wiod_exposure_models.py)

Manual WIOD component runs:

```bash
uv run python code/09_build_wiod_panel.py
uv run python code/10_wiod_baseline.py
uv run python code/11_wiod_institution_moderation.py --moderator coord
uv run python code/11_wiod_institution_moderation.py --moderator adjcov --sample common
uv run python code/11_wiod_institution_moderation.py --moderator ud
uv run python code/12_wiod_bucket_models.py --mode eq3
uv run python code/12_wiod_bucket_models.py --mode eq4 --moderator coord
uv run python code/12_wiod_bucket_models.py --mode eq4 --moderator adjcov --sample common
uv run python code/12_wiod_bucket_models.py --mode eq4 --moderator ud
```

Trade-feasibility and WIOD audit workflow:

```bash
uv run python analysis/trade_feasibility/01_data_availability_audit.py
uv run python analysis/trade_feasibility/02_merge_feasibility.py
uv run python analysis/trade_feasibility/03_sample_size_report.py
uv run python analysis/trade_feasibility/regression_ready_audit.py
uv run python analysis/trade_feasibility/04_wiod_labour_design_comparison.py
```

Full KLEMS legacy / robustness workflow:

```bash
uv run python code/00_run_pipeline.py
```

## Notes

- `outputs/`, most of `data/`, and figures are ignored or regenerated locally.
- The trade-feasibility branch outputs that matter for documentation live under [analysis/trade_feasibility/output](analysis/trade_feasibility/output).
- Greece is harmonized as `GR -> EL` in the new WIOD/trade audit code.
- [code/13_wiod_exposure_models.py](code/13_wiod_exposure_models.py) is retained as an archived comparison script but is not part of the active thesis run sequence.
- In the active thesis framing, `coord` is focal, `adjcov` is secondary but theory-relevant, and `ud` is retained as a reference benchmark only.
- [code/14_wiod_first_results.py](code/14_wiod_first_results.py) archives stale WIOD-only output artifacts into `outputs/archive/` before regenerating the first-results bundle, so the reviewed outputs stay focused on the current naming family.
