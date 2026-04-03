from __future__ import annotations

import pandas as pd

from _common import (
    EUROPE_CANDIDATE_ISO2,
    OUTPUT_DIR,
    build_ifr_main_panel,
    current_baseline_country_nace_entities,
    ensure_output_dir,
    load_ictwss_baseline,
    print_table,
)


def build_main_summary(summary: pd.DataFrame) -> pd.DataFrame:
    def pick(scenario: str, view: str = "collapsed") -> pd.Series:
        return summary[(summary["scenario"] == scenario) & (summary["view"] == view)].iloc[0]

    a = pick("A_ifr_wiod")
    b_both = pick("B_both")
    c = pick("C_adjcov")
    d = pick("D_current_baseline", view="current_pipeline")

    table = pd.DataFrame(
        [
            {
                "Scenario": "A: IFR x WIOD (max)",
                "Countries": a["countries"],
                "Entities": a["entities"],
                "Obs": a["observations"],
                "Years": a["years"],
                "coord": "—",
                "adjcov": "—",
                "ud": "—",
            },
            {
                "Scenario": "B: IFR x WIOD x ICTWSS (coord+ud)",
                "Countries": b_both["countries"],
                "Entities": b_both["entities"],
                "Obs": b_both["observations"],
                "Years": b_both["years"],
                "coord": "Y",
                "adjcov": "—",
                "ud": "Y",
            },
            {
                "Scenario": "C: IFR x WIOD x ICTWSS (adjcov)",
                "Countries": c["countries"],
                "Entities": c["entities"],
                "Obs": c["observations"],
                "Years": c["years"],
                "coord": "Y",
                "adjcov": "Y",
                "ud": "Y",
            },
            {
                "Scenario": "D: Current (IFR x KLEMS x ICTWSS)",
                "Countries": d["countries"],
                "Entities": d["entities"],
                "Obs": d["observations"],
                "Years": d["years"],
                "coord": "Y",
                "adjcov": "Y",
                "ud": "Y",
            },
        ]
    )
    return table


def build_raw_compare_summary(raw_summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scenario in ["A_ifr_wiod", "B_both", "C_adjcov"]:
        sub = raw_summary[raw_summary["scenario"] == scenario].iloc[0]
        rows.append(
            {
                "Scenario": scenario,
                "Countries": sub["countries"],
                "Entities": sub["entities"],
                "Obs": sub["observations"],
                "Years": sub["years"],
            }
        )
    return pd.DataFrame(rows)


def build_country_detail() -> pd.DataFrame:
    ifr_main = build_ifr_main_panel()
    baseline, _ = load_ictwss_baseline()
    current_entities = current_baseline_country_nace_entities()
    scenario_a = pd.read_csv(OUTPUT_DIR / "merge_scenario_A_ifr_trade.csv")

    ifr_country_detail = (
        ifr_main.groupby("country_code")
        .agg(
            ifr_nace_groups=("nace_r2_code", "nunique"),
            ifr_years=("year", "nunique"),
        )
        .reset_index()
    )
    scenario_a_countries = (
        scenario_a[["country_code"]]
        .drop_duplicates()
        .assign(trade_pivot_survives="Y")
    )
    current_countries = (
        current_entities[["country_code"]]
        .drop_duplicates()
        .assign(in_current_klems_sample="Y")
    )

    detail = pd.DataFrame({"country_code": EUROPE_CANDIDATE_ISO2})
    detail = detail.merge(ifr_country_detail, on="country_code", how="left")
    detail = detail.merge(
        baseline[["country_code", "ud_available", "coord_available", "adjcov_available"]],
        on="country_code",
        how="left",
    )
    detail = detail.merge(current_countries, on="country_code", how="left")
    detail = detail.merge(scenario_a_countries, on="country_code", how="left")

    detail["present_in_ifr"] = detail["ifr_nace_groups"].fillna(0).gt(0).map({True: "Y", False: "N"})
    detail["ifr_nace_groups"] = detail["ifr_nace_groups"].fillna(0).astype(int)
    detail["ud_available"] = detail["ud_available"].fillna(False).map({True: "Y", False: "N"})
    detail["coord_available"] = detail["coord_available"].fillna(False).map({True: "Y", False: "N"})
    detail["adjcov_available"] = detail["adjcov_available"].fillna(False).map({True: "Y", False: "N"})
    detail["in_current_klems_sample"] = detail["in_current_klems_sample"].fillna("N")
    detail["trade_pivot_survives"] = detail["trade_pivot_survives"].fillna("N")
    detail["greece_current_code_gap"] = detail["country_code"].eq("EL").map({True: "Dropped in current pipeline (GR/EL mismatch)", False: ""})

    return detail[
        [
            "country_code",
            "present_in_ifr",
            "ifr_nace_groups",
            "coord_available",
            "adjcov_available",
            "ud_available",
            "in_current_klems_sample",
            "trade_pivot_survives",
            "greece_current_code_gap",
        ]
    ]


def main() -> None:
    ensure_output_dir()
    summary = pd.read_csv(OUTPUT_DIR / "merge_feasibility_summary.csv")
    raw_summary = pd.read_csv(OUTPUT_DIR / "merge_feasibility_raw_compare_summary.csv")

    comparison = build_main_summary(summary)
    comparison.to_csv(OUTPUT_DIR / "sample_size_comparison.csv", index=False)
    print_table("Sample Size Comparison", comparison)

    raw_compare = build_raw_compare_summary(raw_summary)
    raw_compare.to_csv(OUTPUT_DIR / "sample_size_comparison_raw_compare.csv", index=False)
    print_table("Raw IFR Comparison Appendix", raw_compare)

    country_detail = build_country_detail()
    country_detail.to_csv(OUTPUT_DIR / "country_detail_matrix.csv", index=False)
    print_table("Country Detail Matrix", country_detail)

    print(f"\nSaved outputs to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
