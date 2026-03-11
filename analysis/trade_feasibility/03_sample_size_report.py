"""
03_sample_size_report.py
==============================================
Load outputs from 01 and 02, produce a single comparison table,
and render the country-level detail matrix.

Outputs (saved to ./output/):
  sample_size_comparison.csv      — scenario-level summary table
  country_detail_matrix.csv       — per-country presence across all scenarios

Run:
    python 03_sample_size_report.py
    (requires 01 and 02 to have been run first)
"""

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT  = SCRIPT_DIR.parents[1]
DATA_DIR   = REPO_ROOT / "data"
OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Reference data (same as previous scripts)
# ---------------------------------------------------------------------------
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
NACE_OPERATIONAL = [
    "C10-C12", "C13-C15", "C16-C18", "C19", "C20-C21",
    "C22-C23", "C24-C25", "C26-C27", "C28", "C29-C30", "C31-C33",
]


def banner(title: str) -> None:
    print(f"\n{'=' * 65}")
    print(f"  {title}")
    print('=' * 65)


# ---------------------------------------------------------------------------
# Load scenario CSVs
# ---------------------------------------------------------------------------

def load_scenario(filename: str) -> pd.DataFrame | None:
    path = OUTPUT_DIR / filename
    if not path.exists():
        print(f"  [MISSING] {filename} — run 02_merge_feasibility.py first")
        return None
    df = pd.read_csv(path, low_memory=False)
    return df


def scenario_metrics(df: pd.DataFrame, scenario_label: str,
                     ud_col: str | None = None,
                     coord_col: str | None = None,
                     adjcov_col: str | None = None) -> dict:
    """Extract standardised metrics from a scenario DataFrame."""
    if df is None or len(df) == 0:
        return {"scenario": scenario_label, "n_countries": "—", "n_entities": "—",
                "n_obs": "—", "years": "—", "ud": "—", "coord": "—", "adjcov": "—"}

    year_col = "year" if "year" in df.columns else None
    ctry_col = "country_code" if "country_code" in df.columns else None
    nace_col = "nace_r2_code" if "nace_r2_code" in df.columns else None

    n_countries = df[ctry_col].nunique() if ctry_col else "?"
    n_entities  = (df[ctry_col] + "_" + df[nace_col]).nunique() \
                  if (ctry_col and nace_col) else "?"
    n_obs       = len(df)
    yr_min      = int(df[year_col].min()) if year_col and df[year_col].notna().any() else "?"
    yr_max      = int(df[year_col].max()) if year_col and df[year_col].notna().any() else "?"
    years       = f"{yr_min}–{yr_max}" if yr_min != "?" else "—"

    def avail_count(col):
        if col and col in df.columns:
            sub = df[df[col] == 1]
            return sub[ctry_col].nunique() if ctry_col else "?"
        return "—"

    return {
        "scenario":    scenario_label,
        "n_countries": n_countries,
        "n_entities":  n_entities,
        "n_obs":       n_obs,
        "years":       years,
        "ud":          avail_count(ud_col),
        "coord":       avail_count(coord_col),
        "adjcov":      avail_count(adjcov_col),
    }


# ---------------------------------------------------------------------------
# Build comparison table
# ---------------------------------------------------------------------------

def build_comparison_table() -> pd.DataFrame:
    banner("Sample Size Comparison: All Scenarios")

    # Load scenario outputs
    df_a = load_scenario("merge_scenario_A_ifr_trade.csv")
    df_b = load_scenario("merge_scenario_B_ifr_trade_ictwss.csv")
    df_c = load_scenario("merge_scenario_C_restricted.csv")
    df_d = load_scenario("merge_scenario_D_current_baseline.csv")

    rows = []

    # Scenario A — no institutions
    rows.append(scenario_metrics(
        df_a, "A: IFR × Trade  (maximum, no institutions)",
    ))

    # Scenario B — ud + coord
    if df_b is not None:
        rows.append(scenario_metrics(
            df_b, "B: IFR × Trade × ICTWSS  (ud + coord)",
            ud_col="has_ud", coord_col="has_coord",
        ))

    # Scenario C — adjcov restricted
    if df_c is not None:
        rows.append(scenario_metrics(
            df_c, "C: IFR × Trade × ICTWSS  (adjcov restricted)",
            ud_col="has_ud", coord_col="has_coord", adjcov_col="has_adjcov",
        ))

    # Scenario D — current baseline
    if df_d is not None:
        # cleaned_data.csv has a different structure; handle both real and simulated
        if "simulated" in df_d.columns:
            # Simulated rows — two sub-rows
            for _, row in df_d.iterrows():
                rows.append({
                    "scenario":    f"D (est.): {row.get('moderator', 'current')}",
                    "n_countries": row["n_countries"],
                    "n_entities":  row["n_entities"],
                    "n_obs":       row["n_obs"],
                    "years":       f"{int(row['year_min'])}–{int(row['year_max'])}",
                    "ud":          "✓" if "ud" in str(row.get("moderator","")) else "—",
                    "coord":       "✓" if "coord" in str(row.get("moderator","")) else "—",
                    "adjcov":      "✓" if "adjcov" in str(row.get("moderator","")) else "—",
                })
        else:
            # Real cleaned_data
            for mod_label, ud_c, coord_c, adjcov_c, filter_col in [
                ("ud+coord (full sample)",   "has_ud", "has_coord",  None,        None),
                ("adjcov (common sample)",   "has_ud", "has_coord",  "has_adjcov","has_adjcov"),
            ]:
                sub = df_d.copy()
                if filter_col and filter_col in sub.columns:
                    sub = sub[sub[filter_col] == 1]
                rows.append(scenario_metrics(
                    sub, f"D: Current IFR×KLEMS  ({mod_label})",
                    ud_col=ud_c, coord_col=coord_c, adjcov_col=adjcov_c,
                ))

    tbl = pd.DataFrame(rows)
    tbl.columns = [
        "Scenario", "Countries", "Entities", "Obs", "Years", "ud ✓", "coord ✓", "adjcov ✓"
    ]

    print()
    print(tbl.to_string(index=False))

    # Decision guidance
    print()
    print("  ── Decision threshold ──────────────────────────────────")
    b_row = tbl[tbl["Scenario"].str.startswith("B:")]
    if not b_row.empty:
        n_b = b_row.iloc[0]["Countries"]
        try:
            n_b_int = int(n_b)
            if n_b_int >= 20:
                verdict = f"✓ PROCEED — {n_b_int} countries ≥ 20 threshold. Trade pivot is worthwhile."
            elif n_b_int >= 16:
                verdict = f"△ MARGINAL — {n_b_int} countries (16–19). Modest gain; evaluate carefully."
            else:
                verdict = f"✗ LIKELY NOT WORTH IT — {n_b_int} countries ≤ 15. Minimal gain over current ~13."
        except (ValueError, TypeError):
            verdict = f"  Scenario B countries: {n_b} (check simulation notes)"
    else:
        verdict = "  Scenario B result not available."
    print(f"  {verdict}")
    print("  ────────────────────────────────────────────────────────")

    out_path = OUTPUT_DIR / "sample_size_comparison.csv"
    tbl.to_csv(out_path, index=False)
    print(f"\n  → Saved: {out_path.relative_to(REPO_ROOT)}")
    return tbl


# ---------------------------------------------------------------------------
# Country-level detail matrix
# ---------------------------------------------------------------------------

def build_country_detail() -> pd.DataFrame:
    banner("Country-Level Detail Matrix")

    # Load all scenarios
    df_a    = load_scenario("merge_scenario_A_ifr_trade.csv")
    df_b    = load_scenario("merge_scenario_B_ifr_trade_ictwss.csv")
    df_c    = load_scenario("merge_scenario_C_restricted.csv")
    df_d    = load_scenario("merge_scenario_D_current_baseline.csv")
    df_ictwss = load_scenario("ictwss_country_coverage.csv")

    # Build per-country flags
    rows = []
    all_countries = sorted(EU_27_ISO2 | {"UK"})

    for iso2 in all_countries:
        row = {
            "country_iso2": iso2,
            "country_name": EU_27_NAMES.get(iso2, iso2),
            "in_eu27":      "Y" if iso2 in EU_27_ISO2 else "N",
        }

        # IFR presence (from Scenario A — IFR is the constraint)
        if df_a is not None and "country_code" in df_a.columns:
            row["in_ifr"]           = "Y" if iso2 in df_a["country_code"].values else "N"
            sub_ifr = df_a[df_a["country_code"] == iso2]
            row["n_nace_in_ifr"]    = sub_ifr["nace_r2_code"].nunique() if len(sub_ifr) > 0 else 0
        else:
            row["in_ifr"]        = "?"
            row["n_nace_in_ifr"] = "?"

        # ICTWSS moderator availability
        if df_ictwss is not None and "country_iso2" in df_ictwss.columns:
            ictwss_row = df_ictwss[df_ictwss["country_iso2"] == iso2]
            if len(ictwss_row) > 0:
                r = ictwss_row.iloc[0]
                row["ud_avail"]     = _yn(r.get("ud_available",    np.nan))
                row["coord_avail"]  = _yn(r.get("coord_available",  np.nan))
                row["adjcov_avail"] = _yn(r.get("adjcov_available", np.nan))
            else:
                row["ud_avail"] = row["coord_avail"] = row["adjcov_avail"] = "?"
        elif df_b is not None and "country_code" in df_b.columns:
            # Infer from scenario B/C
            sub_b = df_b[df_b["country_code"] == iso2]
            sub_c = df_c[df_c["country_code"] == iso2] if df_c is not None else pd.DataFrame()
            row["ud_avail"]     = "Y" if len(sub_b) > 0 else "N"
            row["coord_avail"]  = "Y" if len(sub_b) > 0 else "N"
            row["adjcov_avail"] = "Y" if len(sub_c) > 0 else "N"
        else:
            row["ud_avail"] = row["coord_avail"] = row["adjcov_avail"] = "?"

        # Current KLEMS sample presence (Scenario D)
        if df_d is not None and "country_code" in df_d.columns and "simulated" not in df_d.columns:
            row["in_klems_sample"] = "Y" if iso2 in df_d["country_code"].values else "N"
        else:
            row["in_klems_sample"] = "?"

        # Would survive trade pivot? (Scenario A)
        if df_a is not None and "country_code" in df_a.columns:
            row["survives_trade_pivot"] = "Y" if iso2 in df_a["country_code"].values else "N"
        else:
            row["survives_trade_pivot"] = "?"

        rows.append(row)

    detail = pd.DataFrame(rows)
    out_path = OUTPUT_DIR / "country_detail_matrix.csv"
    detail.to_csv(out_path, index=False)

    print(detail.to_string(index=False))
    print(f"\n  → Saved: {out_path.relative_to(REPO_ROOT)}")

    # Summary counts
    print()
    print("  Summary counts:")
    for col, label in [
        ("in_ifr",             "In IFR data"),
        ("ud_avail",           "UD available (ICTWSS)"),
        ("coord_avail",        "Coord available (ICTWSS)"),
        ("adjcov_avail",       "AdjCov available (ICTWSS)"),
        ("in_klems_sample",    "In current KLEMS sample"),
        ("survives_trade_pivot", "Survives trade pivot (Scenario A)"),
    ]:
        n_y  = (detail[col] == "Y").sum()
        n_n  = (detail[col] == "N").sum()
        n_uk = (detail[col] == "?").sum()
        print(f"    {label:<35} Y={n_y:2d}  N={n_n:2d}  ?={n_uk}")

    return detail


def _yn(val) -> str:
    if pd.isna(val):
        return "?"
    try:
        return "Y" if int(float(val)) == 1 else "N"
    except (ValueError, TypeError):
        return "?"


# ---------------------------------------------------------------------------
# Interpretation notes
# ---------------------------------------------------------------------------

def print_interpretation() -> None:
    banner("Interpretation Notes")

    print("""
  READING THE RESULTS
  -------------------

  Scenario A (IFR × Trade, no institutions)
    Upper bound on the trade-pivot sample.
    IFR robot data is the binding constraint — not trade data.
    Any EU-27 country missing from Scenario A has no usable IFR data
    and cannot be added by switching outcome variables.

  Scenario B (IFR × Trade × ICTWSS, ud + coord)
    The operative comparison for the moderation models.
    Compare directly to Scenario D (full sample) for the gain from the pivot.
    Key question: how many NEW countries appear in B that are absent from D?

  Scenario C (IFR × Trade × ICTWSS, adjcov)
    Restricted sample — should be similar to Scenario D common sample.
    If Scenario C > Scenario D common, the trade pivot also benefits adjcov models.

  Scenario D (Current: IFR × KLEMS × ICTWSS)
    The benchmark. KLEMS is the binding constraint today (~13–15 countries).
    EU KLEMS 2023 release covers ~15–17 EU member states at 2-digit NACE.

  KEY QUESTION
    If Scenario A delivers ≥ 20 EU countries: IFR covers more countries
    than KLEMS. Replacing KLEMS with trade data is worth pursuing.

    If Scenario A delivers ~13–15 countries: IFR is also binding at ~13–15.
    The pivot to trade data will NOT expand the sample materially.
    → In that case, explore whether IFR has data for additional countries
      at lower industry granularity, or consider a different exposure proxy.

  DATA SIMULATION NOTE
    When data/ files are absent, Scenarios A–C use upper-bound simulations:
    - Trade data: assumed available for all EU-27 (conservative assumption)
    - ICTWSS: estimated coverage from known pipeline output (~14/10 countries)
    - IFR: if absent, assumed to cover all EU_ISO2 (will over-estimate)
    Run with actual data files present to get precise numbers.
    """)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 65)
    print("  03 — Sample Size Report")
    print(f"  Repo root  : {REPO_ROOT}")
    print(f"  Output dir : {OUTPUT_DIR}")
    print("=" * 65)

    comparison_tbl = build_comparison_table()
    country_tbl    = build_country_detail()
    print_interpretation()

    print(f"{'=' * 65}")
    print("  Report complete.")
    print("  Key output files:")
    print("    output/sample_size_comparison.csv")
    print("    output/country_detail_matrix.csv")
    print(f"{'=' * 65}\n")


if __name__ == "__main__":
    main()
