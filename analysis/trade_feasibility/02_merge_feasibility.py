"""
02_merge_feasibility.py
==============================================
Simulate the merge under four scenarios and count surviving observations.
This is the core deliverable of the feasibility audit.

Scenarios
---------
A  IFR × Trade data           — maximum possible sample (no ICTWSS)
B  IFR × Trade × ICTWSS       — moderation models (ud + coord)
C  IFR × Trade × ICTWSS       — restricted sample (adjcov)
D  Current: IFR × KLEMS × ICTWSS — baseline for direct comparison

Key question
  If Scenario B delivers ≥ 20 countries, the trade pivot is worth pursuing.
  If ≤ 15 countries, the gain over current ~13 is marginal.

Outputs (saved to ./output/):
  merge_scenario_A_ifr_trade.csv
  merge_scenario_B_ifr_trade_ictwss.csv
  merge_scenario_C_restricted.csv
  merge_scenario_D_current_baseline.csv

Run:
    python 02_merge_feasibility.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR  = Path(__file__).resolve().parent
REPO_ROOT   = SCRIPT_DIR.parents[1]
DATA_DIR    = REPO_ROOT / "data"
OUTPUT_DIR  = SCRIPT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants (mirrored from code/2-build_panel.py and code/_equation_utils.py)
# ---------------------------------------------------------------------------
EU_ISO2 = {
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES",
    "FI", "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV",
    "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK", "UK",
}

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
    "UK": "United Kingdom",
}

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
    "D":      "C",
    "D_other": "C31-C33",
}

# NACE groups in the 5-bucket operational model (excludes "C" aggregate)
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

ICTWSS_CANDIDATES = ["Coord", "AdjCov", "UD"]

# Simulation year range: IFR × Trade overlap
SIM_YEARS = list(range(2000, 2020))   # 2000–2019


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def banner(title: str) -> None:
    print(f"\n{'=' * 65}")
    print(f"  {title}")
    print('=' * 65)


def metrics(df: pd.DataFrame, label: str) -> dict:
    """Compute standardised metrics from a country-industry-year DataFrame."""
    ctry_col  = "country_code"
    ind_col   = "nace_r2_code"
    year_col  = "year"
    entity_col = "entity"

    if entity_col not in df.columns:
        df = df.copy()
        df["entity"] = df[ctry_col] + "_" + df[ind_col]

    n_countries = df[ctry_col].nunique()
    n_entities  = df["entity"].nunique()
    n_obs       = len(df)
    yr_min      = int(df[year_col].min())
    yr_max      = int(df[year_col].max())
    countries   = sorted(df[ctry_col].unique())

    return {
        "scenario":    label,
        "n_countries": n_countries,
        "n_entities":  n_entities,
        "n_obs":       n_obs,
        "year_min":    yr_min,
        "year_max":    yr_max,
        "countries":   countries,
    }


def print_metrics(m: dict) -> None:
    print(f"\n  Scenario: {m['scenario']}")
    print(f"    Countries : {m['n_countries']}  {m['countries']}")
    print(f"    Entities  : {m['n_entities']}  (country × industry cells)")
    print(f"    Obs       : {m['n_obs']:,}  (country–industry–year)")
    print(f"    Years     : {m['year_min']}–{m['year_max']}")


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def load_ifr() -> pd.DataFrame | None:
    """Load IFR robot data; return None if file absent."""
    path = DATA_DIR / "IFR_karol.csv"
    if not path.exists():
        print(f"  [MISSING] {path.relative_to(REPO_ROOT)}")
        return None
    print(f"  [LOADED]  {path.relative_to(REPO_ROOT)}")
    ifr = pd.read_csv(path, low_memory=False)
    ifr["year"] = pd.to_numeric(ifr["year"], errors="coerce")
    ifr = ifr[ifr["country_code"].isin(EU_ISO2)]
    ifr = ifr[ifr["industry_code"].isin(IFR_TO_NACE.keys())]
    ifr = ifr[ifr["year"].between(2000, 2019)]

    # Map IFR → NACE; keep only operational groups
    ifr["nace_r2_code"] = ifr["industry_code"].map(IFR_TO_NACE)
    ifr = ifr[ifr["nace_r2_code"].isin(NACE_OPERATIONAL)]
    ifr = ifr.dropna(subset=["nace_r2_code", "country_code", "year"])
    return ifr


def build_ifr_skeleton(ifr: pd.DataFrame | None) -> pd.DataFrame:
    """
    Build a country × NACE × year skeleton from actual IFR data.
    If IFR is absent, simulate using EU_ISO2 × NACE_OPERATIONAL × SIM_YEARS.
    """
    if ifr is not None:
        skel = (
            ifr[["country_code", "nace_r2_code", "year"]]
            .drop_duplicates()
            .reset_index(drop=True)
        )
        print(f"  IFR skeleton: {skel['country_code'].nunique()} countries, "
              f"{skel['nace_r2_code'].nunique()} NACE groups, "
              f"{len(skel):,} country–industry–year cells")
        return skel
    else:
        # Simulation: assume IFR covers EU_ISO2 (upper bound)
        print("  [SIM] IFR data absent — simulating with EU_ISO2 × NACE_OPERATIONAL × 2000–2019")
        rows = [
            {"country_code": c, "nace_r2_code": n, "year": y}
            for c in sorted(EU_ISO2)
            for n in NACE_OPERATIONAL
            for y in SIM_YEARS
        ]
        skel = pd.DataFrame(rows)
        print(f"  [SIM] Simulated IFR skeleton: {len(EU_ISO2)} countries × "
              f"{len(NACE_OPERATIONAL)} NACE groups × {len(SIM_YEARS)} years = {len(skel):,} cells")
        print("  [NOTE] Actual IFR coverage is a subset of this — real N will be lower.")
        return skel


def load_ictwss_baseline() -> pd.DataFrame | None:
    """Load ICTWSS and compute 1990–1995 baseline means; return None if absent."""
    path = DATA_DIR / "ictwss_institutions.csv"
    if not path.exists():
        print(f"  [MISSING] {path.relative_to(REPO_ROOT)}")
        return None
    print(f"  [LOADED]  {path.relative_to(REPO_ROOT)}")
    ictwss = pd.read_csv(path, low_memory=False)
    ictwss["country_code"] = ictwss["iso3"].map(ISO3_TO_ISO2)
    ictwss = ictwss[ictwss["country_code"].isin(EU_ISO2)]

    for col in ICTWSS_CANDIDATES:
        if col in ictwss.columns:
            ictwss[col] = pd.to_numeric(ictwss[col], errors="coerce")
            ictwss.loc[ictwss[col] == -99, col] = np.nan

    base = ictwss[ictwss["year"].between(1990, 1995)]

    def _safe_mean(s):
        v = pd.to_numeric(s, errors="coerce")
        return v.dropna().mean() if v.notna().any() else np.nan

    agg = {col: (col, _safe_mean) for col in ICTWSS_CANDIDATES if col in base.columns}
    baseline = base.groupby("country_code").agg(**agg).reset_index()

    for col in ICTWSS_CANDIDATES:
        lc = col.lower()
        if col in baseline.columns:
            baseline[f"has_{lc}"] = baseline[col].notna().astype(int)
        else:
            baseline[f"has_{lc}"] = 0
    return baseline


def simulate_ictwss_baseline() -> pd.DataFrame:
    """
    Fallback ICTWSS baseline when file is absent.

    Based on the known panel output (~13–15 full sample, ~9–11 common sample):
    - ud + coord: the 13–15 countries that appear in the current full panel
    - adjcov: the ~9–11 countries in the common sample

    These are conservative estimates from the existing pipeline diagnostics.
    Replace with actual data once data/ files are present.
    """
    print("  [SIM] ICTWSS data absent — using conservative simulation")
    print("        Based on known full-sample (~14) and common-sample (~10) country counts.")

    # Countries known to have good ICTWSS coverage across EU manufacturing studies
    # (Dünhaupt 2017; Traxler et al. 2001; ICTWSS documentation)
    ud_coord_countries = {
        "AT", "BE", "CZ", "DE", "DK", "EE", "EL", "ES",
        "FI", "FR", "HU", "IE", "IT", "NL", "PL", "PT",
        "SE", "SK", "SI",
    }
    adjcov_countries = {
        "AT", "BE", "DE", "DK", "EL", "ES", "FI", "FR",
        "IT", "NL", "PT", "SE",
    }

    rows = []
    for iso2 in sorted(EU_ISO2):
        rows.append({
            "country_code":    iso2,
            "has_ud":          int(iso2 in ud_coord_countries),
            "has_coord":       int(iso2 in ud_coord_countries),
            "has_adjcov":      int(iso2 in adjcov_countries),
            "simulated":       True,
        })
    df = pd.DataFrame(rows)
    print(f"  [SIM] Simulated ICTWSS: "
          f"ud/coord={df['has_ud'].sum()} countries, "
          f"adjcov={df['has_adjcov'].sum()} countries")
    print("  [NOTE] Replace with actual data once ictwss_institutions.csv is available.")
    return df


def load_trade_data() -> pd.DataFrame | None:
    """Try to load any trade data present in data/. Return None if none found."""
    candidates = [
        DATA_DIR / "wiod_sea.xlsx",
        DATA_DIR / "wiod_sea.csv",
        DATA_DIR / "oecd_tiva.csv",
        DATA_DIR / "trade_exports.csv",
    ]
    for path in candidates:
        if path.exists():
            print(f"  [LOADED]  {path.relative_to(REPO_ROOT)}")
            if path.suffix == ".xlsx":
                return pd.read_excel(path)
            return pd.read_csv(path, low_memory=False)
    print("  [MISSING] No trade data found in data/")
    print("            Run script in simulation mode (all EU-27 as available).")
    return None


def simulate_trade_data() -> pd.DataFrame:
    """
    Simulate trade data: assume Eurostat/WIOD covers ALL EU-27 countries.
    This is the upper-bound assumption — every EU-27 country × NACE × year is 'available'.
    The actual constraint will be IFR (not trade data).
    """
    print("  [SIM] Trade data absent — assuming EU-27 full coverage (upper bound)")
    rows = [
        {"country_code": c, "nace_r2_code": n, "year": y, "trade_simulated": True}
        for c in sorted(EU_27_ISO2)
        for n in NACE_OPERATIONAL
        for y in SIM_YEARS
    ]
    df = pd.DataFrame(rows)
    print(f"  [SIM] {len(EU_27_ISO2)} EU-27 countries × {len(NACE_OPERATIONAL)} NACE × "
          f"{len(SIM_YEARS)} years = {len(df):,} cells (simulated trade)")
    return df


def load_current_panel() -> pd.DataFrame | None:
    """Load cleaned_data.csv from the existing pipeline; return None if absent."""
    path = DATA_DIR / "cleaned_data.csv"
    if not path.exists():
        path2 = DATA_DIR / "cleaned_data.parquet"
        if path2.exists():
            return pd.read_parquet(path2)
        print(f"  [MISSING] {(DATA_DIR / 'cleaned_data.csv').relative_to(REPO_ROOT)}")
        return None
    print(f"  [LOADED]  {path.relative_to(REPO_ROOT)}")
    return pd.read_csv(path, low_memory=False)


# ---------------------------------------------------------------------------
# Scenario A: IFR × Trade
# ---------------------------------------------------------------------------

def scenario_a(ifr_skel: pd.DataFrame, trade: pd.DataFrame) -> pd.DataFrame:
    banner("Scenario A: IFR × Trade (maximum possible sample, no institutions)")

    # Inner join: both must have data for that country × NACE × year
    merged = ifr_skel.merge(
        trade[["country_code", "nace_r2_code", "year"]].drop_duplicates(),
        on=["country_code", "nace_r2_code", "year"],
        how="inner",
    )
    merged["entity"] = merged["country_code"] + "_" + merged["nace_r2_code"]

    m = metrics(merged, "A: IFR × Trade (no institutions)")
    print_metrics(m)

    # Countries that DROP: in EU-27 but absent from IFR
    eu27_in_ifr  = set(ifr_skel["country_code"]) & EU_27_ISO2
    eu27_missing = EU_27_ISO2 - eu27_in_ifr
    print(f"\n  EU-27 countries absent from IFR skeleton: {len(eu27_missing)}")
    if eu27_missing:
        print(f"    {sorted(eu27_missing)}")
    print(f"  EU-27 countries present in IFR skeleton: {len(eu27_in_ifr)}")
    print(f"    {sorted(eu27_in_ifr)}")

    out = merged.copy()
    out["scenario"] = "A"
    out_path = OUTPUT_DIR / "merge_scenario_A_ifr_trade.csv"
    out.to_csv(out_path, index=False)
    print(f"\n  → Saved: {out_path.relative_to(REPO_ROOT)}")
    return merged


# ---------------------------------------------------------------------------
# Scenario B: IFR × Trade × ICTWSS (ud + coord)
# ---------------------------------------------------------------------------

def scenario_b(
    scenario_a_df: pd.DataFrame,
    ictwss: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    banner("Scenario B: IFR × Trade × ICTWSS (ud + coord)")

    # Left-join ICTWSS baseline (country-level, time-invariant)
    merged = scenario_a_df.merge(ictwss, on="country_code", how="left")

    results = {}
    for mod, col in [("ud", "has_ud"), ("coord", "has_coord"), ("both", None)]:
        if mod == "both":
            sub = merged[(merged["has_ud"] == 1) & (merged["has_coord"] == 1)]
        else:
            sub = merged[merged[col] == 1]

        sub = sub.copy()
        sub["entity"] = sub["country_code"] + "_" + sub["nace_r2_code"]
        label = f"B: IFR × Trade × ICTWSS ({mod})"
        m = metrics(sub, label)
        print_metrics(m)
        results[mod] = sub

    # Save the "both" scenario as the main B output
    out = results["both"].copy()
    out["scenario"] = "B"
    out_path = OUTPUT_DIR / "merge_scenario_B_ifr_trade_ictwss.csv"
    out.to_csv(out_path, index=False)
    print(f"\n  → Saved: {out_path.relative_to(REPO_ROOT)}")
    return results


# ---------------------------------------------------------------------------
# Scenario C: IFR × Trade × ICTWSS (adjcov restricted)
# ---------------------------------------------------------------------------

def scenario_c(
    scenario_a_df: pd.DataFrame,
    ictwss: pd.DataFrame,
) -> pd.DataFrame:
    banner("Scenario C: IFR × Trade × ICTWSS (adjcov restricted sample)")

    merged = scenario_a_df.merge(ictwss, on="country_code", how="left")

    if "has_adjcov" in merged.columns:
        sub = merged[merged["has_adjcov"] == 1].copy()
    else:
        print("  [WARNING] 'has_adjcov' not found in ICTWSS data — using full join.")
        sub = merged.copy()

    sub["entity"] = sub["country_code"] + "_" + sub["nace_r2_code"]
    m = metrics(sub, "C: IFR × Trade × ICTWSS (adjcov only)")
    print_metrics(m)

    out = sub.copy()
    out["scenario"] = "C"
    out_path = OUTPUT_DIR / "merge_scenario_C_restricted.csv"
    out.to_csv(out_path, index=False)
    print(f"\n  → Saved: {out_path.relative_to(REPO_ROOT)}")
    return sub


# ---------------------------------------------------------------------------
# Scenario D: Current approach (IFR × KLEMS × ICTWSS)
# ---------------------------------------------------------------------------

def scenario_d() -> pd.DataFrame | None:
    banner("Scenario D: Current approach — IFR × KLEMS × ICTWSS (baseline comparison)")

    panel = load_current_panel()

    if panel is not None:
        # Real data available
        panel["year"] = pd.to_numeric(panel["year"], errors="coerce")

        # Check which ICTWSS moderators are available
        has_ud     = "ud_pre" in panel.columns or "has_ud" in panel.columns
        has_coord  = "coord_pre" in panel.columns or "has_coord" in panel.columns
        has_adjcov = "adjcov_pre" in panel.columns or "has_adjcov" in panel.columns

        m = metrics(panel.rename(columns={"nace_r2_code": "nace_r2_code"}),
                    "D: Current (IFR × KLEMS × ICTWSS)")
        print_metrics(m)

        # ICTWSS coverage in actual panel
        for mod_col, label in [
            ("has_ud",     "ud"),
            ("has_coord",  "coord"),
            ("has_adjcov", "adjcov"),
        ]:
            if mod_col in panel.columns:
                n = panel[panel[mod_col]]["country_code"].nunique()
                countries = sorted(panel[panel[mod_col]]["country_code"].unique())
                print(f"\n    {label}: {n} countries  {countries}")
            elif mod_col.replace("has_", "") + "_pre" in panel.columns:
                col = mod_col.replace("has_", "") + "_pre"
                n = panel[panel[col].notna()]["country_code"].nunique()
                countries = sorted(panel[panel[col].notna()]["country_code"].unique())
                print(f"\n    {label}: {n} countries  {countries}")

        out = panel.copy()
        out["scenario"] = "D"
        out_path = OUTPUT_DIR / "merge_scenario_D_current_baseline.csv"
        out.to_csv(out_path, index=False)
        print(f"\n  → Saved: {out_path.relative_to(REPO_ROOT)}")
        return panel

    else:
        # Simulate current panel dimensions from known pipeline outputs
        print("\n  [SIM] cleaned_data.csv absent — simulating from known pipeline output.")
        print("        Run code/2-build_panel.py first to get actual Scenario D numbers.")
        print()
        print("  Known from README and pipeline diagnostics:")
        print("    Full sample (ud + coord):  ~13–15 countries, ~2,600–2,700 obs")
        print("    Common sample (adjcov):    ~9–11 countries,  ~1,900–2,000 obs")
        print("    Years (effective):         ~2003–2019")
        print("    Entities:                  ~265–290")

        # Produce a simulation row for the comparison table
        sim_rows = [
            {"scenario": "D (simulated)",
             "n_countries": 14, "n_entities": 278, "n_obs": 2650,
             "year_min": 2003, "year_max": 2019,
             "moderator": "ud+coord (full sample)", "simulated": True},
            {"scenario": "D (simulated)",
             "n_countries": 10, "n_entities": 210, "n_obs": 1950,
             "year_min": 2003, "year_max": 2019,
             "moderator": "adjcov (common sample)", "simulated": True},
        ]
        sim = pd.DataFrame(sim_rows)
        out_path = OUTPUT_DIR / "merge_scenario_D_current_baseline.csv"
        sim.to_csv(out_path, index=False)
        print(f"\n  → Saved simulation placeholder: {out_path.relative_to(REPO_ROOT)}")
        return None


# ---------------------------------------------------------------------------
# Summary print
# ---------------------------------------------------------------------------

def print_summary_table(results: dict) -> None:
    banner("Summary: Country Counts Across Scenarios")

    rows = []
    for key, val in results.items():
        if val is None:
            continue
        if isinstance(val, dict):
            for subkey, sub_df in val.items():
                m = metrics(sub_df, f"{key}_{subkey}")
                rows.append({
                    "Scenario": m["scenario"],
                    "Countries": m["n_countries"],
                    "Entities":  m["n_entities"],
                    "Obs":       m["n_obs"],
                    "Years":     f"{m['year_min']}–{m['year_max']}",
                })
        else:
            m = metrics(val, key)
            rows.append({
                "Scenario": m["scenario"],
                "Countries": m["n_countries"],
                "Entities":  m["n_entities"],
                "Obs":       m["n_obs"],
                "Years":     f"{m['year_min']}–{m['year_max']}",
            })

    if rows:
        tbl = pd.DataFrame(rows)
        print(tbl.to_string(index=False))

    print()
    print("  Decision threshold (from README): Scenario B ≥ 20 countries → pivot worth pursuing")
    print("  If Scenario B ≤ 15 countries → gain over current ~13 is marginal")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 65)
    print("  02 — Merge Feasibility: Simulating Sample Sizes")
    print(f"  Repo root : {REPO_ROOT}")
    print(f"  Data dir  : {DATA_DIR}  (exists: {DATA_DIR.exists()})")
    print("=" * 65)

    # --- Load or simulate data ---
    print("\n--- Data loading ---")
    ifr        = load_ifr()
    ifr_skel   = build_ifr_skeleton(ifr)
    trade      = load_trade_data()
    if trade is None:
        trade = simulate_trade_data()
    ictwss_raw = load_ictwss_baseline()
    if ictwss_raw is None:
        ictwss = simulate_ictwss_baseline()
    else:
        # Normalise column names for merge helpers
        ictwss = ictwss_raw.copy()
        for col in ["UD", "Coord", "AdjCov"]:
            lc = col.lower()
            has_col = f"has_{lc}"
            if has_col not in ictwss.columns and col in ictwss.columns:
                ictwss[has_col] = ictwss[col].notna().astype(int)

    # --- Run scenarios ---
    skel_a  = scenario_a(ifr_skel, trade)
    skel_bc = scenario_b(skel_a, ictwss[["country_code", "has_ud", "has_coord", "has_adjcov"]
                                         if all(c in ictwss.columns for c in ["has_ud","has_coord","has_adjcov"])
                                         else [c for c in ["country_code","has_ud","has_coord","has_adjcov"] if c in ictwss.columns]])
    skel_c  = scenario_c(skel_a, ictwss[["country_code"] + [c for c in ["has_ud","has_coord","has_adjcov"] if c in ictwss.columns]])
    skel_d  = scenario_d()

    # --- Summary ---
    print_summary_table({
        "A: IFR × Trade (no institutions)":         skel_a,
        "B breakdown":                               skel_bc,
        "C: IFR × Trade × ICTWSS (adjcov)":         skel_c,
    })

    print(f"\n{'=' * 65}")
    print("  Merge feasibility complete.")
    print("  Run 03_sample_size_report.py to see the comparison table.")
    print(f"{'=' * 65}\n")


if __name__ == "__main__":
    main()
