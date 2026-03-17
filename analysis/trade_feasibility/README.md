# Trade Data Feasibility Audit

This directory contains an isolated sample-size audit for a trade-data pivot.
It replaces the current KLEMS outcome with WIOD-derived gross exports and measures how many country-industry-year observations survive under several merge scenarios before any regression work.

## What This Tests

- Whether `IFR x WIOD` materially expands the usable country sample relative to the current `IFR x KLEMS x ICTWSS` pipeline.
- Whether institutional-moderation models remain feasible once `ud`, `coord`, and `adjcov` coverage is applied.
- How much the current repo's raw IFR-to-NACE many-to-one mapping inflates entity counts relative to a collapsed `country x nace_r2_code x year` view.

## Active Data Sources

- IFR: `data/IFR_karol.csv`
- ICTWSS: `data/ictwss_institutions.csv`
- Current baseline comparison: `data/cleaned_data.csv`
- WIOD trade source: `data/WIOTS_in_EXCEL/WIOT{year}_Nov16_ROW.xlsb` for 2000-2014

The WIOD values are treated as current-price millions of USD.
Gross exports are computed from each origin industry row as sales to foreign users:

- foreign intermediate demand
- plus foreign final demand

The final `GO` / total-output column is excluded from the export sum.

## How To Run

Run the scripts in order from the repo root:

```bash
python analysis/trade_feasibility/01_data_availability_audit.py
python analysis/trade_feasibility/02_merge_feasibility.py
python analysis/trade_feasibility/03_sample_size_report.py
```

If your environment cannot read `.xlsb` files, install:

```bash
pip install pyxlsb
```

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

## Notes

- Greece is harmonized as `GR -> EL` inside this audit, and the country-detail output flags that the current baseline pipeline drops Greece because it does not apply that harmonization before joining to KLEMS / ICTWSS.
- Headline feasibility counts use WIOD's actual overlap window, 2000-2014.
- The current baseline comparison remains tied to the repo's existing `cleaned_data.csv`, which still includes UK.
