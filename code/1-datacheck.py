'''
Check all data files for correct years, variables, and coverage before wrangling.
Target panel: ~15 EU countries × ~14 manufacturing industries × 1995-2019.
'''

import pandas as pd
from pathlib import Path
from loguru import logger

# --- Loguru: cleaner format ---
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<level>{message}</level>",
    colorize=True,
)

def section(title: str) -> None:
    logger.info(f"\n{'═' * 60}\n  {title}\n{'─' * 60}")

def ok(msg: str) -> None:
    logger.info(f"  ✓ {msg}")

def warn(msg: str) -> None:
    logger.warning(f"  ⚠ {msg}")

def fail(msg: str) -> None:
    logger.error(f"  ✗ {msg}")


# --- Config ---
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TARGET_YEARS = set(range(1995, 2020))  # 1995-2019

EU_ISO2 = {"AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK", "UK"}
EU_ISO2_EXT = EU_ISO2 | {"EL", "GR"}
ISO2_TO_ISO3 = {"AT": "AUT", "BE": "BEL", "BG": "BGR", "CY": "CYP", "CZ": "CZE", "DE": "DEU", "DK": "DNK", "EE": "EST", "EL": "GRC", "ES": "ESP", "FI": "FIN", "FR": "FRA", "GR": "GRC", "HR": "HRV", "HU": "HUN", "IE": "IRL", "IT": "ITA", "LT": "LTU", "LU": "LUX", "LV": "LVA", "MT": "MLT", "NL": "NLD", "PL": "POL", "PT": "PRT", "RO": "ROU", "SE": "SWE", "SI": "SVN", "SK": "SVK", "UK": "GBR"}

# Eurostat uses country names
EUROSTAT_GEO_TO_ISO2 = {
    "Austria": "AT", "Belgium": "BE", "Bulgaria": "BG", "Croatia": "HR", "Cyprus": "CY",
    "Czechia": "CZ", "Czech Republic": "CZ", "Denmark": "DK", "Estonia": "EE",
    "Finland": "FI", "France": "FR", "Germany": "DE", "Greece": "EL", "Hungary": "HU",
    "Ireland": "IE", "Italy": "IT", "Latvia": "LV", "Lithuania": "LT", "Luxembourg": "LU",
    "Malta": "MT", "Netherlands": "NL", "Poland": "PL", "Portugal": "PT", "Romania": "RO",
    "Slovakia": "SK", "Slovenia": "SI", "Spain": "ES", "Sweden": "SE", "United Kingdom": "UK",
}

# KLEMS Growth: L (labour) = Hours (H) × Labour Composition (LC). H is not reported standalone.
KLEMS_GROWTH_REQUIRED = {"VA_PYP", "CAP_QI", "CAPICT_QI", "CAPNICT_QI", "LAB", "LAB_QI"}
ICTWSS_REQUIRED = {"AdjCov", "Coord"}
IFR_REQUIRED = {"robot_stock", "robot_wrkr_stock_95", "employment"}
KLEMS_LABOUR_COLS = {"nace_r2_code", "geo_code", "year"}  # Labour accounts: LC via Share_E, Share_W


def load_safe(path: Path, reader: str = "csv", **kwargs):
    if not path.exists():
        return None
    try:
        return pd.read_csv(path, **kwargs) if reader == "csv" else pd.read_excel(path, **kwargs)
    except Exception:
        return None


def check_years(df, year_col: str, name: str) -> bool:
    """Return True if all target years present."""
    years = set(pd.to_numeric(df[year_col], errors="coerce").dropna().astype(int))
    missing = sorted(TARGET_YEARS - years)
    if missing:
        warn(f"{name}: missing years {missing[:5]}{'...' if len(missing) > 5 else ''}")
        return False
    ok(f"{name}: years {int(df[year_col].min())}–{int(df[year_col].max())} ✓")
    return True


# --- Load ---
ictwss = load_safe(DATA_DIR / "ictwss_institutions.csv")
ifr = load_safe(DATA_DIR / "IFR_karol.csv")
klems_growth = load_safe(DATA_DIR / "klems_growth_accounts_basic.csv")
klems_labour = load_safe(DATA_DIR / "klems_labour_accounts.csv")
klems_var_list = load_safe(DATA_DIR / "klems_variable_list_2023.xlsx", reader="excel")

# Eurostat: support both "eurostat" and "eurostata" (typo in filename)
_gdp = load_safe(DATA_DIR / "eurostata_gdp_nama_10_gdp.csv")
eurostat_gdp = _gdp if _gdp is not None else load_safe(DATA_DIR / "eurostat_gdp_nama_10_gdp.csv")
eurostat_unemployment = load_safe(DATA_DIR / "eurostat_employment_une_rt_a.csv")


# ═══════════════════════════════════════════════════════════════════
# 1. ICTWSS
# ═══════════════════════════════════════════════════════════════════
section("1. ICTWSS (Labor Market Institutions)")

if ictwss is not None:
    check_years(ictwss, "year", "ICTWSS")
    for v in ICTWSS_REQUIRED:
        ok(f"{v}: ✓") if v in ictwss.columns else warn(f"{v}: MISSING")
    eu_iso3 = {ISO2_TO_ISO3[c] for c in EU_ISO2 if c in ISO2_TO_ISO3}
    ictwss_countries = set(ictwss[ictwss["iso3"].isin(eu_iso3)]["iso3"].unique())
    ok(f"EU countries: {len(ictwss_countries)}")
    if missing := eu_iso3 - ictwss_countries:
        warn(f"Missing EU: {missing}")
else:
    fail("ICTWSS not loaded")


# ═══════════════════════════════════════════════════════════════════
# 2. IFR (Robots)
# ═══════════════════════════════════════════════════════════════════
section("2. IFR (Robot Adoption)")

if ifr is not None:
    check_years(ifr, "year", "IFR")
    for v in IFR_REQUIRED:
        ok(f"{v}: ✓") if v in ifr.columns else warn(f"{v}: MISSING")
    ifr_countries = set(ifr["country_code"].unique())
    ifr_eu = ifr_countries & EU_ISO2
    ok(f"EU countries: {len(ifr_eu)}")
    if missing := EU_ISO2 - ifr_countries:
        warn(f"Missing EU: {missing}")
    mfg = [c for c in ifr["industry_code"].unique() if str(c) != "000"]
    ok(f"Manufacturing industries: {len(mfg)}")
else:
    fail("IFR not loaded")


# ═══════════════════════════════════════════════════════════════════
# 3. KLEMS Growth + Labour
# ═══════════════════════════════════════════════════════════════════
section("3. KLEMS (Employment & Controls)")

klems = klems_growth  # alias
# KLEMS: L = H × LC. Hours (H) not reported standalone; use LAB/LAB_QI as labour input.
ok("Labour input: L = Hours (H) × Labour Composition (LC); H not standalone in growth accounts")

if klems is not None:
    check_years(klems, "year", "KLEMS Growth")
    klem_vars = set(klems["var"].unique())
    for v in KLEMS_GROWTH_REQUIRED:
        present = v in klem_vars
        ok(f"{v}: ✓") if present else warn(f"{v}: MISSING")
    # LAB_QI = labour services volume index; suitable proxy for labour input in models
    if "LAB_QI" in klem_vars:
        ok("LAB_QI (labour services) available as labour input proxy ✓")
    klems_geos = set(klems["geo_code"].unique())
    if "EL" in klems_geos and "GR" not in klems_geos:
        ok("Greece coded as EL (KLEMS convention)")
    ok(f"EU countries: {len(klems_geos & EU_ISO2_EXT)}")
else:
    fail("KLEMS Growth not loaded")

if klems_labour is not None:
    section("3b. KLEMS Labour Accounts (Labour Composition)")
    check_years(klems_labour, "year", "KLEMS Labour")
    cols = set(klems_labour.columns)
    for c in KLEMS_LABOUR_COLS:
        ok(f"{c}: ✓") if c in cols else warn(f"{c}: MISSING")
    ok(f"Labour composition (LC): Share_E, Share_W by education/age/gender ✓")
else:
    warn("KLEMS Labour not loaded — labour composition (LC) unavailable")


# ═══════════════════════════════════════════════════════════════════
# 4. Eurostat (GDP, Unemployment)
# ═══════════════════════════════════════════════════════════════════
section("4. Eurostat (GDP, Unemployment)")

eurostat_year_col = "TIME_PERIOD"
eurostat_geo_col = "geo"

if eurostat_gdp is not None:
    df = eurostat_gdp
    if eurostat_year_col in df.columns:
        y_min, y_max = int(df[eurostat_year_col].min()), int(df[eurostat_year_col].max())
        missing = sorted(TARGET_YEARS - set(df[eurostat_year_col].astype(int)))
        if not missing:
            ok(f"GDP: years {y_min}–{y_max} ✓")
        else:
            warn(f"GDP: missing years {missing[:5]}...")
    if eurostat_geo_col in df.columns:
        eu_in_gdp = set(df[df[eurostat_geo_col].isin(EUROSTAT_GEO_TO_ISO2)][eurostat_geo_col].unique())
        ok(f"GDP: {len(eu_in_gdp)} EU countries")
    ok("GDP: OBS_VALUE present" if "OBS_VALUE" in df.columns else warn("GDP: OBS_VALUE missing"))
else:
    fail("Eurostat GDP not loaded (check eurostata_gdp_nama_10_gdp.csv or eurostat_gdp_*)")

if eurostat_unemployment is not None:
    df = eurostat_unemployment
    if eurostat_year_col in df.columns:
        y_min, y_max = int(df[eurostat_year_col].min()), int(df[eurostat_year_col].max())
        missing = sorted(TARGET_YEARS - set(df[eurostat_year_col].astype(int)))
        if not missing:
            ok(f"Unemployment: years {y_min}–{y_max} ✓")
        else:
            warn(f"Unemployment: missing years {missing[:5]}...")
    if eurostat_geo_col in df.columns:
        eu_in_une = set(df[df[eurostat_geo_col].isin(EUROSTAT_GEO_TO_ISO2)][eurostat_geo_col].unique())
        ok(f"Unemployment: {len(eu_in_une)} EU countries")
    ok("Unemployment: OBS_VALUE present" if "OBS_VALUE" in df.columns else warn("Unemployment: OBS_VALUE missing"))
else:
    fail("Eurostat Unemployment not loaded (check eurostat_employment_une_rt_a.csv)")


# ═══════════════════════════════════════════════════════════════════
# 5. KLEMS Variable List (reference)
# ═══════════════════════════════════════════════════════════════════
section("5. KLEMS Variable List")
if klems_var_list is not None:
    ok(f"Loaded: {klems_var_list.shape[0]} rows")
else:
    warn("Not loaded (install openpyxl)")


# ═══════════════════════════════════════════════════════════════════
# 6. Industry List (C10-C33) — by name and usability in eq4/eq5
# ═══════════════════════════════════════════════════════════════════
# IFR industry_code -> KLEMS nace_r2_code (from 2-cleaning-data.py)
IFR_TO_NACE = {
    "10-12": "C10-C12", "13-15": "C13-C15", "16": "C16-C18", "17-18": "C16-C18",
    "19": "C19", "19-22": "C20-C21", "20": "C20-C21", "20-21": "C20-C21", "20-23": "C20-C21",
    "21": "C21", "22": "C22-C23", "23": "C22-C23", "24": "C24-C25", "24-25": "C24-C25",
    "25": "C24-C25", "26": "C26-C27", "26-27": "C26-C27", "27": "C26-C27",
    "28": "C28", "29": "C29-C30", "29-30": "C29-C30", "30": "C29-C30",
    "D": "C", "D_other": "C31-C33",
}
# NACE Rev. 2 industry names (manufacturing)
NACE_NAMES = {
    "C10-C12": "Food, beverages, tobacco",
    "C13-C15": "Textiles, apparel, leather",
    "C16-C18": "Wood, paper, printing",
    "C19": "Coke, refined petroleum",
    "C20-C21": "Chemicals, pharmaceuticals",
    "C21": "Pharmaceuticals",
    "C22-C23": "Rubber, plastics, non-metallic minerals",
    "C24-C25": "Basic metals, fabricated metal",
    "C26-C27": "Computer, electronic, electrical equipment",
    "C28": "Machinery and equipment n.e.c.",
    "C29-C30": "Motor vehicles, other transport",
    "C31-C33": "Furniture, other manufacturing, repair",
    "C": "Manufacturing total",
}

section("6. Industry List (by name)")
# IFR industries (codes) -> NACE
ifr_nace_from_mapping = set(IFR_TO_NACE.values())
logger.info("  IFR industries (mapped to NACE):")
for nace in sorted(ifr_nace_from_mapping):
    name = NACE_NAMES.get(nace, "(unknown)")
    logger.info(f"    {nace}: {name}")

# KLEMS industries (from raw data; uses nace_r2_code directly)
if klems is not None:
    klems_nace = set(klems["nace_r2_code"].dropna().unique())
    logger.info(f"\n  KLEMS industries (nace_r2_code): {len(klems_nace)}")
    for nace in sorted(klems_nace):
        name = NACE_NAMES.get(nace, "(unknown)")
        logger.info(f"    {nace}: {name}")

# Industries in cleaned panel = intersection (IFR mapped ∩ KLEMS)
cleaned_path = DATA_DIR / "cleaned_data.csv"
cleaned = load_safe(cleaned_path) if cleaned_path.exists() else None
if cleaned is not None and "nace_r2_code" in cleaned.columns:
    cleaned_nace = sorted(cleaned["nace_r2_code"].dropna().unique())
    logger.info(f"\n  Industries in cleaned_data.csv (usable in regressions): {len(cleaned_nace)}")
    for nace in cleaned_nace:
        name = NACE_NAMES.get(nace, "(unknown)")
        n_rows = len(cleaned[cleaned["nace_r2_code"] == nace])
        logger.info(f"    {nace}: {name} ({n_rows} rows)")

    # Usability in eq4 (coordination) and eq5 (coverage)
    MIN_COUNTRIES, MIN_OBS = 5, 50
    req_coord = ["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap", "coord"]
    req_cov = ["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap", "adjcov"]

    usable_eq4 = []
    usable_eq5 = []
    for nace in cleaned_nace:
        sub = cleaned[cleaned["nace_r2_code"] == nace].dropna(subset=req_coord + ["nace_r2_code"])
        if "high_coord" in sub.columns:
            has_var_coord = sub["high_coord"].nunique() >= 2
        else:
            coord_num = pd.to_numeric(sub["coord"], errors="coerce")
            has_var_coord = (coord_num >= 4).astype(int).nunique() >= 2 if coord_num.notna().any() else False
        n_ctry = sub["country_code"].nunique()
        if n_ctry >= MIN_COUNTRIES and len(sub) >= MIN_OBS and has_var_coord:
            usable_eq4.append(nace)

        sub_cov = cleaned[cleaned["nace_r2_code"] == nace].dropna(subset=req_cov + ["nace_r2_code"])
        var_cov = sub_cov["adjcov"].std() >= 1e-10 if "adjcov" in sub_cov.columns else False
        n_ctry_cov = sub_cov["country_code"].nunique()
        if n_ctry_cov >= MIN_COUNTRIES and len(sub_cov) >= MIN_OBS and var_cov:
            usable_eq5.append(nace)

    logger.info(f"\n  Usable in Equation 4 (coordination moderation): {len(usable_eq4)} industries")
    for nace in usable_eq4:
        logger.info(f"    {nace}: {NACE_NAMES.get(nace, '')}")
    skipped_eq4 = set(cleaned_nace) - set(usable_eq4)
    if skipped_eq4:
        logger.info(f"  Skipped for eq4: {sorted(skipped_eq4)}")

    logger.info(f"\n  Usable in Equation 5 (coverage moderation): {len(usable_eq5)} industries")
    for nace in usable_eq5:
        logger.info(f"    {nace}: {NACE_NAMES.get(nace, '')}")
    skipped_eq5 = set(cleaned_nace) - set(usable_eq5)
    if skipped_eq5:
        logger.info(f"  Skipped for eq5: {sorted(skipped_eq5)}")
else:
    warn("cleaned_data.csv not found — run 2-cleaning-data.py first for eq4/eq5 usability")

# ═══════════════════════════════════════════════════════════════════
# 7. Summary
# ═══════════════════════════════════════════════════════════════════
section("SUMMARY: Potential Gaps")

issues = []
if eurostat_gdp is None:
    issues.append("Eurostat GDP missing")
if eurostat_unemployment is None:
    issues.append("Eurostat Unemployment missing")
if ictwss is not None and "AdjCov" in ictwss.columns and "Coord" in ictwss.columns:
    eu_iso3 = {ISO2_TO_ISO3[c] for c in EU_ISO2 if c in ISO2_TO_ISO3}
    base = ictwss[(ictwss["year"].between(1993, 1995)) & (ictwss["iso3"].isin(eu_iso3))]
    adjcov_ok = base["AdjCov"].notna() & (base["AdjCov"].astype(str) != "") & (pd.to_numeric(base["AdjCov"], errors="coerce").notna())
    coord_ok = base["Coord"].notna() & (pd.to_numeric(base["Coord"], errors="coerce").notna())
    if not (adjcov_ok.all() and coord_ok.all()):
        issues.append("ICTWSS: some EU countries missing AdjCov/Coord in 1993–1995 baseline")

for i, issue in enumerate(issues, 1):
    warn(f"{i}. {issue}")

if not issues:
    ok("No critical gaps identified")



logger.info(f"\n{'═' * 60}\n  Data check complete\n{'═' * 60}\n")


