# Trade Data Feasibility Audit

## What this branch tests

The current thesis panel (IFR × EU KLEMS × ICTWSS) has ~13–15 countries — a small N that limits
statistical power for institutional moderation tests. This branch asks a single question:

> **If we replace the KLEMS labour-input outcome with industry-level export data (Eurostat Comext,
> WIOD, or OECD TiVA), would the merged sample be meaningfully larger?**

The audit is purely a **sample-size feasibility check**. No regressions are run here.

### Decision threshold

| Scenario B countries | Verdict |
|----------------------|---------|
| ≥ 20 | **Proceed** — trade pivot worthwhile |
| 16–19 | **Marginal** — modest gain; evaluate carefully |
| ≤ 15 | **Not worth it** — gain over current ~13 is minimal |

---

## Directory structure

```
analysis/trade_feasibility/
├── 01_data_availability_audit.py   # Inventory IFR, ICTWSS, crosswalk; check for trade data
├── 02_merge_feasibility.py         # Simulate merges; count surviving obs per scenario
├── 03_sample_size_report.py        # Produce comparison table + country detail matrix
├── README.md                       # This file
└── output/                         # All CSV / TXT outputs (git-tracked)
    ├── ifr_country_industry_coverage.csv
    ├── ictwss_country_coverage.csv
    ├── ifr_nace_crosswalk.csv
    ├── trade_data_checklist.txt
    ├── merge_scenario_A_ifr_trade.csv
    ├── merge_scenario_B_ifr_trade_ictwss.csv
    ├── merge_scenario_C_restricted.csv
    ├── merge_scenario_D_current_baseline.csv
    ├── sample_size_comparison.csv
    └── country_detail_matrix.csv
```

---

## How to run

Run the three scripts in order from the repo root (or from this directory):

```bash
# From repo root
cd /path/to/msc-thesis

python analysis/trade_feasibility/01_data_availability_audit.py
python analysis/trade_feasibility/02_merge_feasibility.py
python analysis/trade_feasibility/03_sample_size_report.py
```

All scripts are self-contained. They degrade gracefully when `data/` files are absent:
- `01` documents what exists vs. what is missing; always produces the crosswalk CSV.
- `02` falls back to simulation (upper-bound estimates) when IFR/ICTWSS/trade data is absent.
- `03` reads the CSVs produced by `02` and renders the final comparison table.

### With actual data

Place the following files in `data/` before running:

| File | Source |
|------|--------|
| `IFR_karol.csv` | IFR robot database (already used by main pipeline) |
| `ictwss_institutions.csv` | ICTWSS database (already used by main pipeline) |
| `klems_growth_accounts_basic.csv` | EU KLEMS 2023 (already used; needed for Scenario D) |
| `wiod_sea.xlsx` or `oecd_tiva.csv` | See trade data download instructions below |

---

## Trade data download (manual steps required)

The `output/trade_data_checklist.txt` file (produced by script 01) contains full download
instructions. Summary:

### Option 1 — WIOD Socio-Economic Accounts (recommended start)
- URL: https://www.rug.nl/ggdc/valuechain/wiod/wiod-2016-release
- File: `SEA_Nov16.xlsx`
- Coverage: 43 countries, 2000–2014, NACE Rev.2-compatible
- Place as: `data/wiod_sea.xlsx`

### Option 2 — OECD TiVA 2023 (preferred for recency)
- URL: https://stats.oecd.org/ → Trade in Value Added
- Coverage: 75 countries, 2005–2020
- Place as: `data/oecd_tiva.csv`

---

## Scenarios modelled in `02_merge_feasibility.py`

| ID | Name | Join logic | Purpose |
|----|------|------------|---------|
| A | IFR × Trade | inner join on country × NACE × year | Upper bound; IFR is the constraint |
| B | IFR × Trade × ICTWSS (ud + coord) | A + left-join ICTWSS, keep has_ud + has_coord | Moderation model feasibility |
| C | IFR × Trade × ICTWSS (adjcov) | A + left-join ICTWSS, keep has_adjcov | Restricted-sample feasibility |
| D | Current: IFR × KLEMS × ICTWSS | Replicate existing `2-build_panel.py` merge | Benchmark for comparison |

---

## Key output files

| File | Content |
|------|---------|
| `output/sample_size_comparison.csv` | **Primary deliverable** — scenario-level N table |
| `output/country_detail_matrix.csv` | Per-country presence flags across all scenarios |
| `output/ifr_nace_crosswalk.csv` | IFR code → NACE Rev.2 mapping (from existing pipeline) |
| `output/ictwss_country_coverage.csv` | Moderator availability per country (1990–1995 baseline) |
| `output/trade_data_checklist.txt` | Download instructions for trade data |

---

## What this does NOT do

- No regressions (this is a feasibility audit only)
- Does not modify any existing code or data
- Does not download trade data automatically
- Does not assess the conceptual validity of trade exports as an outcome
  (that is a separate theoretical question for the thesis framework)

---

## Context

The main thesis empirical strategy uses:
- **Outcome:** log labour input (ln_hours from EU KLEMS `LAB_QI`)
- **Treatment:** log robot intensity lagged 1 year (`ln_robots_lag1`)
- **Moderators:** union density (`ud_pre_c`), coordination (`coord_pre_c`), coverage (`adjcov_pre_c`)
- **Controls:** log value added, log capital, GDP, unemployment
- **FE:** country–industry + year (two-way)
- **Sample:** ~13–15 countries (full), ~9–11 (common/adjcov)

The trade-pivot hypothesis is that replacing KLEMS (which restricts us to ~15 countries) with
trade export data (which covers ~25–27 EU countries) would expand the N sufficiently to improve
power for institutional moderation tests.

The answer hinges on IFR coverage: if IFR also only covers ~13–15 EU countries at the
2-digit NACE level, switching outcome variables will not expand the sample.
