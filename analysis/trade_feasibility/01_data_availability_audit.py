"""
01_data_availability_audit.py
==============================================
Inventory what we have and what we need — WITHOUT downloading new data.

Outputs (all saved to ./output/):
  ifr_country_industry_coverage.csv  — country × year coverage matrix for IFR
  ictwss_country_coverage.csv        — moderator availability by country
  ifr_nace_crosswalk.csv             — IFR industry code → NACE Rev.2 mapping
  trade_data_checklist.txt           — instructions / status for trade data

Run:
    python 01_data_availability_audit.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]          # msc-thesis/
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants — mirrored exactly from code/2-build_panel.py
# ---------------------------------------------------------------------------
EU_ISO2 = {
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES",
    "FI", "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV",
    "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK", "UK",
}

# EU-27 (current members, Eurostat ISO2 codes — EL for Greece, no UK)
EU_27_ISO2 = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE",
    "FI", "FR", "DE", "EL", "HU", "IE", "IT", "LV",
    "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE",
}

EU_27_NAMES = {
    "AT": "Austria",      "BE": "Belgium",      "BG": "Bulgaria",
    "HR": "Croatia",      "CY": "Cyprus",       "CZ": "Czechia",
    "DK": "Denmark",      "EE": "Estonia",      "FI": "Finland",
    "FR": "France",       "DE": "Germany",      "EL": "Greece",
    "HU": "Hungary",      "IE": "Ireland",      "IT": "Italy",
    "LV": "Latvia",       "LT": "Lithuania",    "LU": "Luxembourg",
    "MT": "Malta",        "NL": "Netherlands",  "PL": "Poland",
    "PT": "Portugal",     "RO": "Romania",      "SK": "Slovakia",
    "SI": "Slovenia",     "ES": "Spain",        "SE": "Sweden",
    # UK kept for reference (historical IFR coverage)
    "UK": "United Kingdom",
}

# IFR industry_code → NACE Rev.2 — exactly from code/2-build_panel.py
IFR_TO_NACE = {
    "10-12":  "C10-C12",
    "13-15":  "C13-C15",
    "16":     "C16-C18",
    "17-18":  "C16-C18",
    "19":     "C19",
    "19-22":  "C20-C21",
    "20":     "C20-C21",
    "20-21":  "C20-C21",
    "20-23":  "C20-C21",
    "21":     "C21",
    "22":     "C22-C23",
    "23":     "C22-C23",
    "24":     "C24-C25",
    "24-25":  "C24-C25",
    "25":     "C24-C25",
    "26":     "C26-C27",
    "26-27":  "C26-C27",
    "27":     "C26-C27",
    "28":     "C28",
    "29":     "C29-C30",
    "29-30":  "C29-C30",
    "30":     "C29-C30",
    "D":      "C",          # Aggregate manufacturing — excluded from bucket models
    "D_other":"C31-C33",
}

# NACE groups that enter the 5-bucket operational model (excludes "C" aggregate)
NACE_OPERATIONAL = [
    "C10-C12", "C13-C15", "C16-C18", "C19", "C20-C21",
    "C22-C23", "C24-C25", "C26-C27", "C28", "C29-C30", "C31-C33",
]

ISO3_TO_ISO2 = {
    "AUT": "AT", "BEL": "BE", "BGR": "BG", "HRV": "HR", "CYP": "CY", "CZE": "CZ",
    "DNK": "DK", "EST": "EE", "FIN": "FI", "FRA": "FR", "DEU": "DE", "GRC": "EL",
    "HUN": "HU", "IRL": "IE", "ITA": "IT", "LVA": "LV", "LTU": "LT", "LUX": "LU",
    "MLT": "MT", "NLD": "NL", "POL": "PL", "PRT": "PT", "ROU": "RO", "SVK": "SK",
    "SVN": "SI", "ESP": "ES", "SWE": "SE", "GBR": "UK",
}

ICTWSS_CANDIDATES = ["Coord", "AdjCov", "UD", "Wstat", "WC", "SPA_signed"]
MAINLINE_MODERATORS = ["UD", "Coord", "AdjCov"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def banner(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def load_csv_safe(path: Path) -> pd.DataFrame | None:
    """Return DataFrame or None if file not found."""
    if not path.exists():
        print(f"  [MISSING] {path.relative_to(REPO_ROOT)}")
        return None
    df = pd.read_csv(path, low_memory=False)
    print(f"  [LOADED]  {path.relative_to(REPO_ROOT)}  ({len(df):,} rows × {len(df.columns)} cols)")
    return df


# ---------------------------------------------------------------------------
# 2a. IFR coverage audit
# ---------------------------------------------------------------------------

def audit_ifr() -> pd.DataFrame | None:
    banner("2a. IFR Robot Data — Country × Year Coverage")

    ifr_raw = load_csv_safe(DATA_DIR / "IFR_karol.csv")
    if ifr_raw is None:
        print("  → IFR data not found. Coverage audit skipped.")
        print("    Expected file: data/IFR_karol.csv")
        print("    Country codes used in existing pipeline: ISO2 (e.g. DE, FR, IT)")
        print(f"    EU_ISO2 set has {len(EU_ISO2)} countries:\n    {sorted(EU_ISO2)}")
        return None

    # Normalise
    ifr = ifr_raw.copy()
    ifr["year"] = pd.to_numeric(ifr["year"], errors="coerce")
    ifr = ifr[ifr["country_code"].isin(EU_ISO2)]
    ifr = ifr[ifr["industry_code"].isin(IFR_TO_NACE.keys())]
    ifr = ifr[ifr["year"].between(1995, 2019)]

    # Map to NACE
    ifr["nace_r2_code"] = ifr["industry_code"].map(IFR_TO_NACE)
    ifr_oper = ifr[ifr["nace_r2_code"].isin(NACE_OPERATIONAL)]

    # --- Country × Year matrix (cells = n NACE groups with data) ---
    year_range = sorted(ifr_oper["year"].dropna().unique().astype(int))
    countries_in_ifr = sorted(ifr_oper["country_code"].unique())

    coverage_rows = []
    for ctry in countries_in_ifr:
        row = {"country": ctry, "country_name": EU_27_NAMES.get(ctry, ctry)}
        sub = ifr_oper[ifr_oper["country_code"] == ctry]
        for yr in year_range:
            n_nace = sub[sub["year"] == yr]["nace_r2_code"].nunique()
            row[str(yr)] = n_nace if n_nace > 0 else 0
        coverage_rows.append(row)

    coverage_matrix = pd.DataFrame(coverage_rows)
    out_path = OUTPUT_DIR / "ifr_country_industry_coverage.csv"
    coverage_matrix.to_csv(out_path, index=False)
    print(f"\n  Countries in IFR (EU subsample): {len(countries_in_ifr)}")
    print(f"  Year range: {min(year_range)}–{max(year_range)}")
    print(f"  Countries: {countries_in_ifr}")
    print(f"\n  Country × Year coverage matrix (cells = N NACE groups with robot data):")
    print(coverage_matrix.to_string(index=False))
    print(f"\n  → Saved: {out_path.relative_to(REPO_ROOT)}")

    # --- Country × NACE summary (collapsed across years) ---
    nace_coverage = (
        ifr_oper.groupby(["country_code", "nace_r2_code"])["year"]
        .count()
        .rename("n_years")
        .reset_index()
    )
    pivot_nace = nace_coverage.pivot(
        index="country_code", columns="nace_r2_code", values="n_years"
    ).fillna(0).astype(int)
    pivot_nace.index.name = "country"
    print(f"\n  Country × NACE industry coverage (values = number of years with robot data):")
    print(pivot_nace.to_string())

    return ifr_oper


# ---------------------------------------------------------------------------
# 2b. ICTWSS coverage audit
# ---------------------------------------------------------------------------

def audit_ictwss() -> pd.DataFrame | None:
    banner("2b. ICTWSS Institutional Data — Moderator Coverage")

    ictwss_raw = load_csv_safe(DATA_DIR / "ictwss_institutions.csv")
    if ictwss_raw is None:
        print("  → ICTWSS data not found. Coverage audit skipped.")
        print("    Expected file: data/ictwss_institutions.csv")
        print("    Country codes in raw file: ISO3 (AUT, DEU, ...) mapped to ISO2")
        print("    Baseline freeze: 1990–1995 averages per country")
        _print_ictwss_known_coverage()
        return None

    # Normalise
    ictwss = ictwss_raw.copy()
    ictwss["country_code"] = ictwss["iso3"].map(ISO3_TO_ISO2)
    ictwss = ictwss[ictwss["country_code"].isin(EU_ISO2)]

    for col in ICTWSS_CANDIDATES:
        if col in ictwss.columns:
            ictwss[col] = pd.to_numeric(ictwss[col], errors="coerce")
            ictwss.loc[ictwss[col] == -99, col] = np.nan

    # Baseline 1990–1995
    base = ictwss[ictwss["year"].between(1990, 1995)]

    def _safe_mean(s):
        v = pd.to_numeric(s, errors="coerce")
        return v.dropna().mean() if v.notna().any() else np.nan

    agg = {col: (col, _safe_mean) for col in ICTWSS_CANDIDATES if col in base.columns}
    baseline = base.groupby("country_code").agg(**agg).reset_index()
    baseline.columns = ["country_code"] + [c.lower() + "_pre" for c in ICTWSS_CANDIDATES if c in base.columns]

    # Build coverage table
    rows = []
    for _, row in baseline.iterrows():
        entry = {
            "country_iso2": row["country_code"],
            "country_name": EU_27_NAMES.get(row["country_code"], row["country_code"]),
        }
        for col in MAINLINE_MODERATORS:
            lc = col.lower() + "_pre"
            if lc in baseline.columns:
                entry[f"{col.lower()}_available"] = int(pd.notna(row.get(lc, np.nan)))
                entry[f"{col.lower()}_value"]     = round(row.get(lc, np.nan), 3) if pd.notna(row.get(lc, np.nan)) else np.nan
        rows.append(entry)

    coverage = pd.DataFrame(rows).sort_values("country_iso2").reset_index(drop=True)
    out_path = OUTPUT_DIR / "ictwss_country_coverage.csv"
    coverage.to_csv(out_path, index=False)

    # Summary
    for col in MAINLINE_MODERATORS:
        avail_col = f"{col.lower()}_available"
        if avail_col in coverage.columns:
            n = coverage[avail_col].sum()
            countries = coverage[coverage[avail_col] == 1]["country_iso2"].tolist()
            print(f"\n  {col}: {n} countries with 1990–1995 baseline data")
            print(f"    {sorted(countries)}")

    print(f"\n  Coverage table:")
    print(coverage.to_string(index=False))
    print(f"\n  → Saved: {out_path.relative_to(REPO_ROOT)}")
    return coverage


def _print_ictwss_known_coverage():
    """Print what we know about ICTWSS from the existing pipeline (when file absent)."""
    print("\n  Known from existing pipeline outputs:")
    print("    Full sample (ud + coord):  ~13–15 countries")
    print("    Common sample (adjcov):    ~9–11 countries")
    print("  The pilot moderator triage (code/8-ictwss-triage.py) screens these.")
    print("  Country-level detail will be available once data/ files are present.")

    # Save a skeleton for downstream scripts
    rows = []
    for iso2 in sorted(EU_27_ISO2):
        rows.append({
            "country_iso2": iso2,
            "country_name": EU_27_NAMES.get(iso2, iso2),
            "ud_available": np.nan,
            "coord_available": np.nan,
            "adjcov_available": np.nan,
            "data_source": "PENDING — run with data/ present",
        })
    skeleton = pd.DataFrame(rows)
    out_path = OUTPUT_DIR / "ictwss_country_coverage.csv"
    skeleton.to_csv(out_path, index=False)
    print(f"\n  → Saved skeleton (NaN values): {out_path.relative_to(REPO_ROOT)}")


# ---------------------------------------------------------------------------
# 2c. IFR → NACE crosswalk
# ---------------------------------------------------------------------------

def document_crosswalk() -> None:
    banner("2c. IFR → NACE Rev.2 Crosswalk")

    # Build crosswalk DataFrame
    rows = []
    nace_descriptions = {
        "C10-C12": "Food, beverages & tobacco",
        "C13-C15": "Textiles, apparel & leather",
        "C16-C18": "Wood, paper & printing",
        "C19":     "Coke & refined petroleum",
        "C20-C21": "Chemicals & pharmaceuticals",
        "C21":     "Pharmaceuticals only (IFR code 21 — merges into C20-C21 in KLEMS)",
        "C22-C23": "Rubber, plastics & non-metallic minerals",
        "C24-C25": "Basic metals & fabricated metal products",
        "C26-C27": "Computer, electronic & electrical equipment",
        "C28":     "Machinery & equipment n.e.c.",
        "C29-C30": "Motor vehicles & other transport equipment",
        "C":       "Manufacturing aggregate (excluded from bucket models)",
        "C31-C33": "Furniture & other manufacturing",
    }

    for ifr_code, nace_code in IFR_TO_NACE.items():
        rows.append({
            "ifr_industry_code": ifr_code,
            "nace_r2_code":      nace_code,
            "in_operational_model": nace_code in NACE_OPERATIONAL,
            "nace_description":  nace_descriptions.get(nace_code, ""),
        })

    crosswalk_df = pd.DataFrame(rows).sort_values("ifr_industry_code")
    out_path = OUTPUT_DIR / "ifr_nace_crosswalk.csv"
    crosswalk_df.to_csv(out_path, index=False)

    print(f"  {len(IFR_TO_NACE)} IFR codes → {crosswalk_df['nace_r2_code'].nunique()} unique NACE codes")
    print(f"  Operational NACE groups (in 5-bucket model): {len(NACE_OPERATIONAL)}")
    print()
    print(crosswalk_df.to_string(index=False))
    print(f"\n  Note: IFR code 'D' maps to aggregate 'C' (total manufacturing).")
    print(f"        These rows are DROPPED when bucket assignment fails (dropna on 'bucket').")
    print(f"\n  → Saved: {out_path.relative_to(REPO_ROOT)}")

    # Unique NACE codes in operational model
    print(f"\n  Unique NACE codes in operational model ({len(NACE_OPERATIONAL)}):")
    for nace in NACE_OPERATIONAL:
        print(f"    {nace:<12}  {nace_descriptions.get(nace, '')}")


# ---------------------------------------------------------------------------
# 2d. Trade data check and download instructions
# ---------------------------------------------------------------------------

def audit_trade_data() -> None:
    banner("2d. Trade Data — Availability Check & Download Instructions")

    # Check for any trade/WIOD files in the repo
    trade_patterns = [
        "wiod*", "WIOD*", "tiva*", "TiVA*", "comext*", "Comext*",
        "*trade*", "*export*", "*SITC*", "*HS*",
    ]
    found_files = []
    for pat in trade_patterns:
        found_files.extend(DATA_DIR.glob(pat))
        found_files.extend((REPO_ROOT / "testing").glob(f"**/{pat}") if (REPO_ROOT / "testing").exists() else [])

    # Also check KLEMS for export variables
    klems_path = DATA_DIR / "klems_growth_accounts_basic.csv"
    klems_has_trade = False
    if klems_path.exists():
        klems_cols = pd.read_csv(klems_path, nrows=5).columns.tolist()
        trade_vars_klems = [c for c in klems_cols if any(t in c.upper() for t in ["EXP", "IMP", "TRADE", "EXPORT"])]
        if trade_vars_klems:
            klems_has_trade = True
            print(f"  [FOUND] Trade-like variables in KLEMS: {trade_vars_klems}")

        # Check var column for trade variables
        klems_sample = pd.read_csv(klems_path, nrows=2000)
        if "var" in klems_sample.columns:
            trade_vars_in_var = [v for v in klems_sample["var"].unique()
                                 if any(t in str(v).upper() for t in ["EXP", "IMP", "TRADE", "X_", "_X"])]
            if trade_vars_in_var:
                klems_has_trade = True
                print(f"  [FOUND] Trade vars in KLEMS 'var' column: {trade_vars_in_var}")

    if found_files:
        print(f"  [FOUND] Trade-related files in repo:")
        for f in found_files:
            print(f"    {f.relative_to(REPO_ROOT)}")
    else:
        print("  [NOT FOUND] No trade data files detected in data/ directory.")

    if not klems_has_trade and not found_files:
        print("\n  Trade data is NOT yet in the repository.")
        print("  The exposed/sheltered extension requires manual download (see below).")

    # Download instructions
    checklist = _build_trade_checklist()
    out_path = OUTPUT_DIR / "trade_data_checklist.txt"
    out_path.write_text(checklist)
    print("\n" + checklist)
    print(f"  → Saved: {out_path.relative_to(REPO_ROOT)}")


def _build_trade_checklist() -> str:
    return """\
============================================================
  TRADE DATA DOWNLOAD CHECKLIST
  (for exposed/sheltered industry extension — Equations 5–6)
============================================================

WHAT WE NEED
  Granularity : country × NACE 2-digit manufacturing × year
  Variable    : export value (EUR/USD) — or export intensity = exports/gross output
  Years       : 2000–2019 (overlap with IFR)
  Countries   : EU-27 (ideally) + UK for historical comparison

---

OPTION 1 (Recommended): WIOD Socio-Economic Accounts (SEA)
  Source   : https://www.rug.nl/ggdc/valuechain/wiod/wiod-2016-release
  File     : wiot_sea_nov16.xlsx (or SEA_Nov16.xlsx)
  Variables: EXP (exports of output), GO (gross output) by country × NACE
  Coverage : 43 countries, 2000–2014, NACE Rev.1/2 industries
  Download : Manual download from WIOD website
  Note     : Year coverage ends 2014; industry concordance to NACE Rev.2 needed.
  Crosswalk: WIOD NACE Rev.1 → NACE Rev.2 concordance available from Eurostat.

---

OPTION 2 (Preferred for recency): OECD TiVA 2023
  Source   : https://stats.oecd.org/  → Trade in Value Added (TiVA)
  Dataset  : TiVA_2023_BASIC.csv (bulk download)
  Variables: EXGR (gross exports) by country × ISIC Rev.4 industry
  Coverage : 75 countries, 2005–2020, ISIC Rev.4 (maps to NACE Rev.2)
  API URL  : https://stats.oecd.org/SDMX-JSON/data/TIVA_2023_C1/...
  Download : Bulk CSV via OECD.Stat or API
  Crosswalk: ISIC Rev.4 → NACE Rev.2 is 1:1 for manufacturing 2-digit.

---

OPTION 3: Eurostat Structural Business Statistics (SBS)
  Source   : https://ec.europa.eu/eurostat/web/structural-business-statistics
  Dataset  : sbs_na_ind_r2 (annual enterprise statistics by NACE Rev.2)
  Variables: V11120 (turnover), V12150 (exports) — not always available at 2-digit
  Coverage : EU-27, 1995–2020
  API URL  : https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sbs_na_ind_r2
  Note     : Export variable availability is patchy at 2-digit NACE level.

---

OPTION 4: Eurostat Comext (detailed but complex)
  Source   : https://ec.europa.eu/eurostat/web/international-trade-in-goods/data/database
  Dataset  : DS-018995 (EU trade since 1988, SITC) or DS-045409 (CN codes)
  Note     : Reported in CN/HS product codes — requires SITC/HS → NACE concordance.
             More granular but concordance mapping is non-trivial.
  Download : Comext bulk download tool or Eurostat API

---

RECOMMENDED APPROACH FOR THIS THESIS
  1. Download WIOD SEA (2000–2014) as the primary source — simple NACE concordance.
  2. Extend to 2019 using OECD TiVA (2005–2020) for recent years.
  3. Compute export intensity = exports / gross output, averaged 1995–2000 (baseline).
  4. Binary Exposed_j = 1 if baseline export intensity above median.
  5. Place downloaded files in: data/wiod_sea.xlsx and data/oecd_tiva.csv

---

CURRENT STATUS IN REPO
  [ ] WIOD SEA          — NOT present
  [ ] OECD TiVA         — NOT present
  [ ] Eurostat SBS      — NOT present
  [ ] Eurostat Comext   — NOT present

All data needs to be downloaded manually before running 02_merge_feasibility.py
in non-simulation mode.
============================================================
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  01 — Data Availability Audit")
    print(f"  Repo root : {REPO_ROOT}")
    print(f"  Data dir  : {DATA_DIR}  (exists: {DATA_DIR.exists()})")
    print(f"  Output dir: {OUTPUT_DIR}")
    print("=" * 60)

    # 2a. IFR
    audit_ifr()

    # 2b. ICTWSS
    audit_ictwss()

    # 2c. Crosswalk (always works — hardcoded constants)
    document_crosswalk()

    # 2d. Trade data
    audit_trade_data()

    print(f"\n{'=' * 60}")
    print("  Audit complete. Outputs saved to analysis/trade_feasibility/output/")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
