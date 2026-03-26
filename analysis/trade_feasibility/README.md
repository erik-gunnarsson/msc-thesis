# Trade Feasibility And WIOD Labour Audit

This directory began as an isolated audit of a trade-data pivot for the thesis.
Phase 1 tested a temporary `IFR x WIOD exports x ICTWSS` merge to answer the sample-size question quickly.
The current branch direction is now broader and clearer: keep **labour input** as the dependent-variable family, use **WIOD SEA** to expand country coverage, and treat WIOD trade as a historical comparison input rather than the active thesis outcome.

In practice, this directory now contains three layers of work:

- Phase 1: trade-feasibility and overlap audit
- Phase 2: regression-readiness audit with WIOD SEA controls
- Phase 3: WIOD labour design comparison, which helped show that **Eq. 2 is the headline contribution** and that **bucket models should be treated as exploratory / appendix material**

## What This Tests

- Whether `IFR x WIOD` materially expands the usable country sample relative to the current `IFR x KLEMS x ICTWSS` pipeline.
- Whether the main institutional-moderation models remain feasible once `coord`, `adjcov`, and `ud` coverage is applied.
- Whether WIOD SEA can replace KLEMS-based industry controls without collapsing the sample back to the old overlap.
- Whether a WIOD **labour** panel can support the mainline Eq. 1-2 workflow while keeping bucket heterogeneity available as exploratory material.
- Whether control-variable comparability and country-level inference need to change once the thesis moves from KLEMS to WIOD.

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

The active WIOD labour mainline uses:

- Outcome: `H_EMPE` -> `ln_h_empe`
- Output control: `VA_QI` -> `ln_va_wiod_qi`
- Default capital proxy: `K` -> `ln_k_wiod`
- Sensitivity capital proxy: `CAP` -> `ln_capcomp_wiod`

This keeps the thesis focused on **robots -> labour input**, not robots -> exports.

Institutional hierarchy in the active thesis workflow:

- `coord`: primary focal channel
- `adjcov`: secondary focal channel with restricted sample
- `ud`: reference benchmark only

## How To Run

Run the audit scripts in order from the repo root:

```bash
python analysis/trade_feasibility/01_data_availability_audit.py
python analysis/trade_feasibility/02_merge_feasibility.py
python analysis/trade_feasibility/03_sample_size_report.py
python analysis/trade_feasibility/regression_ready_audit.py
python analysis/trade_feasibility/04_wiod_labour_design_comparison.py
```

Build the reusable WIOD labour panel and run the WIOD model scripts from the repo root:

```bash
python code/09_build_wiod_panel.py
python code/10_wiod_baseline.py
python code/11_wiod_institution_moderation.py --moderator coord
python code/11_wiod_institution_moderation.py --moderator adjcov --sample common
python code/11_wiod_institution_moderation.py --moderator ud
python code/12_wiod_bucket_models.py --mode eq3
python code/12_wiod_bucket_models.py --mode eq4 --moderator coord
python code/12_wiod_bucket_models.py --mode eq4 --moderator adjcov --sample common
python code/12_wiod_bucket_models.py --mode eq4 --moderator ud
```

If your environment cannot read `.xlsb` files, install:

```bash
pip install pyxlsb
```

## Phase 1 Findings

- `A: IFR x WIOD (max)` = 24 countries, 258 entities, 3870 observations, `2000-2014`
- `B: IFR x WIOD x ICTWSS (coord+ud)` = 21 countries, 225 entities, 3375 observations, `2000-2014`
- `C: IFR x WIOD x ICTWSS (adjcov)` = 14 countries, 148 entities, 2220 observations, `2000-2014`
- `D: Current (IFR x KLEMS x ICTWSS)` = 14 countries, 287 raw IFR entities, 4622 observations, `1995-2019`

This confirmed that WIOD-side coverage is real and large enough to justify deeper follow-up work.

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
- `EQ2_COORD`: 23 countries, 2212 observations
- `EQ2_ADJCOV`: 14 countries, 1535 observations
- `EQ2_UD`: 21 countries, 2068 observations
- `EQ3`: 24 countries, 2283 observations
- `EQ4_COORD`: 23 countries, 2212 observations
- `EQ4_ADJCOV`: 14 countries, 1535 observations
- `EQ4_UD`: 21 countries, 2068 observations

Remaining constraints:

- `ROB_COMMON_UD` fails the restricted threshold at 13 countries
- `ROB_BALANCED` fails badly at 7 countries
- Unemployment is not a viable robustness control on the base-panel support: 101 missing country-years out of 255, or 39.6% missing
- Bucket coverage is not uniform within the shared `coord + ud` availability set:
  - Bucket 1: 20 countries
  - Bucket 2: 19 countries
  - Bucket 3: 19 countries
  - Bucket 4: 20 countries
  - Bucket 5: 21 countries

Interpretation:

- WIOD SEA solves the old KLEMS control bottleneck.
- The branch is ready for the planned main WIOD labour models.
- The branch is not fully "run everything blindly" ready because a few robustness designs still trigger unacceptable sample attrition.

## Phase 3 Findings: WIOD Labour Design Comparison

The current recommended framing is a **WIOD labour mainline**, not an exports-outcome pivot.

Headline support with the default WIOD control set (`ln_va_wiod_qi`, `ln_k_wiod`, `gdp_growth`) is:

- `BASE_H_EMPE`: 24 countries, 236 entities, 2283 observations
- `EQ4_COORD_BUCKET`: 23 countries, 226 entities, 2212 observations
- `EQ4_ADJCOV_BUCKET`: 14 countries, 148 entities, 1535 observations
- `EQ4_UD_BUCKET`: 21 countries, 206 entities, 2068 observations
- `EQ5A_EXPOSURE`: 24 countries, 236 entities, 2283 observations
- `EQ5B_COORD_EXPOSURE`: 23 countries, 226 entities, 2212 observations
- `EQ5B_ADJCOV_EXPOSURE`: 14 countries, 148 entities, 1535 observations
- `EQ5B_UD_EXPOSURE`: 21 countries, 206 entities, 2068 observations

This means the pooled WIOD **bucket** models are estimable and clear the main-country threshold.
Key concern shows up not as identification failure but as **thin bucket support in some contrasts**:

- Bucket 1: 20 countries
- Bucket 2: 19 countries
- Bucket 3: 19 countries
- Bucket 4: 20 countries
- Bucket 5: 21 countries

So the bucket approach can remain in the thesis, but it should be framed as **exploratory / appendix material** rather than the main confirmatory claim.

The exposed/sheltered comparison was useful during the design audit, but it is no longer part of the active thesis workflow. Historical comparison outputs remain available in this directory. In the shared `coord + ud` availability support:

- `exposed`: 20 countries, 110 entities, 1138 observations
- `sheltered`: 21 countries, 96 entities, 930 observations

Control comparability conclusions:

- `LAB_QI` vs `H_EMPE`: same labour-input family, different measurement
- `VA_PYP` vs `VA_QI`: reasonably comparable real-output controls
- `CAP_QI` vs `K` / `CAP`: not directly comparable

This means the KLEMS-WIOD comparison should be presented as a **joint measure-and-controls robustness check**, not as a pure outcome-only swap.

Inference plan for the WIOD panel:

- Headline clustering: **country**
- Headline p-values for key institution interactions: **wild cluster bootstrap**
- Secondary robustness: entity-clustered and Driscoll-Kraay estimates

The active WIOD scripts implement that structure, with country-clustered results as the default headline output and Eq. 2 treated as the primary contribution.

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
- `output/wiod_labour_model_support.csv`
- `output/wiod_bucket_coverage.csv`
- `output/wiod_exposure_balance.csv`
- `output/wiod_control_comparability.csv`
- `output/wiod_model_comparison_skeleton.csv`
- `output/wiod_heterogeneity_coefficients.csv`
- `output/wiod_vs_kelms_note.md`
- `data/cleaned_data_wiod.csv`
- `outputs/wiod_eq1_*`
- `outputs/primary_contribution_eq2_wiod_coord_*`
- `outputs/secondary_focal_eq2_wiod_adjcov_*`
- `outputs/reference_benchmark_eq2_wiod_ud_*`
- `outputs/exploratory_wiod_eq3_*`
- `outputs/exploratory_focal_wiod_eq4_coord_*`
- `outputs/exploratory_secondary_wiod_eq4_adjcov_*`
- `outputs/exploratory_reference_wiod_eq4_ud_*`

## Notes

- Greece is harmonized as `GR -> EL` inside this audit, and the country-detail output flags that the current baseline pipeline drops Greece because it does not apply that harmonization before joining to KLEMS and ICTWSS.
- Headline feasibility counts use WIOD's actual overlap window, `2000-2014`.
- The regression-ready base panel starts in `2001` because of the one-period robot lag.
- The current baseline comparison remains tied to the repo's existing `cleaned_data.csv`, which still includes UK.
- The WIOD model scripts default to `K` as the capital proxy and keep `CAP` as a sensitivity specification.
- `code/13_wiod_exposure_models.py` is retained only as an archived comparison script and is not part of the active thesis workflow.
