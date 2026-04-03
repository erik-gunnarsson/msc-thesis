from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

try:
    from pyxlsb import open_workbook
except ImportError:  # pragma: no cover - handled at runtime
    open_workbook = None


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "results" / "exploration" / "wiod_feasibility"
WIOD_DIR = DATA_DIR / "WIOTS_in_EXCEL"
CURRENT_BASELINE_PATH = DATA_DIR / "cleaned_data.csv"

EUROPE_CANDIDATE_ISO2 = [
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR",
    "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO",
    "SE", "SI", "SK", "UK", "NO", "CH", "TR", "RU", "IC",
]
EUROPE_CANDIDATE_SET = set(EUROPE_CANDIDATE_ISO2)

ISO3_TO_ISO2 = {
    "AUT": "AT",
    "BEL": "BE",
    "BGR": "BG",
    "CHE": "CH",
    "CYP": "CY",
    "CZE": "CZ",
    "DEU": "DE",
    "DNK": "DK",
    "ESP": "ES",
    "EST": "EE",
    "FIN": "FI",
    "FRA": "FR",
    "GBR": "UK",
    "GRC": "EL",
    "HRV": "HR",
    "HUN": "HU",
    "ISL": "IC",
    "IRL": "IE",
    "ITA": "IT",
    "LTU": "LT",
    "LUX": "LU",
    "LVA": "LV",
    "MLT": "MT",
    "NLD": "NL",
    "NOR": "NO",
    "POL": "PL",
    "PRT": "PT",
    "ROU": "RO",
    "RUS": "RU",
    "SVK": "SK",
    "SVN": "SI",
    "SWE": "SE",
    "TUR": "TR",
}
ISO2_TO_ISO3 = {v: k for k, v in ISO3_TO_ISO2.items() if v in EUROPE_CANDIDATE_SET}
EUROPE_CANDIDATE_ISO3 = {ISO2_TO_ISO3[c] for c in EUROPE_CANDIDATE_ISO2 if c in ISO2_TO_ISO3}

IFR_TO_NACE_ALL = {
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
IFR_TO_NACE_MAIN = {
    key: value
    for key, value in IFR_TO_NACE_ALL.items()
    if value not in {"C", "C21"}
}

WIOD_TO_NACE = {
    "C10-C12": "C10-C12",
    "C13-C15": "C13-C15",
    "C16": "C16-C18",
    "C17": "C16-C18",
    "C18": "C16-C18",
    "C19": "C19",
    "C20": "C20-C21",
    "C21": "C20-C21",
    "C22": "C22-C23",
    "C23": "C22-C23",
    "C24": "C24-C25",
    "C25": "C24-C25",
    "C26": "C26-C27",
    "C27": "C26-C27",
    "C28": "C28",
    "C29": "C29-C30",
    "C30": "C29-C30",
    "C29_C30": "C29-C30",
    "C31_C32": "C31-C33",
    "C33": "C31-C33",
}

WIOD_TO_NACE_TABLE = pd.DataFrame(
    [
        {"wiod_code": code, "nace_r2_code": nace}
        for code, nace in WIOD_TO_NACE.items()
    ]
).sort_values(["nace_r2_code", "wiod_code"])

ICTWSS_COLS = ["UD", "Coord", "AdjCov"]


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def print_table(title: str, df: pd.DataFrame, *, max_rows: int | None = None) -> None:
    print(f"\n=== {title} ===")
    if df.empty:
        print("(empty)")
        return
    view = df if max_rows is None else df.head(max_rows)
    with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.width", 220):
        print(view.to_string(index=False))
    if max_rows is not None and len(df) > max_rows:
        print(f"... {len(df) - max_rows} more rows")


def year_range_label(df: pd.DataFrame, year_col: str = "year") -> str:
    if df.empty:
        return "—"
    years = pd.to_numeric(df[year_col], errors="coerce").dropna()
    if years.empty:
        return "—"
    return f"{int(years.min())}-{int(years.max())}"


def scenario_metrics(
    df: pd.DataFrame,
    *,
    entity_cols: list[str],
    scenario: str,
    view: str,
    universe: list[str] | None = None,
) -> dict[str, object]:
    countries = sorted(df["country_code"].dropna().unique().tolist())
    dropped = []
    if universe is not None:
        dropped = sorted(set(universe) - set(countries))
    entities = (
        df[entity_cols]
        .drop_duplicates()
        .shape[0]
        if all(col in df.columns for col in entity_cols)
        else 0
    )
    return {
        "scenario": scenario,
        "view": view,
        "countries": len(countries),
        "entities": entities,
        "observations": len(df),
        "years": year_range_label(df),
        "dropped_countries": ", ".join(dropped) if dropped else "",
    }


def load_ifr_raw() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "IFR_karol.csv")
    df["country_code"] = df["country_code"].replace({"GR": "EL"})
    df["industry_code"] = df["industry_code"].astype(str)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["robot_wrkr_stock_95"] = pd.to_numeric(df["robot_wrkr_stock_95"], errors="coerce")
    return df


def build_ifr_main_panel(year_start: int = 2000, year_end: int = 2014) -> pd.DataFrame:
    df = load_ifr_raw()
    df = df[
        df["country_code"].isin(EUROPE_CANDIDATE_SET)
        & df["industry_code"].isin(IFR_TO_NACE_MAIN)
        & df["year"].between(year_start, year_end)
    ].copy()
    df["nace_r2_code"] = df["industry_code"].map(IFR_TO_NACE_MAIN)
    df = df.dropna(subset=["robot_wrkr_stock_95", "nace_r2_code"])
    collapsed = (
        df.groupby(["country_code", "nace_r2_code", "year"], as_index=False)
        .agg(
            robot_wrkr_stock_95=("robot_wrkr_stock_95", "mean"),
            n_ifr_rows=("industry_code", "size"),
        )
    )
    collapsed["trade_available"] = True
    return collapsed.sort_values(["country_code", "nace_r2_code", "year"]).reset_index(drop=True)


def build_ifr_raw_compare_panel(year_start: int = 2000, year_end: int = 2014) -> pd.DataFrame:
    df = load_ifr_raw()
    df = df[
        df["country_code"].isin(EUROPE_CANDIDATE_SET)
        & df["industry_code"].isin(IFR_TO_NACE_MAIN)
        & df["year"].between(year_start, year_end)
    ].copy()
    df["nace_r2_code"] = df["industry_code"].map(IFR_TO_NACE_MAIN)
    df = df.dropna(subset=["robot_wrkr_stock_95", "nace_r2_code"])
    df["trade_available"] = True
    return df.sort_values(["country_code", "industry_code", "year"]).reset_index(drop=True)


def load_ictwss_baseline() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(DATA_DIR / "ictwss_institutions.csv")
    df["country_code"] = df["iso3"].map(ISO3_TO_ISO2)
    df = df[df["country_code"].isin(EUROPE_CANDIDATE_SET)].copy()
    for col in ICTWSS_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] == -99, col] = pd.NA

    baseline_window = df[df["year"].between(1990, 1995)].copy()
    baseline = (
        baseline_window.groupby("country_code", as_index=False)
        .agg(
            ud_pre=("UD", _safe_mean),
            coord_pre=("Coord", _safe_mean),
            adjcov_pre=("AdjCov", _safe_mean),
        )
        .sort_values("country_code")
        .reset_index(drop=True)
    )
    baseline["ud_available"] = baseline["ud_pre"].notna()
    baseline["coord_available"] = baseline["coord_pre"].notna()
    baseline["adjcov_available"] = baseline["adjcov_pre"].notna()

    earliest_rows: list[dict[str, object]] = []
    for country in sorted(df["country_code"].dropna().unique()):
        row: dict[str, object] = {"country_code": country}
        sub = df[df["country_code"] == country].sort_values("year")
        for src, dst in [("UD", "ud_earliest"), ("Coord", "coord_earliest"), ("AdjCov", "adjcov_earliest")]:
            non_missing = sub[sub[src].notna()]
            row[dst] = non_missing.iloc[0][src] if not non_missing.empty else pd.NA
        earliest_rows.append(row)
    earliest = pd.DataFrame(earliest_rows)
    return baseline, earliest


def _safe_mean(series: pd.Series) -> float | pd.NA:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return pd.NA
    return float(numeric.mean())


def _to_float(value: object) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return 0.0
        return float(value)
    return 0.0


def _require_pyxlsb() -> None:
    if open_workbook is None:
        raise RuntimeError(
            "pyxlsb is required to parse WIOD .xlsb files. Install it with `pip install pyxlsb`."
        )


def _wiod_year_from_path(path: Path) -> int:
    stem = path.stem
    digits = "".join(ch for ch in stem if ch.isdigit())
    return int(digits[:4])


def list_wiod_files() -> list[Path]:
    return sorted(WIOD_DIR.glob("WIOT*_Nov16_ROW.xlsb"))


def read_wiod_header_metadata(path: Path) -> dict[str, object]:
    _require_pyxlsb()
    with open_workbook(path) as wb:
        sheet_name = wb.sheets[0]
        with wb.get_sheet(sheet_name) as sh:
            header_rows: dict[int, list[object]] = {}
            for idx, row in enumerate(sh.rows()):
                if idx in {2, 3, 4, 5}:
                    header_rows[idx] = [cell.v for cell in row]
                if idx > 5:
                    break
    row2 = header_rows[2]
    row4 = header_rows[4]
    total_output_idx = next(
        idx
        for idx, value in enumerate(row2)
        if value == "GO" or row4[idx] == "TOT"
    )
    countries = [c for c in row4[4:total_output_idx] if isinstance(c, str)]
    return {
        "sheet_name": sheet_name,
        "total_output_idx": total_output_idx,
        "countries": sorted(set(countries)),
        "candidate_countries_iso2": sorted(
            {
                ISO3_TO_ISO2[c]
                for c in countries
                if c in ISO3_TO_ISO2 and ISO3_TO_ISO2[c] in EUROPE_CANDIDATE_SET
            }
        ),
    }


def build_wiod_trade_panel(cache_path: Path | None = None) -> pd.DataFrame:
    if cache_path is not None and cache_path.exists():
        cached = pd.read_csv(cache_path)
        expected_groups = set(WIOD_TO_NACE_TABLE["nace_r2_code"].unique())
        cached_groups = set(cached["nace_r2_code"].dropna().unique()) if "nace_r2_code" in cached.columns else set()
        header_meta = read_wiod_header_metadata(list_wiod_files()[-1])
        expected_countries = set(header_meta["candidate_countries_iso2"])
        cached_countries = set(cached["country_code"].dropna().unique()) if "country_code" in cached.columns else set()
        if expected_groups.issubset(cached_groups) and expected_countries.issubset(cached_countries):
            return cached

    _require_pyxlsb()
    records: list[dict[str, object]] = []

    for path in list_wiod_files():
        year = _wiod_year_from_path(path)
        with open_workbook(path) as wb:
            sheet_name = wb.sheets[0]
            with wb.get_sheet(sheet_name) as sh:
                row2: list[object] | None = None
                row4: list[object] | None = None
                total_output_idx: int | None = None
                domestic_columns: dict[str, list[int]] | None = None

                for idx, row in enumerate(sh.rows()):
                    if idx == 2:
                        row2 = [cell.v for cell in row]
                        continue
                    if idx == 4:
                        row4 = [cell.v for cell in row]
                        continue
                    if idx == 5:
                        if row2 is None or row4 is None:
                            raise RuntimeError(f"Unexpected WIOD header order in {path.name}")
                        total_output_idx = next(
                            col_idx
                            for col_idx, value in enumerate(row2)
                            if value == "GO" or row4[col_idx] == "TOT"
                        )
                        domestic_columns = {
                            origin_iso3: [
                                col_idx
                                for col_idx in range(4, total_output_idx)
                                if row4[col_idx] == origin_iso3
                            ]
                            for origin_iso3 in EUROPE_CANDIDATE_ISO3
                        }
                        continue
                    if idx < 6:
                        continue

                    if total_output_idx is None or row4 is None or domestic_columns is None:
                        raise RuntimeError(f"Missing header boundary in {path.name}")

                    sector_code = row[0].v if len(row) > 0 else None
                    origin_iso3 = row[2].v if len(row) > 2 else None
                    row_code = row[3].v if len(row) > 3 else None

                    if not isinstance(row_code, str) or not row_code.startswith("r"):
                        continue
                    if origin_iso3 not in EUROPE_CANDIDATE_ISO3:
                        continue
                    nace_r2_code = WIOD_TO_NACE.get(sector_code)
                    if nace_r2_code is None:
                        continue

                    total_output = _to_float(row[total_output_idx].v if total_output_idx < len(row) else None)
                    domestic_use = 0.0
                    for col_idx in domestic_columns[origin_iso3]:
                        domestic_use += _to_float(row[col_idx].v if col_idx < len(row) else None)
                    gross_exports = max(total_output - domestic_use, 0.0)

                    records.append(
                        {
                            "country_code": ISO3_TO_ISO2[origin_iso3],
                            "nace_r2_code": nace_r2_code,
                            "year": year,
                            "gross_exports_usd_m": gross_exports,
                            "trade_available": gross_exports > 0,
                        }
                    )

    df = (
        pd.DataFrame(records)
        .groupby(["country_code", "nace_r2_code", "year"], as_index=False)
        .agg(
            gross_exports_usd_m=("gross_exports_usd_m", "sum"),
            trade_available=("trade_available", "max"),
        )
        .sort_values(["country_code", "nace_r2_code", "year"])
        .reset_index(drop=True)
    )
    if cache_path is not None:
        df.to_csv(cache_path, index=False)
    return df


def load_current_baseline() -> pd.DataFrame:
    df = pd.read_csv(CURRENT_BASELINE_PATH)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    return df


def current_baseline_country_nace_entities() -> pd.DataFrame:
    df = load_current_baseline()
    entities = df[["country_code", "nace_r2_code"]].drop_duplicates()
    entities["present_in_current_baseline"] = True
    return entities
