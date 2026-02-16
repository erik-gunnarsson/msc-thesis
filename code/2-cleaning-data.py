'''
Clean data in preparation for regression analysis.

Creates data/cleaned_data.csv: country × industry × year panel (1995-2019).
Outcome: ln(LAB_QI) [labour services proxy for hours]
Treatment: ln(robot_wrkr_stock_95)_{t-1} [robots per 1000 workers, lagged]
Controls: ln(VA_PYP), ln(CAP_QI), ln(GDP), unemployment
Institutions: AdjCov, Coord (baseline 1993-1995, time-invariant)
'''

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
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
    # AdjCov: use 1990-1995 (DEU/FRA have 1990, missing in 1993-1995)
    ictwss = load_csv(DATA_DIR / "ictwss_institutions.csv")
    ictwss["country_code"] = ictwss["iso3"].map(ISO3_TO_ISO2)
    ictwss = ictwss[ictwss["country_code"].isin(EU_ISO2)]
    base_years = ictwss[ictwss["year"].between(1990, 1995)]
    def _safe_mean(s):
        v = pd.to_numeric(s, errors="coerce")
        return v.dropna().mean() if v.notna().any() else np.nan

    ictwss_baseline = (
        base_years.groupby("country_code")
        .agg(AdjCov=("AdjCov", _safe_mean), Coord=("Coord", _safe_mean))
        .reset_index()
    )

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
    df["adjcov"] = pd.to_numeric(df["AdjCov"], errors="coerce")
    df["coord"] = pd.to_numeric(df["Coord"], errors="coerce")

    # Institutional moderation vars (for equation 2/3 scripts; no wrangling in equation files)
    adj_mean = df["adjcov"].mean()
    df["adjcov_centered"] = df["adjcov"] - adj_mean
    df["high_coord"] = np.where(df["coord"].notna(), (df["coord"] >= 4).astype(int), np.nan)

    # Industry heterogeneity: high robot-use industries (C26-C27, C28, C29-C30)
    high_robot_nace = {"C26-C27", "C28", "C29-C30"}
    df["high_robot_industry"] = df["nace_r2_code"].isin(high_robot_nace).astype(int)

    # Drop rows with missing key vars
    required = ["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap"]
    df = df.dropna(subset=required)

    # Entity and time indices for panel
    df["entity"] = df["country_code"] + "_" + df["industry_code"]
    df["year_int"] = df["year"].astype(int)

    cols_out = [
        "country_code", "industry_code", "nace_r2_code", "year", "entity", "year_int",
        "ln_hours", "ln_robots", "ln_robots_lag1", "ln_va", "ln_cap", "ln_gdp",
        "unemployment", "adjcov", "coord", "adjcov_centered", "high_coord", "high_robot_industry",
        "robot_wrkr_stock_95", "LAB_QI", "VA_PYP", "CAP_QI",
    ]
    cols_out = [c for c in cols_out if c in df.columns]
    df_out = df[cols_out]

    df_out.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Saved {len(df_out)} rows to {OUTPUT_PATH}")
    logger.info(f"Countries: {df_out['country_code'].nunique()}, Industries: {df_out['industry_code'].nunique()}, Years: {df_out['year'].min():.0f}-{df_out['year'].max():.0f}")


    # Indepth Summary of avaible data for regression analysis
    logger.info(f"===== Summary of available data for regression analysis =====\n\n\n")
    logger.info(f"===== Countries: {df_out['country_code'].nunique()}")
    logger.info(f"===== Industries: {df_out['industry_code'].nunique()}")
    logger.info(f"===== Years: {df_out['year'].min():.0f}-{df_out['year'].max():.0f}")
    logger.info(f"===== AdjCov: {df_out['adjcov'].mean():.2f}")
    logger.info(f"===== Coord: {df_out['coord'].mean():.2f}")
    logger.info(f"===== High Coordination: {df_out['high_coord'].mean():.2f}")
    logger.info(f"===== High Robot Industry: {df_out['high_robot_industry'].mean():.2f}")
    
    # Countries with NO adjcov data (dropped in coverage regressions)
    missing_adjcov = df_out.groupby("country_code")["adjcov"].apply(lambda x: x.isna().all()).pipe(lambda s: s[s].index.tolist())
    logger.info(f"===== Countries WITHOUT AdjCov (dropped in coverage model): {sorted(missing_adjcov)}")
    # Countries WITH adjcov data
    has_adjcov = df_out.groupby("country_code")["adjcov"].apply(lambda x: x.notna().any()).pipe(lambda s: s[s].index.tolist())
    logger.info(f"===== Countries WITH AdjCov: {sorted(has_adjcov)}")


if __name__ == "__main__":
    main()
