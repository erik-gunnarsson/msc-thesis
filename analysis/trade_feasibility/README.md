# Trade Data Feasibility Audit

This directory contains an isolated audit of a trade-data pivot for the thesis.
Phase 1 replaces the current KLEMS labour-input outcome with WIOD-derived gross exports and measures how many country-industry-year observations survive under several merge scenarios.
Phase 2 extends that work into a regression-readiness audit by adding WIOD Socio-Economic Accounts (SEA) controls and checking the exact sample support for each planned model and robustness specification.

## What This Tests

- Whether `IFR x WIOD` materially expands the usable country sample relative to the current `IFR x KLEMS x ICTWSS` pipeline.
- Whether the main institutional-moderation models remain feasible once `ud`, `coord`, and `adjcov` coverage is applied.
- Whether WIOD SEA can replace KLEMS-based industry controls without collapsing the sample back to the old overlap.
- Which robustness checks still fail because of coverage limits, balanced-panel attrition, or missing macro controls.

## Active Data Sources

- IFR: `data/IFR_karol.csv`
- ICTWSS: `data/ictwss_institutions.csv`
- Current baseline comparison: `data/cleaned_data.csv`
- WIOD trade tables: `data/WIOTS_in_EXCEL/WIOT{year}_Nov16_ROW.xlsb` for 2000-2014
- WIOD SEA controls: `data/WIOTS_SEA/Socio_Economic_Accounts.xlsx`
- Eurostat GDP: `data/eurostata_gdp_nama_10_gdp.csv`
- Eurostat unemployment: `data/eurostat_employment_une_rt_a.csv`

The WIOD trade values are treated as current-price millions of USD.
In the current implementation, gross exports are computed as `total output - domestic use`, which is equivalent to sales to foreign users in the WIOT structure.

The WIOD SEA audit uses current-price `VA`, `CAP`, `GO`, and `H_EMPE`.
For the regression-ready panel, the control variables are `ln_va_sea` and `ln_cap_sea`.

## How To Run

Run the scripts in order from the repo root:

```bash
python analysis/trade_feasibility/01_data_availability_audit.py
python analysis/trade_feasibility/02_merge_feasibility.py
python analysis/trade_feasibility/03_sample_size_report.py
python analysis/trade_feasibility/regression_ready_audit.py
```

If your environment cannot read `.xlsb` files, install:

```bash
pip install pyxlsb
```

## Phase 1 Findings

- `A: IFR x WIOD (max)` = 24 countries, 258 entities, 3870 observations, `2000-2014`
- `B: IFR x WIOD x ICTWSS (ud+coord)` = 21 countries, 225 entities, 3375 observations, `2000-2014`
- `C: IFR x WIOD x ICTWSS (adjcov)` = 14 countries, 148 entities, 2220 observations, `2000-2014`
- `D: Current (IFR x KLEMS x ICTWSS)` = 14 countries, 287 raw IFR entities, 4622 observations, `1995-2019`

This confirms that a trade pivot materially expands the country sample for the main `ud + coord` moderation models.

## Phase 2 Findings

The regression-ready audit uses the thesis-consistent robot regressor construction:

- `ln_robots = log(robot_wrkr_stock_95)` after replacing zeroes with missing
- `ln_robots_lag1` created by entity lag

Headline results:

- WIOD SEA is complete for all 27 EU countries across all 19 WIOD manufacturing sectors for `VA`, `CAP`, `GO`, and `H_EMPE` over `2000-2014`
- The SEA-backed base panel is 24 countries, 236 entities, and 2283 observations over `2001-2014`
- Main models all pass the `>=20 countries` threshold
- Restricted `adjcov` models pass the `>=14 countries` threshold
- Overall verdict: `CONDITIONALLY READY`

Main model support:

- `EQ1`: 24 countries, 2283 observations
- `EQ1_GDP`: 24 countries, 2283 observations
- `EQ2_UD`: 21 countries, 2068 observations
- `EQ2_COORD`: 23 countries, 2212 observations
- `EQ3`: 24 countries, 2283 observations
- `EQ4_UD`: 21 countries, 2068 observations
- `EQ4_COORD`: 23 countries, 2212 observations
- `EQ2_ADJCOV`: 14 countries, 1535 observations
- `EQ4_ADJCOV`: 14 countries, 1535 observations

Remaining constraints:

- `ROB_COMMON_UD` fails the restricted threshold at 13 countries
- `ROB_BALANCED` fails badly at 7 countries
- Unemployment is not a viable robustness control on the base-panel support: 101 missing country-years out of 255, or 39.6% missing
- Bucket coverage is not uniform within the 21-country `ud + coord` set:
  - Bucket 1: 20 countries
  - Bucket 2: 19 countries
  - Bucket 3: 19 countries
  - Bucket 4: 20 countries
  - Bucket 5: 21 countries

Interpretation:

- The trade pivot is workable for the planned main regressions.
- WIOD SEA solves the old KLEMS control bottleneck.
- The branch is not fully "run everything blindly" ready because a few robustness designs still trigger unacceptable sample attrition.

## Key Outputs

- `output/ifr_country_year_coverage.csv`
- `output/ifr_country_industry_coverage.csv`
- `output/ictwss_country_coverage.csv`
- `output/ifr_nace_crosswalk.csv`
- `output/wiod_to_nace_crosswalk.csv`
- `output/wiod_trade_panel.csv`
- `output/merge_scenario_A_ifr_trade.csv`
- `output/merge_scenario_B_ifr_trade_ictwss.csv`
- `output/merge_scenario_C_restricted.csv`
- `output/merge_scenario_D_current_baseline.csv`
- `output/sample_size_comparison.csv`
- `output/country_detail_matrix.csv`
- `output/sea_coverage_matrix.csv`
- `output/sample_attrition_table.csv`
- `output/bucket_coverage_detail.csv`
- `output/unemployment_feasibility.csv`
- `output/klems_legacy_feasibility.csv`
- `output/regression_ready_summary.txt`

## Notes

- Greece is harmonized as `GR -> EL` inside this audit, and the country-detail output flags that the current baseline pipeline drops Greece because it does not apply that harmonization before joining to KLEMS and ICTWSS.
- Headline feasibility counts use WIOD's actual overlap window, `2000-2014`.
- The regression-ready base panel starts in `2001` because of the one-period robot lag.
- The current baseline comparison remains tied to the repo's existing `cleaned_data.csv`, which still includes UK.
