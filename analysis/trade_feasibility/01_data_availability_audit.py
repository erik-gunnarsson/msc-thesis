from __future__ import annotations

from pathlib import Path

import pandas as pd

from _common import (
    OUTPUT_DIR,
    WIOD_TO_NACE_TABLE,
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
                "eu_countries_in_wiod": ", ".join(header_meta["eu_countries_iso2"]),
                "wiod_values_note": "Current-price millions of USD",
            }
        ]
    )
    wiod_summary.to_csv(OUTPUT_DIR / "wiod_availability_summary.csv", index=False)
    print_table("WIOD Availability Summary", wiod_summary)

    trade_panel = build_wiod_trade_panel(cache_path=OUTPUT_DIR / "wiod_trade_panel.csv")
    print_table("WIOD Trade Panel Preview", trade_panel, max_rows=20)


def main() -> None:
    ensure_output_dir()
    audit_ifr()
    audit_ictwss()
    audit_crosswalks_and_wiod()
    print(f"\nSaved outputs to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
