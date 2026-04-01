from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[3]
CODE_DIR = ROOT_DIR / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from _wiod_panel_utils import (
    WIOD_EUROPE_CANDIDATE_ISO2,
    build_wiod_panel,
    get_wiod_controls,
    load_ifr_panel as load_active_ifr_panel,
    load_ictwss,
    load_macro_controls,
    load_wiod_sea_long,
    prepare_wiod_joint_coord_ud_sample,
    prepare_wiod_panel,
)

from _common import (
    IFR_TO_NACE_MAIN,
    OUTPUT_DIR,
    WIOD_TO_NACE_TABLE,
    EUROPE_CANDIDATE_ISO2,
    build_ifr_main_panel,
    build_ifr_raw_compare_panel,
    build_wiod_trade_panel,
    ensure_output_dir,
    list_wiod_files,
    load_ictwss_baseline,
    load_ifr_raw,
    print_table,
    read_wiod_header_metadata,
)


def audit_ifr() -> None:
    ifr_main = build_ifr_main_panel()
    ifr_raw = build_ifr_raw_compare_panel()

    country_year = (
        ifr_main.groupby(["country_code", "year"])["nace_r2_code"]
        .nunique()
        .reset_index(name="n_nace_groups")
        .pivot(index="country_code", columns="year", values="n_nace_groups")
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    country_year.to_csv(OUTPUT_DIR / "ifr_country_year_coverage.csv", index=False)
    print_table("IFR Country x Year Coverage (collapsed NACE)", country_year)

    country_industry = (
        ifr_main.groupby(["country_code", "nace_r2_code"])
        .agg(years_present=("year", "nunique"), first_year=("year", "min"), last_year=("year", "max"))
        .reset_index()
        .sort_values(["country_code", "nace_r2_code"])
    )
    country_industry.to_csv(OUTPUT_DIR / "ifr_country_industry_coverage.csv", index=False)
    print_table("IFR Country x NACE Coverage", country_industry)

    country_codes = (
        load_ifr_raw()[["country_code", "country_name"]]
        .drop_duplicates()
        .sort_values("country_code")
        .reset_index(drop=True)
    )
    country_codes.to_csv(OUTPUT_DIR / "ifr_country_codes.csv", index=False)
    print_table("IFR Country Codes", country_codes)

    raw_compare = (
        ifr_raw.groupby(["country_code", "nace_r2_code"])
        .agg(raw_ifr_codes=("industry_code", "nunique"))
        .reset_index()
        .sort_values(["country_code", "nace_r2_code"])
    )
    raw_compare.to_csv(OUTPUT_DIR / "ifr_raw_compare_multiplicity.csv", index=False)
    print_table("IFR Raw-Code Multiplicity By Country x NACE", raw_compare)


def audit_ictwss() -> None:
    baseline, earliest = load_ictwss_baseline()
    coverage = baseline[
        [
            "country_code",
            "ud_available",
            "coord_available",
            "adjcov_available",
            "ud_pre",
            "coord_pre",
            "adjcov_pre",
        ]
    ].copy()
    merged = coverage.merge(earliest, on="country_code", how="left")
    merged = merged.rename(columns={"country_code": "country_iso2"})
    merged.to_csv(OUTPUT_DIR / "ictwss_country_coverage.csv", index=False)
    print_table("ICTWSS Coverage (1990-1995 baseline + earliest diagnostic)", merged)


def audit_crosswalks_and_wiod() -> None:
    WIOD_TO_NACE_TABLE.to_csv(OUTPUT_DIR / "wiod_to_nace_crosswalk.csv", index=False)
    print_table("WIOD to Thesis NACE Mapping", WIOD_TO_NACE_TABLE)

    from _common import IFR_TO_NACE_MAIN

    ifr_crosswalk = (
        pd.DataFrame(
            [{"ifr_industry_code": code, "nace_r2_code": nace} for code, nace in IFR_TO_NACE_MAIN.items()]
        )
        .sort_values(["nace_r2_code", "ifr_industry_code"])
        .reset_index(drop=True)
    )
    ifr_crosswalk.to_csv(OUTPUT_DIR / "ifr_nace_crosswalk.csv", index=False)
    print_table("IFR to NACE Crosswalk (main audit mappings)", ifr_crosswalk)

    wiod_files = list_wiod_files()
    header_meta = read_wiod_header_metadata(wiod_files[-1])
    wiod_summary = pd.DataFrame(
        [
            {
                "years_present": f"{min(int(path.stem[4:8]) for path in wiod_files)}-{max(int(path.stem[4:8]) for path in wiod_files)}",
                "n_wiod_files": len(wiod_files),
                "candidate_countries_in_wiod": ", ".join(header_meta["candidate_countries_iso2"]),
                "wiod_values_note": "Current-price millions of USD",
            }
        ]
    )
    wiod_summary.to_csv(OUTPUT_DIR / "wiod_availability_summary.csv", index=False)
    print_table("WIOD Availability Summary", wiod_summary)

    trade_panel = build_wiod_trade_panel(cache_path=OUTPUT_DIR / "wiod_trade_panel.csv")
    print_table("WIOD Trade Panel Preview", trade_panel, max_rows=20)


def _bool_flag(series: pd.Series, countries: list[str]) -> pd.Series:
    return pd.Series(countries).isin(set(series.dropna().astype(str))).map({True: "Y", False: "N"})


def _blocker_columns(detail: pd.DataFrame) -> pd.DataFrame:
    blocker_priority = [
        "missing_ifr_extract",
        "missing_wiod_sea",
        "missing_gdp",
        "no_lagged_robot_support",
        "missing_coord_baseline",
        "missing_ud_baseline",
        "missing_adjcov_baseline",
    ]

    def blocker_list(row: pd.Series) -> list[str]:
        blockers: list[str] = []
        if row["has_ifr_raw"] == "N":
            blockers.append("missing_ifr_extract")
        if row["has_wiod_sea"] == "N":
            blockers.append("missing_wiod_sea")
        if row["has_gdp"] == "N":
            blockers.append("missing_gdp")
        if row["has_ifr_raw"] == "Y" and row["has_ifr_lagged"] == "N":
            blockers.append("no_lagged_robot_support")
        if row["has_ictwss_coord"] == "N":
            blockers.append("missing_coord_baseline")
        if row["has_ictwss_ud"] == "N":
            blockers.append("missing_ud_baseline")
        if row["has_ictwss_adjcov"] == "N":
            blockers.append("missing_adjcov_baseline")
        return blockers

    primary: list[str] = []
    secondary: list[str] = []
    for _, row in detail.iterrows():
        blockers = blocker_list(row)
        if row["in_eq2_coord"] == "Y":
            primary.append("regression_ready")
            secondary.append(", ".join(blockers) if blockers else "")
            continue
        chosen = ""
        for label in blocker_priority:
            if label in blockers:
                chosen = label
                break
        primary.append(chosen or "not_regression_ready")
        secondary.append(", ".join([b for b in blockers if b != chosen]))

    detail["primary_blocker"] = primary
    detail["secondary_blockers"] = secondary
    return detail


def audit_europe_country_availability() -> None:
    countries = sorted(WIOD_EUROPE_CANDIDATE_ISO2)

    ifr_raw = load_ifr_raw()
    ifr_raw = ifr_raw[
        ifr_raw["year"].between(2000, 2014)
        & ifr_raw["industry_code"].isin(IFR_TO_NACE_MAIN)
    ].copy()
    ifr_panel = load_active_ifr_panel()

    sea_long = load_wiod_sea_long()
    ictwss_baseline, _ = load_ictwss()
    gdp, _ = load_macro_controls()
    panel = build_wiod_panel()

    controls = get_wiod_controls(capital_proxy="k", include_gdp=True)
    eq1 = prepare_wiod_panel(panel, require=["ln_h_empe", "ln_robots_lag1"] + controls, sample="full")
    eq2_coord = prepare_wiod_panel(
        panel,
        require=["ln_h_empe", "ln_robots_lag1", "coord_pre_c"] + controls,
        sample="full",
    )
    eq2_ud = prepare_wiod_panel(
        panel,
        require=["ln_h_empe", "ln_robots_lag1", "ud_pre_c"] + controls,
        sample="full",
    )
    eq2_adjcov = prepare_wiod_panel(
        panel,
        require=["ln_h_empe", "ln_robots_lag1", "adjcov_pre_c"] + controls,
        sample="common",
    )
    eq2b, _ = prepare_wiod_joint_coord_ud_sample(panel, capital_proxy="k", include_gdp=True)

    detail = pd.DataFrame({"country_code": countries})
    detail["has_wiod_sea"] = _bool_flag(sea_long["country_code"], countries)
    detail["has_ifr_raw"] = _bool_flag(ifr_raw["country_code"], countries)
    lagged_countries = ifr_panel.loc[ifr_panel["ln_robots_lag1"].notna(), "country_code"]
    detail["has_ifr_lagged"] = _bool_flag(lagged_countries, countries)

    detail = detail.merge(
        ictwss_baseline[["country_code", "has_coord", "has_ud", "has_adjcov"]],
        on="country_code",
        how="left",
    )
    detail["has_ictwss_coord"] = detail["has_coord"].fillna(False).map({True: "Y", False: "N"})
    detail["has_ictwss_ud"] = detail["has_ud"].fillna(False).map({True: "Y", False: "N"})
    detail["has_ictwss_adjcov"] = detail["has_adjcov"].fillna(False).map({True: "Y", False: "N"})
    detail = detail.drop(columns=["has_coord", "has_ud", "has_adjcov"])

    gdp_countries = gdp.loc[gdp["gdp_growth"].notna(), "country_code"]
    detail["has_gdp"] = _bool_flag(gdp_countries, countries)
    detail["in_raw_wiod_panel"] = _bool_flag(panel["country_code"], countries)
    detail["in_eq1"] = _bool_flag(eq1["country_code"], countries)
    detail["in_eq2_coord"] = _bool_flag(eq2_coord["country_code"], countries)
    detail["in_eq2_ud"] = _bool_flag(eq2_ud["country_code"], countries)
    detail["in_eq2_adjcov"] = _bool_flag(eq2_adjcov["country_code"], countries)
    detail["in_eq2b"] = _bool_flag(eq2b["country_code"], countries)
    detail = _blocker_columns(detail)

    detail.to_csv(OUTPUT_DIR / "europe_country_availability_matrix.csv", index=False)
    print_table("Europe Candidate Availability Matrix", detail)

    four_way_overlap = sorted(
        set(ifr_raw["country_code"].dropna())
        & set(sea_long["country_code"].dropna())
        & set(ictwss_baseline["country_code"].dropna())
        & set(gdp_countries.dropna())
    )
    summary = pd.DataFrame(
        [
            {
                "candidate_universe_size": len(countries),
                "four_way_raw_overlap": len(four_way_overlap),
                "four_way_raw_overlap_countries": ", ".join(four_way_overlap),
                "eq1_countries": eq1["country_code"].nunique(),
                "eq2_coord_countries": eq2_coord["country_code"].nunique(),
                "eq2_ud_countries": eq2_ud["country_code"].nunique(),
                "eq2_adjcov_countries": eq2_adjcov["country_code"].nunique(),
                "eq2b_countries": eq2b["country_code"].nunique(),
            }
        ]
    )
    summary.to_csv(OUTPUT_DIR / "europe_country_availability_summary.csv", index=False)
    print_table("Europe Candidate Availability Summary", summary)


def main() -> None:
    ensure_output_dir()
    audit_ifr()
    audit_ictwss()
    audit_crosswalks_and_wiod()
    audit_europe_country_availability()
    print(f"\nSaved outputs to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
