# MSc Thesis: Robots, Labour Input, and Collective Bargaining Institutions

This repository contains the empirical code for an MSc thesis on how industrial robot adoption affects labour input in manufacturing, and how that relationship is conditioned by collective bargaining institutions.

- `Eq. 1`: baseline robot-labour relationship
- `Eq. 2`: single-moderator institutional moderation
- `Eq. 2b`: exploratory joint `coord x ud` Hawk-Dove extension

Machine-checked coherence of committed regression outputs under `results/core/`, `results/secondary/`, and `results/tables/` is described in [REPRODUCIBILITY.md](REPRODUCIBILITY.md) (steps 10–11: `_validate_artifacts.py` and `smoke_test.py`).

How result folders relate to each other (canonical vs archive vs exploration reruns): [results/README.md](results/README.md).

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

- outcome: `H_EMPE` from WIOD SEA → estimation column `ln_h_empe`
- robots: IFR **per-worker robot intensity** (`ln_robots_lag1`), lagged one year — headline operationalisation matches **Leibrecht et al. (2023)** (IFR robots-per-worker with a baseline-frozen denominator). **Appendix (GH [#29](https://github.com/erik-gunnarsson/msc-thesis/issues/29)):** lagged **log robot stock** (`ln_robot_stock_lag1`) for **Eq. 1** and **Eq. 2 coord** on the **CH-inclusive** sample in one table — [`results/tables/wiod_regression_table_appendix_robot_stock_ch_inclusive.{md,tex,csv}`](results/tables/wiod_regression_table_appendix_robot_stock_ch_inclusive.md) (cross-reference from **§6.2.2** and **§6.2.3**). *Graetz & Michaels (2018)* motivate capital-stock controls on the **level** equation; they are **not** the comparator for how robot **exposure** is scaled in the moderation design.
- output control: `VA_QI` from WIOD SEA → `ln_va_wiod_qi`
- capital control: `K` from WIOD SEA by default (`ln_k_wiod`), **capital compensation** `CAP` as sensitivity (`ln_capcomp_wiod`)
- macro control: Eurostat GDP growth
- institutions: ICTWSS country-level coordination, adjusted coverage, and union-density measures averaged over **1990–1995** and held fixed through the regression window (**2001–2014**). This **pre-sample institutional freeze** is the same benchmark as **Leibrecht et al. (2023)** (reverse causality: institutions are measured before robot adoption in the panel). **No alternative ICTWSS averaging windows** are used or planned as sensitivity checks—the thesis cites that reference for this timing choice instead of multiplying appendix variants.

Country scope in the active WIOD workflow:

- the workflow starts from a broader **European candidate universe** (33 countries), not a hard EU-27 cutoff
- countries enter each model only if they survive the actual WIOD + IFR + ICTWSS + GDP variable requirements
- with the current data, `UK` and `NO` are the practical non-EU additions to the active regressions

**Excluded countries and reasons:**

- `CH` (Switzerland): **Headline intensity panel:** IFR records **zero employment** across Swiss manufacturing sub-industries, so the **per-worker intensity denominator** behind `robot_wrkr_stock_95` is **undefined** — CH cannot enter on the **same intensity measure** as other countries (secondary-data **measurement constraint**, not discretionary trimming). Raw robot **stocks** exist; CH is included under **`ln_robot_stock_lag1`** in the **appendix table** [`wiod_regression_table_appendix_robot_stock_ch_inclusive.{md,tex,csv}`](results/tables/wiod_regression_table_appendix_robot_stock_ch_inclusive.md). Technical note: [`results/secondary/wiod_ch_alt_normalisation.md`](results/secondary/wiod_ch_alt_normalisation.md).
- `CY` (Cyprus), `HR` (Croatia), `LU` (Luxembourg), `TR` (Turkey): the IFR data source provides only aggregate country-level robot figures for these countries, with no disaggregated manufacturing sub-industry breakdown. Since the identification strategy relies on within-country cross-industry variation in robot adoption, aggregate-only data is incompatible with the panel design.
- `IC` (Iceland): missing from the WIOD SEA release (fixed 43-country set), and IFR disaggregated data is also unavailable.
- `RU` (Russia): missing from the IFR extract, missing Eurostat GDP coverage, and missing all ICTWSS institutional baselines.

The full 33-country audit matrix is committed under [`results/archive/exploration/wiod_feasibility/europe_country_availability_matrix.csv`](results/archive/exploration/wiod_feasibility/europe_country_availability_matrix.csv). Re-running exploration scripts writes fresh copies under `results/exploration/wiod_feasibility/` (see [results/README.md](results/README.md)).

## Methodology

This is a **country-industry-year fixed-effects panel study**.

The active WIOD design uses:

- country-industry fixed effects
- year fixed effects
- country-clustered headline inference
- wild cluster bootstrap p-values for the key interaction terms

Wild cluster bootstrap uses **999** repetitions by default (`--bootstrap-reps` on each model script). **`--bootstrap-seed`** (default **123**) is offset per `key_terms` row (`+0`, `+1`, …); Eq. 2 coordination interaction uses **effective seed 124**. Algorithm and thesis inference wording: [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) §6–7; audit: [`results/secondary/bootstrap_audit_eq2_coord.md`](results/secondary/bootstrap_audit_eq2_coord.md). While bootstrap runs, **tqdm** shows a progress bar per focal coefficient with elapsed time and rate estimates. Pass `--no-bootstrap-progress` on the model scripts or on `code/core/14_wiod_first_results.py` (which forwards the flag to child scripts) to suppress bars, for example in CI logs. Regenerated `run_metadata_*.json` files include `effective_bootstrap_seed_by_term`.

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
- `ln(H_EMPE)_ijt`: log labour input from WIOD SEA (column `ln_h_empe`)
- `ln(Robots)_{ij,t-1}`: one-year-lagged log robot intensity from IFR (column `ln_robots_lag1`)
- `ln(VA_QI)_{ijt}`: log real value added from WIOD SEA (column `ln_va_wiod_qi`)
- `ln(K)_{ijt}`: log WIOD SEA capital stock (column `ln_k_wiod`; compensation flow: `ln_capcomp_wiod`)
- `GDPGrowth_it`: country-level GDP growth
- `coord_pre_c`: centered baseline bargaining coordination
- `adjcov_pre_c`: centered baseline adjusted bargaining coverage
- `ud_pre_c`: centered baseline union density
- `α_ij`: country-industry fixed effects
- `δ_t`: year fixed effects
- `ε_ijt`: idiosyncratic error term

### Identification Note

The institutional moderators are country-level and baseline-frozen (ICTWSS **1990–1995** country means; timing benchmark from **Leibrecht et al. 2023**, not an alternate-window sensitivity grid). Their standalone main effects are therefore absorbed by the country-industry fixed effects. What is identified in `Eq. 2` and `Eq. 2b` is whether institutions change the slope on robot adoption.

### Thesis vs appendix specification defaults

**Headline (combined thesis tables, full calendar span):** WIOD SEA **capital stock `K`**. This keeps the labour-demand controls aligned with production-function-style benchmarking used in reference robot–labour work (e.g. Graetz & Michaels 2018 rely on **capital stock**, not capital compensation, in comparable specifications). **`CAP`** is a **flow** that mechanically shares variation with **value added**; headline specs therefore pair **`ln(VA_QI)`** with **`ln(K)`**, not with **`ln(CAP)`**.

**Appendix-only sensitivities** (outputs under [`results/secondary/robustness/`](results/secondary/robustness/), summary in [`results/secondary/robustness_overview_20260515.md`](results/secondary/robustness_overview_20260515.md); flags: `--exclude-years 2008 2009`, `--capital-proxy capcomp` on [`code/core/10_wiod_baseline.py`](code/core/10_wiod_baseline.py) / [`code/core/11_wiod_institution_moderation.py`](code/core/11_wiod_institution_moderation.py)):

- **Crisis-year drop:** exclude **2008–2009** to address GFC timing concerns. The focal Eq. 2 coordination interaction stays ~**0.012** (wild *p* virtually unchanged); present in an **appendix table** with a **one-sentence forward reference from §6.2.4** (placeholder **Table A.X** until final appendix numbering). Main tables stay on **2001–2014** because binding inference is **country cluster count**, not calendar length—trimming years does not fix few-cluster bias and can shift the bootstrap reference distribution.
- **`CAP` instead of `K`:** report as an **explicit sensitivity**. Under **`CAP`**, the coordination interaction **attenuates materially** relative to the **`K`** headline — prose must say so (see [`RESULTS_BRIEF.md`](results/RESULTS_BRIEF.md)). **`CAP`** remains informative precisely because it is constructed differently from **`K`**.

Locked placement decision: **GH [#30](https://github.com/erik-gunnarsson/msc-thesis/issues/30)**.

## Folder Structure

```text
.
├── code/
│   ├── core/
│   │   ├── 09_build_wiod_panel.py
│   │   ├── 10_wiod_baseline.py
│   │   ├── 11_wiod_institution_moderation.py
│   │   ├── 14_wiod_first_results.py
│   │   └── 18_wiod_academic_tables.py
│   ├── secondary/
│   │   ├── 15_wiod_eq2b_hawk_dove.py
│   │   ├── 16_wiod_eq2_coord_on_eq2b_sample.py
│   │   ├── 17_wiod_common_sample_robustness.py
│   │   ├── 19_wiod_jackknife.py
│   │   ├── 20_wiod_vif_audit.py
│   │   ├── _validate_artifacts.py
│   │   ├── smoke_test.py
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
│   ├── tables/
│   ├── secondary/
│   ├── exploration/
│   │   └── wiod_feasibility/
│   ├── _snapshot_YYYYMMDD/   # optional dated freezes (historical); prefer archive/ long-term
│   └── archive/
└── README.md
```

### What Lives Where

- `code/core/`: active WIOD mainline scripts
- `code/secondary/`: diagnostics, decomposition checks, and appendix-facing robustness scripts
- `code/secondary/legacy_klems/`: legacy KLEMS overlap workflow
- `code/exploration/wiod_feasibility/`: branch-history audits and feasibility scripts
- `results/core/`: active first-results outputs
- `results/tables/`: thesis-facing combined tables (from `18_wiod_academic_tables.py`)
- `results/secondary/`: Eq. 2b, diagnostics, robustness CSVs/MD (incl. jackknife, VIF audit)
- `results/exploration/wiod_feasibility/`: **live** output when you run `code/exploration/wiod_feasibility/*` (may be empty in a fresh clone until you rerun)
- `results/archive/`: retained historical bundles — incl. [`archive/exploration/wiod_feasibility/`](results/archive/exploration/wiod_feasibility/README.md) (feasibility artefacts) and legacy migration snapshots
- `results/_snapshot_YYYYMMDD/`: optional **point-in-time** copies for meetings or `--compare-snapshot`; not part of the day-to-day canonical layer — plan to treat as historical or relocate under `results/archive/` over time

## Active Workflow

For a copy-paste **re-run checklist** (commands, expected sample counts, script taxonomy), see [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

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

Default wild bootstrap size is **999** repetitions; override with `--bootstrap-reps N` if needed. Use `--no-bootstrap-progress` to disable tqdm bars during bootstrap (forwarded to `10_wiod_baseline.py` and `11_wiod_institution_moderation.py`).

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

### 2b. Build the Combined Regression Table (optional)

After the first-results bundle (and after step 3 if you need the Eq. 2b column), regenerate thesis-facing tables from the saved `*_key_terms.csv` artifacts:

```bash
uv run python code/core/18_wiod_academic_tables.py
uv run python code/core/18_wiod_academic_tables.py --star-source cluster
```

The **thesis-facing inference standard** is **wild-cluster bootstrap** stars on robot-related terms, with country-clustered standard errors in parentheses (`results/tables/wiod_regression_table_combined.{md,tex,csv}`). The second command is **optional**: it writes an **inference-robustness** variant with stars from asymptotic country-clustered *p*-values (`results/secondary/inference_robustness/wiod_regression_table_combined_clusterstars.{md,tex,csv}`) — use appendix / §6.2 comparisons only; it is **not** a co-equal headline table. These scripts do not re-estimate models.

**Appendix — CH-inclusive log robot stock (GH #29)** — same structured artefacts as the main table builder, but pulls `robust_robotstock_*` from `results/secondary/robustness/`:

```bash
uv run python code/core/18_wiod_academic_tables.py --appendix-robot-stock-ch-inclusive-only
uv run python code/core/18_wiod_academic_tables.py --appendix-robot-stock-ch-inclusive-only --star-source cluster
```

Writes `results/tables/wiod_regression_table_appendix_robot_stock_ch_inclusive.{md,tex,csv}` (wild-bootstrap stars) and `results/secondary/inference_robustness/wiod_regression_table_appendix_robot_stock_ch_inclusive_clusterstars.{md,tex,csv}`. Regenerate the underlying estimates first if needed:

```bash
uv run python code/core/10_wiod_baseline.py --robot-regressor stock \
  --output-dir results/secondary/robustness --prefix-override robust_robotstock_eq1_baseline
uv run python code/core/11_wiod_institution_moderation.py --moderator coord --robot-regressor stock \
  --output-dir results/secondary/robustness --prefix-override robust_robotstock_eq2_coord
```

### 3. Run the Exploratory Eq. 2b Extension

```bash
uv run python code/exploration/wiod_feasibility/05_wiod_eq2b_hawk_dove_gate.py
uv run python code/secondary/15_wiod_eq2b_hawk_dove.py
```

The Eq. 2b estimation uses the same bootstrap defaults as the core scripts: **999** repetitions; pass `--no-bootstrap-progress` to disable tqdm during wild bootstrap.

This writes (gate script → `results/exploration/wiod_feasibility/`; estimation → `results/secondary/`):

- `results/exploration/wiod_feasibility/wiod_eq2b_coord_ud_gate.md`
- `results/exploration/wiod_feasibility/wiod_eq2b_coord_ud_country_table.csv`
- `results/exploration/wiod_feasibility/wiod_eq2b_coord_ud_cell_counts.csv`
- `results/exploration/wiod_feasibility/wiod_eq2b_coord_ud_vif.csv`
- `results/exploration/wiod_feasibility/wiod_eq2b_coord_ud_scatter.png`
- `results/secondary/exploratory_wiod_eq2b_coord_ud_*`
- `results/secondary/wiod_eq2b_coord_ud_comparison.csv`

Committed copies of the gate bundle also live under [`results/archive/exploration/wiod_feasibility/`](results/archive/exploration/wiod_feasibility/README.md) if `results/exploration/` is not populated.

### 4. Run the Coord-Attenuation Diagnostic

```bash
uv run python code/secondary/16_wiod_eq2_coord_on_eq2b_sample.py
```

Supports `--bootstrap-reps` (default **999**) and `--no-bootstrap-progress`.

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

Supports `--bootstrap-reps` (default **999**) and `--no-bootstrap-progress`.

This estimates `Eq. 1`, `Eq. 2 coord`, `Eq. 2 ud`, and `Eq. 2b` on the exact same `coord x ud` intersection sample.

Outputs:

- `results/secondary/wiod_common_sample_robustness.csv`
- `results/secondary/wiod_common_sample_robustness.md`

### 6. Jackknife and VIF audit (optional but documented)

```bash
uv run python code/secondary/19_wiod_jackknife.py
uv run python code/secondary/20_wiod_vif_audit.py
```

Writes `results/secondary/wiod_jackknife_eq2_coord.{csv,md}` and `results/secondary/wiod_vif_audit.{csv,md}`. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for ordering relative to the headline bundle.

### 7. Validate committed artifacts

```bash
uv run python code/secondary/_validate_artifacts.py
```

Optional snapshot diff: `uv run python code/secondary/_validate_artifacts.py --compare-snapshot results/_snapshot_YYYYMMDD/run_manifest.json`

### 8. CI smoke imports (no data)

```bash
uv run python code/secondary/smoke_test.py
```

## Exploration And Branch-History Audits

Exploratory feasibility and readiness scripts live under:

- `code/exploration/wiod_feasibility/`

Retained (committed) exploration outputs live under **`results/archive/exploration/wiod_feasibility/`**. Re-running scripts repopulates **`results/exploration/wiod_feasibility/`** (same filenames; see [results/README.md](results/README.md)).

These scripts are not part of the main thesis run sequence. They exist to document how the branch evolved and to preserve the feasibility evidence behind the WIOD pivot.

The exploration layer also carries the broader Europe-candidate audit that distinguishes:

- raw-country availability in the downloaded sources
- regression-usable countries in the active WIOD workflow

## Legacy KLEMS Workflow (was replaced with WIOD) May For Robustness Tests

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

- headline regression artefacts → `results/core/`
- thesis tables → `results/tables/`; cluster-stars siblings → `results/secondary/inference_robustness/`
- diagnostics, Eq. 2b estimates, jackknife, VIF → `results/secondary/` (robustness reruns often under `results/secondary/robustness/`)
- exploration gate outputs (when rerun) → `results/exploration/wiod_feasibility/`
- retained exploration + legacy snapshots → `results/archive/`
- optional dated freezes → `results/_snapshot_YYYYMMDD/` (historical; see [results/README.md](results/README.md))
