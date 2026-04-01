# MSc Thesis: Robots, Labour Input, and Collective Bargaining Institutions

This repository contains the empirical code for an MSc thesis on how industrial robot adoption affects labour input in manufacturing, and how that relationship is conditioned by collective bargaining institutions.

- `Eq. 1`: baseline robot-labour relationship
- `Eq. 2`: single-moderator institutional moderation
- `Eq. 2b`: exploratory joint `coord x ud` Hawk-Dove extension

## Research Focus

The active thesis question is:

To what extent does collective bargaining coordination influence the relationship between industrial robot adoption and employment in European manufacturing industries?​

Institutional hierarchy in the active workflow:

- `coord`: bargaining coordination, primary focal moderator
- `adjcov`: adjusted collective-bargaining coverage, secondary focal moderator with restricted sample
- `ud`: union density, reference benchmark only

Current empirical hierarchy:

- `Eq. 1` and `Eq. 2` are the headline models
- `Eq. 2b` is an exploratory theory test of the Hawk-Dove intuition

## Active Data Sources

Expected local inputs under `data/`:

- `IFR_karol.csv`
- `ictwss_institutions.csv`
- `eurostata_gdp_nama_10_gdp.csv`
- `eurostat_employment_une_rt_a.csv`
- `WIOTS_SEA/Socio_Economic_Accounts.xlsx`
- `WIOTS_in_EXCEL/WIOT{year}_Nov16_ROW.xlsb`
- `klems_growth_accounts_basic.csv`

Main data use in the active WIOD workflow:

- outcome: `H_EMPE` from WIOD SEA
- robots: IFR robot intensity, lagged one year
- output control: `VA_QI` from WIOD SEA
- capital control: `K` from WIOD SEA by default, `CAP` as sensitivity
- macro control: Eurostat GDP growth
- institutions: ICTWSS baseline-frozen 1990-1995 measures

Country scope in the active WIOD workflow:

- the workflow starts from a broader **European candidate universe** (33 countries), not a hard EU-27 cutoff
- countries enter each model only if they survive the actual WIOD + IFR + ICTWSS + GDP variable requirements
- with the current data, `UK` and `NO` are the practical non-EU additions to the active regressions

**Excluded countries and reasons:**

- `CH` (Switzerland): the IFR extract contains disaggregated `robot_stock` at the sub-industry level, but `robot_wrkr_stock_95` (the per-worker normalisation used in the regression) is missing because IFR employment is zero for all Swiss manufacturing sub-industries. The raw robot counts exist but cannot be normalised consistently with other countries. CH will be revisited as a robustness exercise using alternative normalisation approaches.
- `CY` (Cyprus), `HR` (Croatia), `LU` (Luxembourg), `TR` (Turkey): the IFR data source provides only aggregate country-level robot figures for these countries, with no disaggregated manufacturing sub-industry breakdown. Since the identification strategy relies on within-country cross-industry variation in robot adoption, aggregate-only data is incompatible with the panel design.
- `IC` (Iceland): missing from the WIOD SEA release (fixed 43-country set), and IFR disaggregated data is also unavailable.
- `RU` (Russia): missing from the IFR extract, missing Eurostat GDP coverage, and missing all ICTWSS institutional baselines.

The full 33-country audit matrix is available at `results/exploration/wiod_feasibility/europe_country_availability_matrix.csv`.

## Methodology

This is a **country-industry-year fixed-effects panel study**.

The active WIOD design uses:

- country-industry fixed effects
- year fixed effects
- country-clustered headline inference
- wild cluster bootstrap p-values for the key interaction terms

### Eq. 1

```text
ln(H_EMPE)_ijt
  = β1 ln(Robots)_{ij,t-1}
  + γ1 ln(VA_QI)_{ijt}
  + γ2 ln(K)_{ijt}
  + γ3 GDPGrowth_it
  + α_ij + δ_t + ε_ijt
```

### Eq. 2

For a single institutional moderator `M_c`:

```text
ln(H_EMPE)_ijt
  = β1 ln(Robots)_{ij,t-1}
  + β2 [ln(Robots)_{ij,t-1} x M_c]
  + γ1 ln(VA_QI)_{ijt}
  + γ2 ln(K)_{ijt}
  + γ3 GDPGrowth_it
  + α_ij + δ_t + ε_ijt
```

Active moderator variants:

- `M_c = coord_pre_c`
- `M_c = adjcov_pre_c`
- `M_c = ud_pre_c`

### Eq. 2b

Exploratory joint coordination and union-density specification:

```text
ln(H_EMPE)_ijt
  = β1 ln(Robots)_{ij,t-1}
  + β2 [ln(Robots)_{ij,t-1} x coord_pre_c]
  + β3 [ln(Robots)_{ij,t-1} x ud_pre_c]
  + β4 [ln(Robots)_{ij,t-1} x coord_pre_c x ud_pre_c]
  + γ1 ln(VA_QI)_{ijt}
  + γ2 ln(K)_{ijt}
  + γ3 GDPGrowth_it
  + α_ij + δ_t + ε_ijt
```

`Eq. 2b` is an exploratory theory test, not part of the headline first-results bundle.

### Variable Legend

- `i`: country
- `j`: manufacturing industry
- `t`: year
- `ln(H_EMPE)_ijt`: log labour input from WIOD SEA
- `ln(Robots)_{ij,t-1}`: one-year-lagged log robot intensity from IFR
- `ln(VA_QI)_{ijt}`: log real value added from WIOD SEA
- `ln(K)_{ijt}`: log WIOD SEA capital proxy
- `GDPGrowth_it`: country-level GDP growth
- `coord_pre_c`: centered baseline bargaining coordination
- `adjcov_pre_c`: centered baseline adjusted bargaining coverage
- `ud_pre_c`: centered baseline union density
- `α_ij`: country-industry fixed effects
- `δ_t`: year fixed effects
- `ε_ijt`: idiosyncratic error term

### Identification Note

The institutional moderators are country-level and baseline-frozen. Their standalone main effects are therefore absorbed by the country-industry fixed effects. What is identified in `Eq. 2` and `Eq. 2b` is whether institutions change the slope on robot adoption.

## Folder Structure

```text
.
├── code/
│   ├── core/
│   │   ├── 09_build_wiod_panel.py
│   │   ├── 10_wiod_baseline.py
│   │   ├── 11_wiod_institution_moderation.py
│   │   └── 14_wiod_first_results.py
│   ├── secondary/
│   │   ├── 15_wiod_eq2b_hawk_dove.py
│   │   ├── 16_wiod_eq2_coord_on_eq2b_sample.py
│   │   ├── 17_wiod_common_sample_robustness.py
│   │   ├── archived/
│   │   └── legacy_klems/
│   ├── exploration/
│   │   └── wiod_feasibility/
│   ├── _paths.py
│   ├── _shared_utils.py
│   ├── _wiod_model_utils.py
│   └── _wiod_panel_utils.py
├── data/
├── results/
│   ├── core/
│   ├── secondary/
│   ├── exploration/
│   │   └── wiod_feasibility/
│   └── archive/
└── README.md
```

### What Lives Where

- `code/core/`: active WIOD mainline scripts
- `code/secondary/`: diagnostics, decomposition checks, and appendix-facing robustness scripts
- `code/secondary/legacy_klems/`: legacy KLEMS overlap workflow
- `code/exploration/wiod_feasibility/`: branch-history audits and feasibility scripts
- `results/core/`: active first-results outputs
- `results/secondary/`: Eq. 2b and diagnostic outputs
- `results/exploration/wiod_feasibility/`: saved feasibility and readiness artifacts
- `results/archive/`: archived legacy output snapshot from the pre-cleanup structure

## Active Workflow

### 1. Build the WIOD Panel

```bash
uv run python code/core/09_build_wiod_panel.py
```

This writes:

- `data/cleaned_data_wiod.csv`

### 2. Run the Main First-Results Bundle

```bash
uv run python code/core/14_wiod_first_results.py
```

This coordinated run executes:

- `Eq. 1` baseline
- `Eq. 2 coord`
- `Eq. 2 adjcov --sample common`
- `Eq. 2 ud`

Main review files:

- `results/core/wiod_first_results_summary.csv`
- `results/core/wiod_first_results_overview.md`
- `results/core/wiod_eq1_baseline_*`
- `results/core/primary_contribution_eq2_wiod_coord_*`
- `results/core/secondary_focal_eq2_wiod_adjcov_*`
- `results/core/reference_benchmark_eq2_wiod_ud_*`

Current first-results support after the Europe-candidate expansion:

- `Eq. 1`: 26 countries, 257 entities, 2571 observations
- `Eq. 2 coord`: 25 countries, 247 entities, 2500 observations
- `Eq. 2 adjcov`: 15 countries, 153 entities, 1685 observations
- `Eq. 2 ud`: 23 countries, 227 entities, 2356 observations

### 3. Run the Exploratory Eq. 2b Extension

```bash
uv run python code/exploration/wiod_feasibility/05_wiod_eq2b_hawk_dove_gate.py
uv run python code/secondary/15_wiod_eq2b_hawk_dove.py
```

This writes:

- `results/exploration/wiod_feasibility/wiod_eq2b_coord_ud_gate.md`
- `results/exploration/wiod_feasibility/wiod_eq2b_coord_ud_country_table.csv`
- `results/exploration/wiod_feasibility/wiod_eq2b_coord_ud_cell_counts.csv`
- `results/exploration/wiod_feasibility/wiod_eq2b_coord_ud_vif.csv`
- `results/exploration/wiod_feasibility/wiod_eq2b_coord_ud_scatter.png`
- `results/secondary/exploratory_wiod_eq2b_coord_ud_*`
- `results/secondary/wiod_eq2b_coord_ud_comparison.csv`

### 4. Run the Coord-Attenuation Diagnostic

```bash
uv run python code/secondary/16_wiod_eq2_coord_on_eq2b_sample.py
```

This isolates whether any change in the coord coefficient comes from:

- moving from the broader coord sample to the exact joint-modulator intersection, or
- adding `ud` and the three-way term to the model

Outputs:

- `results/secondary/diagnostic_wiod_eq2_coord_on_eq2b_sample_*`
- `results/secondary/wiod_eq2_coord_sample_decomposition.csv`

### 5. Run the Common-Sample Robustness Table

```bash
uv run python code/secondary/17_wiod_common_sample_robustness.py
```

This estimates `Eq. 1`, `Eq. 2 coord`, `Eq. 2 ud`, and `Eq. 2b` on the exact same `coord x ud` intersection sample.

Outputs:

- `results/secondary/wiod_common_sample_robustness.csv`
- `results/secondary/wiod_common_sample_robustness.md`

## Exploration And Branch-History Audits

Exploratory feasibility and readiness scripts live under:

- `code/exploration/wiod_feasibility/`

Their current documentation and retained outputs live under:

- `results/exploration/wiod_feasibility/`

These scripts are not part of the main thesis run sequence. They exist to document how the branch evolved and to preserve the feasibility evidence behind the WIOD pivot.

The exploration layer also carries the broader Europe-candidate audit that distinguishes:

- raw-country availability in the downloaded sources
- regression-usable countries in the active WIOD workflow

## Legacy KLEMS Workflow (was replaced with WIOD)

The KLEMS pipeline is kept only as a legacy / overlap robustness path.

Main scripts:

- `code/secondary/legacy_klems/00_run_pipeline.py`
- `code/secondary/legacy_klems/01_data_check.py`
- `code/secondary/legacy_klems/02_build_klems_panel.py`
- `code/secondary/legacy_klems/03_ictwss_moderator_triage.py`
- `code/secondary/legacy_klems/04_klems_baseline.py`
- `code/secondary/legacy_klems/05_klems_institution_moderation.py`
- `code/secondary/legacy_klems/06_klems_adjcov_moderation.py`

Legacy outputs now write to:

- `results/secondary/legacy_klems/`

## Control Comparability

The WIOD and KLEMS workflows are comparable in design, but not identical in measurement:

- `LAB_QI` vs `H_EMPE`: same labour-input family, different measure
- `VA_PYP` vs `VA_QI`: reasonably comparable real-output controls
- `CAP_QI` vs `K` or `CAP`: not directly equivalent

So the KLEMS-WIOD comparison should be read as a **joint measurement-and-controls robustness check**, not as a pure outcome-only swap.

## Results Storage

- active first results -> `results/core/`
- active diagnostics and appendix tables -> `results/secondary/`
- exploration/audit artifacts -> `results/exploration/wiod_feasibility/`
- migrated legacy output snapshot -> `results/archive/`
