from __future__ import annotations

import pandas as pd

from _common import (
    CURRENT_BASELINE_PATH,
    EUROPE_CANDIDATE_ISO2,
    OUTPUT_DIR,
    build_ifr_main_panel,
    build_ifr_raw_compare_panel,
    build_wiod_trade_panel,
    ensure_output_dir,
    load_current_baseline,
    load_ictwss_baseline,
    print_table,
    scenario_metrics,
)


def merge_main() -> tuple[pd.DataFrame, pd.DataFrame]:
    ifr_main = build_ifr_main_panel()
    wiod = build_wiod_trade_panel(cache_path=OUTPUT_DIR / "wiod_trade_panel.csv")
    baseline, _ = load_ictwss_baseline()

    scenario_a = ifr_main.merge(
        wiod,
        on=["country_code", "nace_r2_code", "year"],
        how="inner",
        suffixes=("_ifr", "_wiod"),
    )
    scenario_a["entity"] = scenario_a["country_code"] + "_" + scenario_a["nace_r2_code"]
    scenario_a.to_csv(OUTPUT_DIR / "merge_scenario_A_ifr_trade.csv", index=False)

    scenario_b = scenario_a.merge(
        baseline[["country_code", "ud_pre", "coord_pre", "adjcov_pre", "ud_available", "coord_available", "adjcov_available"]],
        on="country_code",
        how="left",
    )
    scenario_b["both_available"] = scenario_b["ud_available"] & scenario_b["coord_available"]
    scenario_b.to_csv(OUTPUT_DIR / "merge_scenario_B_ifr_trade_ictwss.csv", index=False)

    scenario_c = scenario_b[scenario_b["adjcov_available"]].copy()
    scenario_c.to_csv(OUTPUT_DIR / "merge_scenario_C_restricted.csv", index=False)
    return scenario_a, scenario_b


def merge_raw_compare() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ifr_raw = build_ifr_raw_compare_panel()
    wiod = build_wiod_trade_panel(cache_path=OUTPUT_DIR / "wiod_trade_panel.csv")
    baseline, _ = load_ictwss_baseline()

    scenario_a_raw = ifr_raw.merge(
        wiod,
        on=["country_code", "nace_r2_code", "year"],
        how="inner",
        suffixes=("_ifr", "_wiod"),
    )
    scenario_a_raw["entity"] = scenario_a_raw["country_code"] + "_" + scenario_a_raw["industry_code"]
    scenario_a_raw.to_csv(OUTPUT_DIR / "merge_scenario_A_ifr_trade_raw_compare.csv", index=False)

    scenario_b_raw = scenario_a_raw.merge(
        baseline[["country_code", "ud_pre", "coord_pre", "adjcov_pre", "ud_available", "coord_available", "adjcov_available"]],
        on="country_code",
        how="left",
    )
    scenario_b_raw["both_available"] = scenario_b_raw["ud_available"] & scenario_b_raw["coord_available"]
    scenario_b_raw.to_csv(OUTPUT_DIR / "merge_scenario_B_ifr_trade_ictwss_raw_compare.csv", index=False)

    scenario_c_raw = scenario_b_raw[scenario_b_raw["adjcov_available"]].copy()
    scenario_c_raw.to_csv(OUTPUT_DIR / "merge_scenario_C_restricted_raw_compare.csv", index=False)
    return scenario_a_raw, scenario_b_raw, scenario_c_raw


def current_baseline() -> pd.DataFrame:
    baseline_df = load_current_baseline().copy()
    baseline_df.to_csv(OUTPUT_DIR / "merge_scenario_D_current_baseline.csv", index=False)
    return baseline_df


def build_summary(
    scenario_a: pd.DataFrame,
    scenario_b: pd.DataFrame,
    scenario_c: pd.DataFrame,
    scenario_d: pd.DataFrame,
    scenario_a_raw: pd.DataFrame,
    scenario_b_raw: pd.DataFrame,
    scenario_c_raw: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows = [
        scenario_metrics(scenario_a, entity_cols=["country_code", "nace_r2_code"], scenario="A_ifr_wiod", view="collapsed", universe=EUROPE_CANDIDATE_ISO2),
        scenario_metrics(scenario_b[scenario_b["ud_available"]], entity_cols=["country_code", "nace_r2_code"], scenario="B_ud", view="collapsed", universe=EUROPE_CANDIDATE_ISO2),
        scenario_metrics(scenario_b[scenario_b["coord_available"]], entity_cols=["country_code", "nace_r2_code"], scenario="B_coord", view="collapsed", universe=EUROPE_CANDIDATE_ISO2),
        scenario_metrics(scenario_b[scenario_b["both_available"]], entity_cols=["country_code", "nace_r2_code"], scenario="B_both", view="collapsed", universe=EUROPE_CANDIDATE_ISO2),
        scenario_metrics(scenario_c, entity_cols=["country_code", "nace_r2_code"], scenario="C_adjcov", view="collapsed", universe=EUROPE_CANDIDATE_ISO2),
        scenario_metrics(scenario_d, entity_cols=["country_code", "entity"], scenario="D_current_baseline", view="current_pipeline"),
    ]
    raw_rows = [
        scenario_metrics(scenario_a_raw, entity_cols=["country_code", "industry_code"], scenario="A_ifr_wiod", view="raw_ifr_compare", universe=EUROPE_CANDIDATE_ISO2),
        scenario_metrics(scenario_b_raw[scenario_b_raw["ud_available"]], entity_cols=["country_code", "industry_code"], scenario="B_ud", view="raw_ifr_compare", universe=EUROPE_CANDIDATE_ISO2),
        scenario_metrics(scenario_b_raw[scenario_b_raw["coord_available"]], entity_cols=["country_code", "industry_code"], scenario="B_coord", view="raw_ifr_compare", universe=EUROPE_CANDIDATE_ISO2),
        scenario_metrics(scenario_b_raw[scenario_b_raw["both_available"]], entity_cols=["country_code", "industry_code"], scenario="B_both", view="raw_ifr_compare", universe=EUROPE_CANDIDATE_ISO2),
        scenario_metrics(scenario_c_raw, entity_cols=["country_code", "industry_code"], scenario="C_adjcov", view="raw_ifr_compare", universe=EUROPE_CANDIDATE_ISO2),
    ]
    summary = pd.DataFrame(summary_rows)
    raw_summary = pd.DataFrame(raw_rows)
    summary.to_csv(OUTPUT_DIR / "merge_feasibility_summary.csv", index=False)
    raw_summary.to_csv(OUTPUT_DIR / "merge_feasibility_raw_compare_summary.csv", index=False)
    return summary, raw_summary


def main() -> None:
    ensure_output_dir()

    scenario_a, scenario_b = merge_main()
    scenario_c = pd.read_csv(OUTPUT_DIR / "merge_scenario_C_restricted.csv")
    scenario_a_raw, scenario_b_raw, scenario_c_raw = merge_raw_compare()
    scenario_d = current_baseline()

    summary, raw_summary = build_summary(
        scenario_a,
        scenario_b,
        scenario_c,
        scenario_d,
        scenario_a_raw,
        scenario_b_raw,
        scenario_c_raw,
    )

    print_table("Scenario Summary", summary)
    print_table("Scenario Raw IFR Comparison", raw_summary)
    print(f"\nCurrent baseline source: {CURRENT_BASELINE_PATH}")
    print(f"Saved outputs to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
