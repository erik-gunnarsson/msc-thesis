from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from _common import (
    DATA_DIR,
    EU27_ISO2,
    EU27_ISO3,
    ISO3_TO_ISO2,
    OUTPUT_DIR,
    WIOD_TO_NACE,
    build_ifr_main_panel,
    build_wiod_trade_panel,
    ensure_output_dir,
    load_ictwss_baseline,
    print_table,
)


SEA_PATH = DATA_DIR / "WIOTS_SEA" / "Socio_Economic_Accounts.xlsx"
MERGE_SCENARIO_B_PATH = OUTPUT_DIR / "merge_scenario_B_ifr_trade_ictwss.csv"
SEA_VARIABLES = ["VA", "CAP", "GO", "H_EMPE"]
SEA_MANUFACTURING_CODES = [
    "C10-C12",
    "C13-C15",
    "C16",
    "C17",
    "C18",
    "C19",
    "C20",
    "C21",
    "C22",
    "C23",
    "C24",
    "C25",
    "C26",
    "C27",
    "C28",
    "C29",
    "C30",
    "C31_C32",
    "C33",
]
SEA_YEAR_COLUMNS = list(range(2000, 2015))
ANALYSIS_YEARS = list(range(2001, 2015))
MAIN_THRESHOLD = 20
RESTRICTED_THRESHOLD = 14

EUROSTAT_GEO_TO_ISO2 = {
    "Austria": "AT",
    "Belgium": "BE",
    "Bulgaria": "BG",
    "Croatia": "HR",
    "Cyprus": "CY",
    "Czechia": "CZ",
    "Czech Republic": "CZ",
    "Denmark": "DK",
    "Estonia": "EE",
    "Finland": "FI",
    "France": "FR",
    "Germany": "DE",
    "Greece": "EL",
    "Hungary": "HU",
    "Ireland": "IE",
    "Italy": "IT",
    "Latvia": "LV",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Malta": "MT",
    "Netherlands": "NL",
    "Poland": "PL",
    "Portugal": "PT",
    "Romania": "RO",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "Spain": "ES",
    "Sweden": "SE",
    "United Kingdom": "UK",
}

BUCKET_MAP = {
    "C29-C30": 1,
    "C26-C27": 2,
    "C28": 2,
    "C24-C25": 3,
    "C19": 4,
    "C20-C21": 4,
    "C22-C23": 4,
    "C10-C12": 5,
    "C13-C15": 5,
    "C16-C18": 5,
    "C31-C33": 5,
}
BUCKET_NAMES = {
    1: "Transport equipment",
    2: "Electro-mechanical capital goods",
    3: "Metals",
    4: "Process and materials",
    5: "Low-tech / traditional",
}
EXPECTED_BUCKETS = set(BUCKET_NAMES.keys())
EXPECTED_COLLAPSED_NACE = sorted(set(WIOD_TO_NACE.values()))
SUMMARY_PATH = OUTPUT_DIR / "regression_ready_summary.txt"


@dataclass(frozen=True)
class ModelSpec:
    model: str
    description: str
    required_variables: list[str]
    threshold: int
    source_panel: str = "base"
    require_all_buckets: bool = False
    restrict_adjcov_countries: bool = False
    use_coord_binary: bool = False
    timevarying_moderator: str | None = None
    balanced: bool = False
    year_min: int | None = None
    year_max: int | None = None
    bucket_value: int | None = None


def load_phase1_support() -> pd.DataFrame:
    if MERGE_SCENARIO_B_PATH.exists():
        df = pd.read_csv(MERGE_SCENARIO_B_PATH)
    else:
        ifr = build_ifr_main_panel()
        wiod = build_wiod_trade_panel(cache_path=OUTPUT_DIR / "wiod_trade_panel.csv")
        baseline, _ = load_ictwss_baseline()
        df = ifr.merge(
            wiod,
            on=["country_code", "nace_r2_code", "year"],
            how="inner",
            suffixes=("_ifr", "_wiod"),
        )
        df["entity"] = df["country_code"] + "_" + df["nace_r2_code"]
        df = df.merge(
            baseline[
                [
                    "country_code",
                    "ud_pre",
                    "coord_pre",
                    "adjcov_pre",
                    "ud_available",
                    "coord_available",
                    "adjcov_available",
                ]
            ],
            on="country_code",
            how="left",
        )
        df["both_available"] = df["ud_available"] & df["coord_available"]
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df


def _sum_min_count(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().any():
        return float(numeric.sum())
    return np.nan


def load_sea_long() -> pd.DataFrame:
    if not SEA_PATH.exists():
        raise FileNotFoundError(f"Missing WIOD SEA workbook: {SEA_PATH}")

    df = pd.read_excel(SEA_PATH, sheet_name="DATA")
    expected_cols = {"country", "variable", "code"}
    if not expected_cols.issubset(df.columns):
        raise RuntimeError(f"Unexpected SEA columns in {SEA_PATH}")

    df = df[
        df["country"].isin(EU27_ISO3)
        & df["code"].isin(SEA_MANUFACTURING_CODES)
        & df["variable"].isin(SEA_VARIABLES)
    ].copy()

    long = df.melt(
        id_vars=["country", "variable", "code"],
        value_vars=SEA_YEAR_COLUMNS,
        var_name="year",
        value_name="value",
    )
    long["year"] = pd.to_numeric(long["year"], errors="coerce").astype(int)
    long["country_code"] = long["country"].map(ISO3_TO_ISO2)
    long["nace_r2_code"] = long["code"].map(WIOD_TO_NACE)
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    return long


def build_sea_outputs(sea_long: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    full_grid = pd.MultiIndex.from_product(
        [sorted(EU27_ISO2), SEA_YEAR_COLUMNS],
        names=["country_code", "year"],
    ).to_frame(index=False)

    raw_counts = (
        sea_long.groupby(["country_code", "year", "variable"])["value"]
        .apply(lambda s: int(pd.to_numeric(s, errors="coerce").notna().sum()))
        .unstack("variable")
        .reset_index()
    )
    raw_counts = raw_counts.rename(
        columns={
            "VA": "va_non_missing_19",
            "CAP": "cap_non_missing_19",
            "GO": "go_non_missing_19",
            "H_EMPE": "h_empe_non_missing_19",
        }
    )
    raw_counts = full_grid.merge(raw_counts, on=["country_code", "year"], how="left")
    for col in ["va_non_missing_19", "cap_non_missing_19", "go_non_missing_19", "h_empe_non_missing_19"]:
        raw_counts[col] = raw_counts[col].fillna(0).astype(int)
    raw_counts["va_complete_19"] = raw_counts["va_non_missing_19"] == 19
    raw_counts["cap_complete_19"] = raw_counts["cap_non_missing_19"] == 19
    raw_counts["go_complete_19"] = raw_counts["go_non_missing_19"] == 19
    raw_counts["h_empe_complete_19"] = raw_counts["h_empe_non_missing_19"] == 19

    collapsed = (
        sea_long.dropna(subset=["nace_r2_code"])
        .groupby(["country_code", "nace_r2_code", "year", "variable"], as_index=False)
        .agg(value=("value", _sum_min_count))
    )

    collapsed_counts = (
        collapsed.groupby(["country_code", "year", "variable"])["value"]
        .apply(lambda s: int(pd.to_numeric(s, errors="coerce").notna().sum()))
        .unstack("variable")
        .reset_index()
    )
    collapsed_counts = collapsed_counts.rename(
        columns={
            "VA": "va_non_missing_11",
            "CAP": "cap_non_missing_11",
            "GO": "go_non_missing_11",
            "H_EMPE": "h_empe_non_missing_11",
        }
    )
    collapsed_counts = full_grid.merge(collapsed_counts, on=["country_code", "year"], how="left")
    for col in ["va_non_missing_11", "cap_non_missing_11", "go_non_missing_11", "h_empe_non_missing_11"]:
        collapsed_counts[col] = collapsed_counts[col].fillna(0).astype(int)
    collapsed_counts["va_complete_11"] = collapsed_counts["va_non_missing_11"] == 11
    collapsed_counts["cap_complete_11"] = collapsed_counts["cap_non_missing_11"] == 11
    collapsed_counts["go_complete_11"] = collapsed_counts["go_non_missing_11"] == 11
    collapsed_counts["h_empe_complete_11"] = collapsed_counts["h_empe_non_missing_11"] == 11

    coverage = raw_counts.merge(collapsed_counts, on=["country_code", "year"], how="left")
    coverage.to_csv(OUTPUT_DIR / "sea_coverage_matrix.csv", index=False)

    sea_panel = (
        collapsed.pivot_table(
            index=["country_code", "nace_r2_code", "year"],
            columns="variable",
            values="value",
            aggfunc="first",
        )
        .reset_index()
        .sort_values(["country_code", "nace_r2_code", "year"])
        .reset_index(drop=True)
    )
    sea_panel.columns.name = None
    for col in SEA_VARIABLES:
        if col not in sea_panel.columns:
            sea_panel[col] = np.nan
    sea_panel["ln_va_sea"] = np.log(sea_panel["VA"].clip(lower=0.1))
    sea_panel["ln_cap_sea"] = np.log(sea_panel["CAP"].clip(lower=0.1))

    complete_country_years = coverage[
        coverage["va_complete_19"] & coverage["cap_complete_19"] & coverage["go_complete_19"]
    ]
    complete_countries = (
        complete_country_years.groupby("country_code")["year"].nunique().eq(len(SEA_YEAR_COLUMNS)).sum()
    )
    unmatched_raw_codes = sorted(set(SEA_MANUFACTURING_CODES) - set(WIOD_TO_NACE))
    unexpected_collapsed = sorted(set(sea_panel["nace_r2_code"].dropna().unique()) - set(EXPECTED_COLLAPSED_NACE))
    missing_collapsed = sorted(set(EXPECTED_COLLAPSED_NACE) - set(sea_panel["nace_r2_code"].dropna().unique()))
    sea_meta = {
        "complete_va_cap_countries": int(complete_countries),
        "unmatched_raw_codes": unmatched_raw_codes,
        "unexpected_collapsed_codes": unexpected_collapsed,
        "missing_collapsed_codes": missing_collapsed,
    }
    return coverage, sea_panel, sea_meta


def load_gdp_growth() -> pd.DataFrame:
    gdp_path = DATA_DIR / "eurostata_gdp_nama_10_gdp.csv"
    if not gdp_path.exists():
        raise FileNotFoundError(f"Missing GDP file: {gdp_path}")

    gdp = pd.read_csv(gdp_path)
    gdp["country_code"] = gdp["geo"].map(EUROSTAT_GEO_TO_ISO2)
    gdp["year"] = pd.to_numeric(gdp["TIME_PERIOD"], errors="coerce")
    gdp["gdp"] = pd.to_numeric(gdp["OBS_VALUE"], errors="coerce")
    gdp = gdp[["country_code", "year", "gdp"]].dropna(subset=["country_code", "year"])
    gdp = gdp[gdp["country_code"].isin(EU27_ISO2)].copy()
    gdp = gdp.groupby(["country_code", "year"], as_index=False)["gdp"].first()
    gdp = gdp.sort_values(["country_code", "year"]).reset_index(drop=True)
    gdp["gdp_growth"] = gdp.groupby("country_code")["gdp"].transform(
        lambda s: np.log(s.clip(lower=0.1)).diff()
    )
    return gdp


def load_unemployment() -> pd.DataFrame:
    une_path = DATA_DIR / "eurostat_employment_une_rt_a.csv"
    if not une_path.exists():
        raise FileNotFoundError(f"Missing unemployment file: {une_path}")

    une = pd.read_csv(une_path)
    une["country_code"] = une["geo"].map(EUROSTAT_GEO_TO_ISO2)
    une["year"] = pd.to_numeric(une["TIME_PERIOD"], errors="coerce")
    une["unemployment"] = pd.to_numeric(une["OBS_VALUE"], errors="coerce")
    une = une[["country_code", "year", "unemployment"]].dropna(subset=["country_code", "year"])
    une = une[une["country_code"].isin(EU27_ISO2)].copy()
    une = une.groupby(["country_code", "year"], as_index=False)["unemployment"].first()
    return une


def load_timevarying_ictwss() -> pd.DataFrame:
    path = DATA_DIR / "ictwss_institutions.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing ICTWSS file: {path}")

    df = pd.read_csv(path)
    df["country_code"] = df["iso3"].map(ISO3_TO_ISO2)
    df = df[df["country_code"].isin(EU27_ISO2)].copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    for src, dst in [("UD", "ud"), ("Coord", "coord"), ("AdjCov", "adjcov")]:
        df[dst] = pd.to_numeric(df[src], errors="coerce")
        df.loc[df[dst] == -99, dst] = np.nan
    return df[["country_code", "year", "ud", "coord", "adjcov"]]


def load_klems_controls() -> pd.DataFrame:
    path = DATA_DIR / "klems_growth_accounts_basic.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing KLEMS file: {path}")

    klems = pd.read_csv(path)
    klems["year"] = pd.to_numeric(klems["year"], errors="coerce")
    klems["value"] = pd.to_numeric(klems["value"], errors="coerce")
    klems = klems[klems["var"].isin(["VA_PYP", "CAP_QI"])].copy()
    klems["country_code"] = klems["geo_code"]
    klems = klems[klems["country_code"].isin(set(EU27_ISO2) | {"EL"})]
    wide = (
        klems.pivot_table(
            index=["country_code", "nace_r2_code", "year"],
            columns="var",
            values="value",
            aggfunc="first",
        )
        .reset_index()
    )
    wide.columns.name = None
    wide["ln_va_klems"] = np.log(wide["VA_PYP"].clip(lower=0.1))
    wide["ln_cap_klems"] = np.log(wide["CAP_QI"].clip(lower=0.1))
    return wide


def prepare_panels(
    phase1: pd.DataFrame,
    sea_panel: pd.DataFrame,
    gdp: pd.DataFrame,
    unemployment: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    panel = phase1.copy()
    panel["year"] = pd.to_numeric(panel["year"], errors="coerce")
    panel["gross_exports_usd_m"] = pd.to_numeric(panel["gross_exports_usd_m"], errors="coerce")
    panel["robot_wrkr_stock_95"] = pd.to_numeric(panel["robot_wrkr_stock_95"], errors="coerce")
    panel["ln_exports"] = np.log(panel["gross_exports_usd_m"].clip(lower=0.1))
    panel = panel.sort_values(["entity", "year"]).reset_index(drop=True)
    panel["ln_robots"] = np.log(panel["robot_wrkr_stock_95"].replace(0, np.nan))
    panel["ln_robots_lag1"] = panel.groupby("entity")["ln_robots"].shift(1)

    panel = panel.merge(
        sea_panel[["country_code", "nace_r2_code", "year", "VA", "CAP", "GO", "H_EMPE", "ln_va_sea", "ln_cap_sea"]],
        on=["country_code", "nace_r2_code", "year"],
        how="left",
    )
    panel = panel.merge(gdp[["country_code", "year", "gdp", "gdp_growth"]], on=["country_code", "year"], how="left")
    panel = panel.merge(unemployment, on=["country_code", "year"], how="left")
    panel["bucket"] = panel["nace_r2_code"].map(BUCKET_MAP)
    panel["bucket_name"] = panel["bucket"].map(BUCKET_NAMES)
    panel = panel[panel["year"].between(ANALYSIS_YEARS[0], ANALYSIS_YEARS[-1])].copy()

    no_controls = panel.dropna(subset=["ln_exports", "ln_robots_lag1"]).copy()
    base = no_controls.dropna(subset=["ln_va_sea", "ln_cap_sea"]).copy()
    base_tv = base.merge(load_timevarying_ictwss(), on=["country_code", "year"], how="left")
    return {
        "panel": panel,
        "no_controls": no_controls,
        "base": base,
        "base_tv": base_tv,
    }


def entity_count(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    return df[["country_code", "nace_r2_code"]].drop_duplicates().shape[0]


def model_specs() -> list[ModelSpec]:
    specs = [
        ModelSpec("EQ1", "Baseline: robots -> labour input", [], MAIN_THRESHOLD),
        ModelSpec("EQ1_GDP", "Baseline + GDP control", ["gdp_growth"], MAIN_THRESHOLD),
        ModelSpec("EQ2_COORD", "Primary focal moderation by coord", ["coord_pre"], MAIN_THRESHOLD),
        ModelSpec("EQ2_ADJCOV", "Secondary focal moderation by adjcov (restricted)", ["adjcov_pre"], RESTRICTED_THRESHOLD),
        ModelSpec("EQ2_UD", "Reference moderation by ud", ["ud_pre"], MAIN_THRESHOLD),
        ModelSpec("EQ3", "Bucket heterogeneity", ["bucket"], MAIN_THRESHOLD, require_all_buckets=True),
        ModelSpec("EQ4_COORD", "Bucket x coord (primary focal)", ["coord_pre", "bucket"], MAIN_THRESHOLD, require_all_buckets=True),
        ModelSpec("EQ4_ADJCOV", "Bucket x adjcov (secondary focal, restricted)", ["adjcov_pre", "bucket"], RESTRICTED_THRESHOLD, require_all_buckets=True),
        ModelSpec("EQ4_UD", "Bucket x ud (reference)", ["ud_pre", "bucket"], MAIN_THRESHOLD, require_all_buckets=True),
        ModelSpec("ROB_COMMON_COORD", "coord on adjcov-available countries only", ["coord_pre"], RESTRICTED_THRESHOLD, restrict_adjcov_countries=True),
        ModelSpec("ROB_COORD_BIN", "Binary coord (>=4) moderation", ["coord_pre_binary"], MAIN_THRESHOLD, use_coord_binary=True),
        ModelSpec("ROB_TIMEVAR_COORD", "Time-varying coord", ["coord"], MAIN_THRESHOLD, source_panel="base_tv", timevarying_moderator="coord"),
        ModelSpec("ROB_COMMON_UD", "ud on adjcov-available countries only", ["ud_pre"], RESTRICTED_THRESHOLD, restrict_adjcov_countries=True),
        ModelSpec("ROB_TIMEVAR_UD", "Time-varying ud", ["ud"], MAIN_THRESHOLD, source_panel="base_tv", timevarying_moderator="ud"),
        ModelSpec("ROB_BALANCED", "Balanced sub-panel (entities in every year)", [], MAIN_THRESHOLD, balanced=True),
        ModelSpec("ROB_PRECRISIS", "Pre-crisis period only", [], MAIN_THRESHOLD, year_min=2001, year_max=2007),
        ModelSpec("ROB_POSTCRISIS", "Post-crisis period only", [], MAIN_THRESHOLD, year_min=2008, year_max=2014),
        ModelSpec("ROB_NO_CONTROLS", "Baseline without industry controls", [], MAIN_THRESHOLD, source_panel="no_controls"),
    ]
    for bucket_value, bucket_name in BUCKET_NAMES.items():
        specs.append(
            ModelSpec(
                f"ROB_PER_BUCKET_{bucket_value}",
                f"Separate regression: {bucket_name}",
                ["bucket"],
                MAIN_THRESHOLD,
                bucket_value=bucket_value,
            )
        )
    return specs


def evaluate_model(spec: ModelSpec, panels: dict[str, pd.DataFrame]) -> tuple[dict[str, object], str | None]:
    df = panels[spec.source_panel].copy()

    if spec.use_coord_binary:
        df["coord_pre_binary"] = np.where(df["coord_pre"].notna(), (df["coord_pre"] >= 4).astype(int), np.nan)
    if spec.restrict_adjcov_countries:
        df = df[df["adjcov_pre"].notna()].copy()
    if spec.year_min is not None and spec.year_max is not None:
        df = df[df["year"].between(spec.year_min, spec.year_max)].copy()
    if spec.balanced:
        counts = df.groupby("entity")["year"].nunique()
        full_entities = counts[counts == len(ANALYSIS_YEARS)].index
        df = df[df["entity"].isin(full_entities)].copy()
    if spec.bucket_value is not None:
        df = df[df["bucket"] == spec.bucket_value].copy()

    if spec.required_variables:
        df = df.dropna(subset=spec.required_variables).copy()

    n_buckets = int(df["bucket"].dropna().nunique()) if "bucket" in df.columns else 0
    country_count = int(df["country_code"].nunique())
    reasons: list[str] = []
    if country_count < spec.threshold:
        reasons.append(f"{country_count} countries (<{spec.threshold})")
    if spec.require_all_buckets and n_buckets < len(EXPECTED_BUCKETS):
        reasons.append(f"only {n_buckets}/5 buckets populated")

    result = {
        "model": spec.model,
        "description": spec.description,
        "required_variables": required_variables_label(spec),
        "n_countries": country_count,
        "n_entities": entity_count(df),
        "n_observations": int(len(df)),
        "countries_list": ", ".join(sorted(df["country_code"].dropna().unique().tolist())),
        "pass_threshold": "PASS" if not reasons else "FAIL",
    }
    return result, "; ".join(reasons) if reasons else None


def build_sample_attrition_table(panels: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, dict[str, str]]:
    rows: list[dict[str, object]] = []
    reasons: dict[str, str] = {}
    for spec in model_specs():
        row, reason = evaluate_model(spec, panels)
        rows.append(row)
        if reason:
            reasons[spec.model] = reason
    table = pd.DataFrame(rows)
    table.to_csv(OUTPUT_DIR / "sample_attrition_table.csv", index=False)
    return table, reasons


def required_variables_label(spec: ModelSpec) -> str:
    parts = list(spec.required_variables)
    if spec.restrict_adjcov_countries:
        parts.append("restrict(adjcov_pre available)")
    if spec.use_coord_binary:
        parts.append("coord_pre >= 4")
    if spec.timevarying_moderator is not None:
        parts.append(f"time-varying {spec.timevarying_moderator}")
    if spec.balanced:
        parts.append("balanced entities (14 years)")
    if spec.year_min is not None and spec.year_max is not None:
        parts.append(f"years {spec.year_min}-{spec.year_max}")
    if spec.require_all_buckets:
        parts.append("all 5 buckets populated")
    if spec.bucket_value is not None:
        parts.append(f"bucket={spec.bucket_value}")
    if spec.source_panel == "no_controls":
        parts.append("no ln_va_sea / ln_cap_sea requirement")
    return ", ".join(parts) if parts else "(none beyond base)"


def build_bucket_coverage_detail(base_panel: pd.DataFrame, reference_countries: list[str]) -> pd.DataFrame:
    both_panel = base_panel[base_panel["ud_pre"].notna() & base_panel["coord_pre"].notna()].copy()
    rows: list[dict[str, object]] = []
    reference_set = set(reference_countries)

    for bucket_value in sorted(BUCKET_NAMES):
        sub = both_panel[both_panel["bucket"] == bucket_value].copy()
        present = sorted(sub["country_code"].dropna().unique().tolist())
        missing = sorted(reference_set - set(present))
        rows.append(
            {
                "bucket": bucket_value,
                "bucket_name": BUCKET_NAMES[bucket_value],
                "n_countries": len(present),
                "countries_present": ", ".join(present),
                "countries_missing": ", ".join(missing),
                "n_entities": entity_count(sub),
                "n_observations": int(len(sub)),
                "pass_threshold": "PASS" if len(present) >= MAIN_THRESHOLD else "FAIL",
            }
        )

    detail = pd.DataFrame(rows)
    detail.to_csv(OUTPUT_DIR / "bucket_coverage_detail.csv", index=False)
    return detail


def build_unemployment_feasibility(base_panel: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    country_year_support = base_panel[["country_code", "year"]].drop_duplicates().sort_values(["country_code", "year"])
    support = country_year_support.merge(load_unemployment(), on=["country_code", "year"], how="left")
    support["missing"] = support["unemployment"].isna()

    rows: list[dict[str, object]] = []
    for country, sub in support.groupby("country_code"):
        missing_years = sub.loc[sub["missing"], "year"].astype(int).tolist()
        rows.append(
            {
                "country_code": country,
                "n_panel_years": int(len(sub)),
                "n_missing_years": int(len(missing_years)),
                "missing_years": ", ".join(str(year) for year in missing_years),
                "country_missingness_rate": round(len(missing_years) / len(sub), 4) if len(sub) else np.nan,
                "all_years_available": len(missing_years) == 0,
            }
        )

    total_missing = int(support["missing"].sum())
    total_rows = int(len(support))
    missingness_rate = total_missing / total_rows if total_rows else np.nan
    rows.append(
        {
            "country_code": "__OVERALL__",
            "n_panel_years": total_rows,
            "n_missing_years": total_missing,
            "missing_years": ", ".join(
                f"{row.country_code}:{int(row.year)}" for row in support.loc[support["missing"], ["country_code", "year"]].itertuples(index=False)
            ),
            "country_missingness_rate": round(missingness_rate, 4) if not np.isnan(missingness_rate) else np.nan,
            "all_years_available": missingness_rate <= 0.10 if not np.isnan(missingness_rate) else False,
        }
    )

    detail = pd.DataFrame(rows)
    detail.to_csv(OUTPUT_DIR / "unemployment_feasibility.csv", index=False)
    meta = {
        "total_country_years": total_rows,
        "missing_country_years": total_missing,
        "missingness_rate": missingness_rate,
        "viable_under_10pct": bool(missingness_rate <= 0.10) if not np.isnan(missingness_rate) else False,
        "missing_countries": sorted(support.loc[support["missing"], "country_code"].unique().tolist()),
    }
    return detail, meta


def build_klems_legacy_feasibility(no_controls_panel: pd.DataFrame) -> pd.DataFrame:
    klems = load_klems_controls()
    legacy = no_controls_panel.merge(
        klems[["country_code", "nace_r2_code", "year", "ln_va_klems", "ln_cap_klems"]],
        on=["country_code", "nace_r2_code", "year"],
        how="left",
    )
    eq1 = legacy.dropna(subset=["ln_va_klems", "ln_cap_klems"]).copy()
    eq2_ud = eq1.dropna(subset=["ud_pre"]).copy()

    rows = [
        {
            "model": "EQ1_KLEMS",
            "description": "WIOD exports + KLEMS ln_va and ln_cap",
            "n_countries": int(eq1["country_code"].nunique()),
            "n_entities": entity_count(eq1),
            "n_observations": int(len(eq1)),
            "countries_list": ", ".join(sorted(eq1["country_code"].dropna().unique().tolist())),
        },
        {
            "model": "EQ2_UD_KLEMS",
            "description": "WIOD exports + KLEMS ln_va and ln_cap + ud_pre",
            "n_countries": int(eq2_ud["country_code"].nunique()),
            "n_entities": entity_count(eq2_ud),
            "n_observations": int(len(eq2_ud)),
            "countries_list": ", ".join(sorted(eq2_ud["country_code"].dropna().unique().tolist())),
        },
    ]
    output = pd.DataFrame(rows)
    output.to_csv(OUTPUT_DIR / "klems_legacy_feasibility.csv", index=False)
    return output


def build_summary_text(
    sea_meta: dict[str, object],
    base_panel: pd.DataFrame,
    attrition: pd.DataFrame,
    attrition_reasons: dict[str, str],
    bucket_detail: pd.DataFrame,
    unemployment_meta: dict[str, object],
) -> str:
    index = attrition.set_index("model")
    data_source_statuses = {
        "IFR (robots)": "AVAILABLE" if (DATA_DIR / "IFR_karol.csv").exists() else "MISSING",
        "WIOD trade tables (exports)": "AVAILABLE" if any((DATA_DIR / "WIOTS_in_EXCEL").glob("WIOT*_Nov16_ROW.xlsb")) else "MISSING",
        "WIOD SEA (VA, CAP controls)": "AVAILABLE" if SEA_PATH.exists() else "MISSING",
        "ICTWSS (ud, coord, adjcov)": "AVAILABLE" if (DATA_DIR / "ictwss_institutions.csv").exists() else "MISSING",
        "Eurostat GDP": "AVAILABLE" if (DATA_DIR / "eurostata_gdp_nama_10_gdp.csv").exists() else "MISSING",
    }

    main_ids = ["EQ1", "EQ1_GDP", "EQ2_COORD", "EQ3", "EQ4_COORD"]
    restricted_ids = ["EQ2_ADJCOV", "EQ4_ADJCOV"]
    reference_ids = ["EQ2_UD", "EQ4_UD"]
    robustness_ids = [model for model in attrition["model"].tolist() if model not in main_ids + restricted_ids + reference_ids]

    main_failures = [model for model in main_ids if index.loc[model, "pass_threshold"] == "FAIL"]
    restricted_failures = [model for model in restricted_ids if index.loc[model, "pass_threshold"] == "FAIL"]
    reference_failures = [model for model in reference_ids if index.loc[model, "pass_threshold"] == "FAIL"]
    robustness_failures = [model for model in robustness_ids if index.loc[model, "pass_threshold"] == "FAIL"]

    if main_failures or restricted_failures:
        verdict = "NOT REGRESSION-READY"
    elif robustness_failures or not unemployment_meta["viable_under_10pct"]:
        verdict = "CONDITIONALLY READY"
    else:
        verdict = "REGRESSION-READY"

    lines = [
        "============================================================",
        "REGRESSION-READY AUDIT SUMMARY",
        "============================================================",
        "",
        "DATA SOURCES REQUIRED:",
    ]
    for label, status in data_source_statuses.items():
        lines.append(f"  - {label}: {status}")
    lines.extend(
        [
            "",
            f"SEA COVERAGE: {sea_meta['complete_va_cap_countries']} countries have complete VA+CAP for all manufacturing industries across 2000-2014.",
            f"BASE PANEL: {base_panel['country_code'].nunique()} countries, {entity_count(base_panel)} entities, {len(base_panel)} obs, {int(base_panel['year'].min())}-{int(base_panel['year'].max())}",
            "",
            "MAIN MODELS (threshold: >=20 countries):",
        ]
    )
    for model in main_ids:
        row = index.loc[model]
        lines.append(f"  {model:<10} {row['pass_threshold']} — {int(row['n_countries'])} countries, {int(row['n_observations'])} obs")
    lines.extend(
        [
            "",
            "RESTRICTED MODELS (threshold: >=14 countries):",
        ]
    )
    for model in restricted_ids:
        row = index.loc[model]
        lines.append(f"  {model:<10} {row['pass_threshold']} — {int(row['n_countries'])} countries, {int(row['n_observations'])} obs")
    lines.extend(
        [
            "",
            "REFERENCE BENCHMARKS:",
        ]
    )
    for model in reference_ids:
        row = index.loc[model]
        lines.append(f"  {model:<10} {row['pass_threshold']} — {int(row['n_countries'])} countries, {int(row['n_observations'])} obs")
    lines.extend(
        [
            "",
            "ROBUSTNESS CHECKS:",
        ]
    )
    for model in robustness_ids:
        row = index.loc[model]
        lines.append(f"  {model:<15} {row['pass_threshold']} — {int(row['n_countries'])} countries, {int(row['n_observations'])} obs")
    lines.extend(
        [
            "",
            "BUCKET COVERAGE:",
        ]
    )
    for row in bucket_detail.itertuples(index=False):
        lines.append(f"  Bucket {int(row.bucket)} ({row.bucket_name}): {int(row.n_countries)} countries")

    lines.extend(
        [
            "",
            f"OVERALL VERDICT: {verdict}",
        ]
    )

    if verdict == "NOT REGRESSION-READY":
        lines.append("  - Failing main/restricted models:")
        for model in main_failures + restricted_failures:
            lines.append(f"    {model}: {attrition_reasons.get(model, 'threshold not met')}")
    elif verdict == "CONDITIONALLY READY":
        lines.append("  - Main and restricted models pass, but remaining constraints are:")
        for model in reference_failures:
            lines.append(f"    {model}: {attrition_reasons.get(model, 'threshold not met')}")
        for model in robustness_failures:
            lines.append(f"    {model}: {attrition_reasons.get(model, 'threshold not met')}")
        if not unemployment_meta["viable_under_10pct"]:
            rate = (
                unemployment_meta["missingness_rate"] * 100
                if pd.notna(unemployment_meta["missingness_rate"])
                else float("nan")
            )
            lines.append(
                f"    Unemployment control infeasible: {unemployment_meta['missing_country_years']} missing country-years out of {unemployment_meta['total_country_years']} ({rate:.1f}% missing)"
            )
    else:
        lines.append("  - All planned models and robustness checks pass the configured coverage thresholds.")

    lines.append("============================================================")
    return "\n".join(lines)


def main() -> None:
    ensure_output_dir()

    phase1 = load_phase1_support()
    sea_long = load_sea_long()
    coverage, sea_panel, sea_meta = build_sea_outputs(sea_long)
    gdp = load_gdp_growth()
    unemployment = load_unemployment()
    panels = prepare_panels(phase1, sea_panel, gdp, unemployment)

    attrition, attrition_reasons = build_sample_attrition_table(panels)
    reference_countries = sorted(phase1.loc[phase1["both_available"], "country_code"].dropna().unique().tolist())
    bucket_detail = build_bucket_coverage_detail(panels["base"], reference_countries)
    unemployment_detail, unemployment_meta = build_unemployment_feasibility(panels["base"])
    klems_legacy = build_klems_legacy_feasibility(panels["no_controls"])

    summary_text = build_summary_text(
        sea_meta=sea_meta,
        base_panel=panels["base"],
        attrition=attrition,
        attrition_reasons=attrition_reasons,
        bucket_detail=bucket_detail,
        unemployment_meta=unemployment_meta,
    )
    SUMMARY_PATH.write_text(summary_text + "\n", encoding="utf-8")

    print(f"SEA coverage: {sea_meta['complete_va_cap_countries']} countries have complete VA+CAP for all manufacturing industries across 2000-2014.")
    print_table("SEA Coverage Matrix", coverage.head(15))
    print_table("Sample Attrition Table", attrition)
    print_table("Bucket Coverage Detail", bucket_detail)
    print_table("Unemployment Feasibility", unemployment_detail)
    print_table("KLEMS Legacy Feasibility", klems_legacy)
    print()
    print(summary_text)


if __name__ == "__main__":
    main()
