'''
Build analysis panel for regression analysis.

Creates data/cleaned_data.csv: country × industry × year panel (1995-2019).
Outcome: ln(LAB_QI) [labour input proxy]
Treatment: ln(robot_wrkr_stock_95)_{t-1} [robots per 1000 workers, lagged]
Controls: ln(VA_PYP), ln(CAP_QI), ln(GDP), unemployment
Institutions (pre-sample 1990-1995 mean, time-invariant — the default everywhere):
  Mainline moderators: Coord (primary), AdjCov (secondary), UD (reference)
  Appendix-only: Wstat, WC, SPA_signed
  Variants per moderator:
    {name}_pre        raw pre-sample value
    {name}_pre_c      demeaned (continuous only)
    {name}_pre_binary 0/1 (binary candidates only: WC, SPA_signed)
    has_{name}        non-missing indicator (for sample filtering)
  high_coord_pre      binary robustness variant (Coord >= 4)
  has_adjcov is used by apply_sample_filter(sample="common") to restrict
  the country set to those with collective-bargaining-coverage data.
'''

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger

ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
OUTPUT_PATH = DATA_DIR / "cleaned_data.csv"

# Target sample
TARGET_YEARS = range(1995, 2020)
EU_ISO2 = {"AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK", "UK"}

# IFR industry_code -> KLEMS nace_r2_code (manufacturing)
IFR_TO_NACE = {
    "10-12": "C10-C12",
    "13-15": "C13-C15",
    "16": "C16-C18",
    "17-18": "C16-C18",
    "19": "C19",
    "19-22": "C20-C21",
    "20": "C20-C21",
    "20-21": "C20-C21",
    "20-23": "C20-C21",
    "21": "C21",
    "22": "C22-C23",
    "23": "C22-C23",
    "24": "C24-C25",
    "24-25": "C24-C25",
    "25": "C24-C25",
    "26": "C26-C27",
    "26-27": "C26-C27",
    "27": "C26-C27",
    "28": "C28",
    "29": "C29-C30",
    "29-30": "C29-C30",
    "30": "C29-C30",
    "D": "C",
    "D_other": "C31-C33",
}

EUROSTAT_GEO_TO_ISO2 = {
    "Austria": "AT", "Belgium": "BE", "Bulgaria": "BG", "Croatia": "HR", "Cyprus": "CY",
    "Czechia": "CZ", "Czech Republic": "CZ", "Denmark": "DK", "Estonia": "EE",
    "Finland": "FI", "France": "FR", "Germany": "DE", "Greece": "EL", "Hungary": "HU",
    "Ireland": "IE", "Italy": "IT", "Latvia": "LV", "Lithuania": "LT", "Luxembourg": "LU",
    "Malta": "MT", "Netherlands": "NL", "Poland": "PL", "Portugal": "PT", "Romania": "RO",
    "Slovakia": "SK", "Slovenia": "SI", "Spain": "ES", "Sweden": "SE", "United Kingdom": "UK",
}
ISO3_TO_ISO2 = {
    "AUT": "AT", "BEL": "BE", "BGR": "BG", "HRV": "HR", "CYP": "CY", "CZE": "CZ",
    "DNK": "DK", "EST": "EE", "FIN": "FI", "FRA": "FR", "DEU": "DE", "GRC": "EL",
    "HUN": "HU", "IRL": "IE", "ITA": "IT", "LVA": "LV", "LTU": "LT", "LUX": "LU",
    "MLT": "MT", "NLD": "NL", "POL": "PL", "PRT": "PT", "ROU": "RO", "SVK": "SK",
    "SVN": "SI", "ESP": "ES", "SWE": "SE", "GBR": "UK",
}


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return pd.read_csv(path)


def main():
    logger.info("Loading raw data...")

    # 1. IFR (robots)
    ifr = load_csv(DATA_DIR / "IFR_karol.csv")
    ifr = ifr[ifr["country_code"].isin(EU_ISO2)]
    ifr = ifr[ifr["industry_code"].isin(IFR_TO_NACE.keys())]
    ifr = ifr[ifr["year"].between(1993, 2019)]
    ifr["ln_robots"] = np.log(ifr["robot_wrkr_stock_95"].replace(0, np.nan))
    ifr["ln_robots_lag1"] = ifr.groupby(["country_code", "industry_code"])["ln_robots"].shift(1)
    ifr = ifr[ifr["year"] >= 1995]

    # 2. KLEMS (outcome + controls)
    klems = load_csv(DATA_DIR / "klems_growth_accounts_basic.csv")
    klems["year"] = pd.to_numeric(klems["year"], errors="coerce")
    klems["value"] = pd.to_numeric(klems["value"], errors="coerce")
    klems = klems[(klems["geo_code"].isin(EU_ISO2)) | (klems["geo_code"] == "EL")]
    klems["country_code"] = klems["geo_code"]

    vars_needed = ["LAB_QI", "VA_PYP", "CAP_QI", "CAPICT_QI", "CAPNICT_QI"]
    klems = klems[klems["var"].isin(vars_needed)]
    klems_wide = klems.pivot_table(
        index=["country_code", "nace_r2_code", "year"],
        columns="var",
        values="value",
        aggfunc="first"
    ).reset_index()

    # 3. ICTWSS (institutions, baseline 1990-1995 for max coverage)
    ICTWSS_CANDIDATES = ["Coord", "AdjCov", "UD", "Wstat", "WC", "SPA_signed"]

    ictwss = load_csv(DATA_DIR / "ictwss_institutions.csv")
    ictwss["country_code"] = ictwss["iso3"].map(ISO3_TO_ISO2)
    ictwss = ictwss[ictwss["country_code"].isin(EU_ISO2)]

    for col in ICTWSS_CANDIDATES:
        if col in ictwss.columns:
            ictwss[col] = pd.to_numeric(ictwss[col], errors="coerce")
            ictwss.loc[ictwss[col] == -99, col] = np.nan

    base_years = ictwss[ictwss["year"].between(1990, 1995)]

    def _safe_mean(s):
        v = pd.to_numeric(s, errors="coerce")
        return v.dropna().mean() if v.notna().any() else np.nan

    agg_dict = {col: (col, _safe_mean) for col in ICTWSS_CANDIDATES if col in base_years.columns}
    ictwss_baseline = base_years.groupby("country_code").agg(**agg_dict).reset_index()

    # 4. Eurostat GDP
    gdp_path = DATA_DIR / "eurostata_gdp_nama_10_gdp.csv"
    if not gdp_path.exists():
        gdp_path = DATA_DIR / "eurostat_gdp_nama_10_gdp.csv"
    gdp = load_csv(gdp_path)
    gdp["country_code"] = gdp["geo"].map(EUROSTAT_GEO_TO_ISO2)
    gdp["year"] = pd.to_numeric(gdp["TIME_PERIOD"], errors="coerce")
    gdp["gdp"] = pd.to_numeric(gdp["OBS_VALUE"], errors="coerce")
    gdp = gdp[["country_code", "year", "gdp"]].dropna(subset=["country_code"])
    gdp = gdp[gdp["country_code"].isin(EU_ISO2)]
    gdp = gdp.groupby(["country_code", "year"])["gdp"].first().reset_index()

    # 5. Eurostat unemployment
    une = load_csv(DATA_DIR / "eurostat_employment_une_rt_a.csv")
    une["country_code"] = une["geo"].map(EUROSTAT_GEO_TO_ISO2)
    une["year"] = pd.to_numeric(une["TIME_PERIOD"], errors="coerce")
    une["unemployment"] = pd.to_numeric(une["OBS_VALUE"], errors="coerce")
    une = une[["country_code", "year", "unemployment"]].dropna(subset=["country_code"])
    une = une[une["country_code"].isin(EU_ISO2)]
    une = une.groupby(["country_code", "year"])["unemployment"].first().reset_index()

    # Merge IFR with KLEMS via industry crosswalk
    ifr["nace_r2_code"] = ifr["industry_code"].map(IFR_TO_NACE)
    ifr = ifr.dropna(subset=["nace_r2_code"])
    df = ifr.merge(
        klems_wide,
        on=["country_code", "nace_r2_code", "year"],
        how="inner",
        suffixes=("", "_klems"),
    )

    # Add country-level
    df = df.merge(gdp, on=["country_code", "year"], how="left")
    df = df.merge(une, on=["country_code", "year"], how="left")
    df = df.merge(ictwss_baseline, on="country_code", how="left")

    # Build regression variables
    df["ln_hours"] = np.log(df["LAB_QI"].clip(lower=0.1))
    df["ln_va"] = np.log(df["VA_PYP"].clip(lower=0.1))
    df["ln_cap"] = np.log(df["CAP_QI"].clip(lower=0.1))
    df["ln_gdp"] = np.log(df["gdp"].clip(lower=0.1))

    # --- Legacy institution vars (backward compat) ---
    df["adjcov"] = pd.to_numeric(df["AdjCov"], errors="coerce") if "AdjCov" in df.columns else np.nan
    df["coord"] = pd.to_numeric(df["Coord"], errors="coerce") if "Coord" in df.columns else np.nan
    adj_mean = df["adjcov"].mean()
    df["adjcov_c"] = df["adjcov"] - adj_mean
    df["high_coord"] = np.where(df["coord"].notna(), (df["coord"] >= 4).astype(int), np.nan)

    # --- Pre-sample institution measures (_pre, _pre_c, has_*) ---
    # Binary indicators: WC, SPA_signed — use as-is after binary split
    # Continuous: Coord, AdjCov, UD, Wstat — create centered version
    BINARY_CANDIDATES = {"WC", "SPA_signed"}

    for col in ICTWSS_CANDIDATES:
        lc = col.lower()
        if col in df.columns:
            df[f"{lc}_pre"] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[f"{lc}_pre"] = np.nan
        df[f"has_{lc}"] = df[f"{lc}_pre"].notna()

        if col not in BINARY_CANDIDATES:
            m = df[f"{lc}_pre"].mean()
            df[f"{lc}_pre_c"] = df[f"{lc}_pre"] - m
        else:
            df[f"{lc}_pre_binary"] = np.where(
                df[f"{lc}_pre"].notna(),
                (df[f"{lc}_pre"] > 0).astype(int),
                np.nan,
            )

    df["high_coord_pre"] = np.where(
        df["coord_pre"].notna(), (df["coord_pre"] >= 4).astype(int), np.nan
    )

    logger.info(
        "Pre-sample institution columns created (1990-1995 baseline). "
        "Active hierarchy: coord primary, adjcov secondary, ud reference. "
        f"has_adjcov covers {df['has_adjcov'].sum() / len(df) * 100:.0f}% of rows."
    )

    # Drop rows with missing key vars
    required = ["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap"]
    df = df.dropna(subset=required)
    df = df[df["nace_r2_code"] != "C"].copy()

    # Entity and time indices for panel
    df["entity"] = df["country_code"] + "_" + df["industry_code"]
    df["year_int"] = df["year"].astype(int)

    # Pre-sample columns to export
    pre_cols = []
    for col in ICTWSS_CANDIDATES:
        lc = col.lower()
        pre_cols.extend([f"{lc}_pre", f"has_{lc}"])
        if col not in BINARY_CANDIDATES:
            pre_cols.append(f"{lc}_pre_c")
        else:
            pre_cols.append(f"{lc}_pre_binary")
    pre_cols.append("high_coord_pre")

    cols_out = [
        "country_code", "industry_code", "nace_r2_code", "year", "entity", "year_int",
        "ln_hours", "ln_robots", "ln_robots_lag1", "ln_va", "ln_cap", "ln_gdp",
        "unemployment", "adjcov", "coord", "adjcov_c", "high_coord",
        *pre_cols,
        "robot_wrkr_stock_95", "LAB_QI", "VA_PYP", "CAP_QI",
    ]
    cols_out = [c for c in cols_out if c in df.columns]
    df_out = df[cols_out]

    df_out.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Saved {len(df_out)} rows to {OUTPUT_PATH}")
    logger.info(f"Countries: {df_out['country_code'].nunique()}, Industries: {df_out['industry_code'].nunique()}, Years: {df_out['year'].min():.0f}-{df_out['year'].max():.0f}")

    # Summary
    logger.info(f"===== Summary of available data for regression analysis =====")
    logger.info(f"  Countries: {df_out['country_code'].nunique()}")
    logger.info(f"  Industries: {df_out['industry_code'].nunique()}")
    logger.info(f"  Years: {df_out['year'].min():.0f}-{df_out['year'].max():.0f}")

    # ICTWSS pre-sample diagnostics
    logger.info(f"\n===== ICTWSS pre-sample moderator coverage =====")
    for col in ICTWSS_CANDIDATES:
        lc = col.lower()
        has_col = f"has_{lc}"
        pre_col = f"{lc}_pre"
        if has_col in df_out.columns and pre_col in df_out.columns:
            n_ctry = df_out[df_out[has_col]]["country_code"].nunique()
            vals = df_out.groupby("country_code")[pre_col].first().dropna()
            if len(vals) > 0:
                logger.info(f"  {col}: {n_ctry} countries, mean={vals.mean():.2f}, SD={vals.std():.2f}")
            else:
                logger.info(f"  {col}: 0 countries with data")

    # Countries with NO adjcov data (dropped in coverage regressions)
    missing_adjcov = df_out.groupby("country_code")["adjcov"].apply(lambda x: x.isna().all()).pipe(lambda s: s[s].index.tolist())
    logger.info(f"  Countries WITHOUT AdjCov (dropped in coverage model): {sorted(missing_adjcov)}")
    has_adjcov_list = df_out.groupby("country_code")["adjcov"].apply(lambda x: x.notna().any()).pipe(lambda s: s[s].index.tolist())
    logger.info(f"  Countries WITH AdjCov: {sorted(has_adjcov_list)}")


if __name__ == "__main__":
    main()
