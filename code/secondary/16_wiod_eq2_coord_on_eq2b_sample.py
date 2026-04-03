'''
Diagnostic re-estimation of WIOD Eq. 2 coordination moderation on the exact
Eq. 2b sample.

Purpose:
  - isolate the sample effect from moving from the full coord model to
    the coord x ud intersection sample
  - compare that sample effect to the additional attenuation that happens when
    ud and the three-way term are added in Eq. 2b

This is a diagnostic decomposition check, not a new headline equation.
'''

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd
from loguru import logger

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from _paths import RESULTS_CORE_DIR, RESULTS_SECONDARY_DIR
from _wiod_model_utils import load_or_build_wiod_panel, write_model_bundle
from _wiod_panel_utils import fit_all_inference, prepare_wiod_joint_coord_ud_sample


COMPARISON_CSV_PATH = RESULTS_SECONDARY_DIR / "wiod_eq2_coord_sample_decomposition.csv"
COMPARISON_MD_PATH = RESULTS_SECONDARY_DIR / "wiod_eq2_coord_sample_decomposition.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--capital-proxy",
        choices=["k", "capcomp"],
        default="k",
        help="WIOD capital control; K stays the default for this diagnostic.",
    )
    parser.add_argument(
        "--no-gdp",
        action="store_true",
        help="Omit GDP growth from the control set.",
    )
    parser.add_argument(
        "--bootstrap-reps",
        type=int,
        default=999,
        help="Wild cluster bootstrap repetitions for the diagnostic coord term.",
    )
    parser.add_argument(
        "--no-bootstrap-progress",
        action="store_true",
        help="Disable tqdm progress bars during wild cluster bootstrap.",
    )
    return parser.parse_args()


def check_sample_integrity(sample: pd.DataFrame) -> None:
    if sample.empty:
        raise RuntimeError("Exact Eq. 2b sample integrity check failed: sample is empty.")
    if sample.duplicated(subset=["entity", "year_int"]).any():
        raise RuntimeError("Exact Eq. 2b sample integrity check failed: duplicate entity-year rows detected.")
    years = f"{int(sample['year_int'].min())}-{int(sample['year_int'].max())}"
    if years != "2001-2014":
        raise RuntimeError(
            "Exact Eq. 2b sample integrity check failed: "
            f"expected 2001-2014 support after lagging, got {years}."
        )


def load_reference_rows() -> tuple[pd.Series, pd.Series]:
    summary_path = RESULTS_CORE_DIR / "wiod_first_results_summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError(
            "This diagnostic requires results/core/wiod_first_results_summary.csv. "
            "Run code/core/14_wiod_first_results.py first."
        )
    summary = pd.read_csv(summary_path)
    eq2_coord = summary.loc[summary["model_id"] == "EQ2_COORD"]
    eq2_ud = summary.loc[summary["model_id"] == "EQ2_UD"]
    if eq2_coord.empty or eq2_ud.empty:
        raise RuntimeError(
            "This diagnostic requires EQ2_COORD and EQ2_UD rows in "
            "results/core/wiod_first_results_summary.csv."
        )
    return eq2_coord.iloc[0], eq2_ud.iloc[0]


def check_against_ud_support(sample: pd.DataFrame, eq2_ud_row: pd.Series) -> None:
    support = {
        "n_countries": int(sample["country_code"].nunique()),
        "n_entities": int(sample["entity"].nunique()),
        "n_observations": int(len(sample)),
    }
    benchmark = {
        "n_countries": int(eq2_ud_row["n_countries"]),
        "n_entities": int(eq2_ud_row["n_entities"]),
        "n_observations": int(eq2_ud_row["n_observations"]),
    }
    if support != benchmark:
        raise RuntimeError(
            "Eq. 2 coord-on-intersection sample does not match the current "
            f"Eq. 2 ud support. Expected {benchmark}, got {support}."
        )


def load_eq2b_coord_term(prefix: str) -> pd.Series:
    key_terms_path = RESULTS_SECONDARY_DIR / f"{prefix}_key_terms.csv"
    if not key_terms_path.exists():
        raise FileNotFoundError(
            "This diagnostic requires the Eq. 2b bundle. "
            "Run code/secondary/15_wiod_eq2b_hawk_dove.py first."
        )
    key_terms = pd.read_csv(key_terms_path)
    eq2b_coord = key_terms.loc[key_terms["term"] == "ln_robots_lag1:coord_pre_c"]
    if eq2b_coord.empty:
        raise RuntimeError(
            f"Missing ln_robots_lag1:coord_pre_c in {key_terms_path}"
        )
    return eq2b_coord.iloc[0]


def build_decomposition_table(
    eq2_coord_full_row: pd.Series,
    eq2_coord_intersection_row: pd.Series,
    eq2b_coord_row: pd.Series,
    sample: pd.DataFrame,
) -> pd.DataFrame:
    rows = [
        {
            "review_order": 1,
            "comparison_id": "EQ2_COORD_FULL",
            "title": (
                "WIOD Eq. 2 coordination moderation "
                f"({int(eq2_coord_full_row['n_countries'])}-country full sample)"
            ),
            "term": "ln_robots_lag1:coord_pre_c",
            "n_countries": int(eq2_coord_full_row["n_countries"]),
            "n_entities": int(eq2_coord_full_row["n_entities"]),
            "n_observations": int(eq2_coord_full_row["n_observations"]),
            "years": eq2_coord_full_row["years"],
            "coef_country_cluster": float(eq2_coord_full_row["coef_country_cluster"]),
            "se_country_cluster": float(eq2_coord_full_row["se_country_cluster"]),
            "p_country_cluster": float(eq2_coord_full_row["p_country_cluster"]),
            "p_wild_cluster": float(eq2_coord_full_row["p_wild_cluster"]),
        },
        {
            "review_order": 2,
            "comparison_id": "EQ2_COORD_EQ2B_SAMPLE",
            "title": "WIOD Eq. 2 coordination moderation (exact Eq. 2b sample)",
            "term": "ln_robots_lag1:coord_pre_c",
            "n_countries": int(sample["country_code"].nunique()),
            "n_entities": int(sample["entity"].nunique()),
            "n_observations": int(len(sample)),
            "years": f"{int(sample['year_int'].min())}-{int(sample['year_int'].max())}",
            "coef_country_cluster": float(eq2_coord_intersection_row["coef_country_cluster"]),
            "se_country_cluster": float(eq2_coord_intersection_row["se_country_cluster"]),
            "p_country_cluster": float(eq2_coord_intersection_row["p_country_cluster"]),
            "p_wild_cluster": float(eq2_coord_intersection_row["p_wild_cluster"]),
        },
        {
            "review_order": 3,
            "comparison_id": "EQ2B_COORD_TERM",
            "title": "WIOD Eq. 2b joint coord x ud moderation (coord term only)",
            "term": "ln_robots_lag1:coord_pre_c",
            "n_countries": int(sample["country_code"].nunique()),
            "n_entities": int(sample["entity"].nunique()),
            "n_observations": int(len(sample)),
            "years": f"{int(sample['year_int'].min())}-{int(sample['year_int'].max())}",
            "coef_country_cluster": float(eq2b_coord_row["coef_country_cluster"]),
            "se_country_cluster": float(eq2b_coord_row["se_country_cluster"]),
            "p_country_cluster": float(eq2b_coord_row["p_country_cluster"]),
            "p_wild_cluster": float(eq2b_coord_row["p_wild_cluster"]),
        },
    ]
    comparison = pd.DataFrame(rows).sort_values("review_order").reset_index(drop=True)
    base_coef = float(
        comparison.loc[
            comparison["comparison_id"] == "EQ2_COORD_FULL", "coef_country_cluster"
        ].iloc[0]
    )
    base_p_wild = float(
        comparison.loc[
            comparison["comparison_id"] == "EQ2_COORD_FULL", "p_wild_cluster"
        ].iloc[0]
    )
    eq2b_coef = float(
        comparison.loc[
            comparison["comparison_id"] == "EQ2B_COORD_TERM", "coef_country_cluster"
        ].iloc[0]
    )
    eq2b_p_wild = float(
        comparison.loc[
            comparison["comparison_id"] == "EQ2B_COORD_TERM", "p_wild_cluster"
        ].iloc[0]
    )
    comparison["delta_vs_eq2_full_coef"] = comparison["coef_country_cluster"] - base_coef
    comparison["delta_vs_eq2_full_p_wild"] = comparison["p_wild_cluster"] - base_p_wild
    comparison["delta_vs_eq2b_coord_term_coef"] = comparison["coef_country_cluster"] - eq2b_coef
    comparison["delta_vs_eq2b_coord_term_p_wild"] = comparison["p_wild_cluster"] - eq2b_p_wild
    return comparison


def classify_decomposition(comparison: pd.DataFrame) -> str:
    eq2_full = comparison.loc[comparison["comparison_id"] == "EQ2_COORD_FULL"].iloc[0]
    eq2_intersection = comparison.loc[
        comparison["comparison_id"] == "EQ2_COORD_EQ2B_SAMPLE"
    ].iloc[0]
    eq2b = comparison.loc[comparison["comparison_id"] == "EQ2B_COORD_TERM"].iloc[0]

    sample_shift = abs(
        float(eq2_full["coef_country_cluster"])
        - float(eq2_intersection["coef_country_cluster"])
    )
    specification_shift = abs(
        float(eq2_intersection["coef_country_cluster"])
        - float(eq2b["coef_country_cluster"])
    )
    if sample_shift <= 0.0005 and specification_shift > sample_shift:
        return "mostly specification effect"
    if specification_shift <= 0.0005 and sample_shift > specification_shift:
        return "mostly sample-loss effect"
    return "mixed effect"


def write_comparison_markdown(comparison: pd.DataFrame, interpretation: str) -> None:
    lines = [
        "# WIOD Eq. 2 Coordination Sample Decomposition",
        "",
        "This diagnostic isolates whether the coordination attenuation in Eq. 2b is mainly due to moving from the broader coord sample to the exact joint-modulator intersection or due to adding union density and the three-way term on the same rows.",
        "",
        f"Interpretation: **{interpretation}**",
        "",
        "| comparison_id | title | n_countries | n_entities | n_observations | coef_country_cluster | se_country_cluster | p_country_cluster | p_wild_cluster | delta_vs_eq2_full_coef | delta_vs_eq2_full_p_wild | delta_vs_eq2b_coord_term_coef | delta_vs_eq2b_coord_term_p_wild |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for _, row in comparison.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["comparison_id"]),
                    str(row["title"]),
                    str(int(row["n_countries"])),
                    str(int(row["n_entities"])),
                    str(int(row["n_observations"])),
                    f"{float(row['coef_country_cluster']):.6f}",
                    f"{float(row['se_country_cluster']):.6f}",
                    f"{float(row['p_country_cluster']):.6f}",
                    f"{float(row['p_wild_cluster']):.6f}",
                    f"{float(row['delta_vs_eq2_full_coef']):.6f}",
                    f"{float(row['delta_vs_eq2_full_p_wild']):.6f}",
                    f"{float(row['delta_vs_eq2b_coord_term_coef']):.6f}",
                    f"{float(row['delta_vs_eq2b_coord_term_p_wild']):.6f}",
                ]
            )
            + " |"
        )
    COMPARISON_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    df = load_or_build_wiod_panel()
    sample, controls = prepare_wiod_joint_coord_ud_sample(
        df,
        capital_proxy=args.capital_proxy,
        include_gdp=not args.no_gdp,
    )
    check_sample_integrity(sample)

    eq2_coord_full_row, eq2_ud_row = load_reference_rows()
    check_against_ud_support(sample, eq2_ud_row)

    rhs_terms = ["ln_robots_lag1", "ln_robots_lag1:coord_pre_c"] + controls
    prefix = f"diagnostic_wiod_eq2_coord_on_eq2b_sample_full_{args.capital_proxy}_continuous"

    logger.info(
        "WIOD Eq. 2 coord-on-intersection sample: "
        f"{len(sample)} obs, {sample['entity'].nunique()} entities, "
        f"{sample['country_code'].nunique()} countries"
    )
    result = fit_all_inference(sample, outcome="ln_h_empe", rhs_terms=rhs_terms)
    key_df = write_model_bundle(
        prefix=prefix,
        title="WIOD Eq. 2 coordination moderation on exact Eq. 2b sample (diagnostic sample-decomposition check)",
        result=result,
        rhs_terms=rhs_terms,
        key_terms=["ln_robots_lag1", "ln_robots_lag1:coord_pre_c"],
        flags={
            "capital_proxy": args.capital_proxy,
            "include_gdp": not args.no_gdp,
            "headline_se": "country_cluster",
            "secondary_se": ["entity_cluster", "driscoll_kraay"],
            "wild_cluster_bootstrap_reps": args.bootstrap_reps,
            "diagnostic": "eq2_coord_on_eq2b_sample",
        },
        sample_mode="full",
        bootstrap_reps=args.bootstrap_reps,
        bootstrap_show_progress=not args.no_bootstrap_progress,
        out_dir=RESULTS_SECONDARY_DIR,
        extra_lines=[
            "Outcome: ln_h_empe (WIOD H_EMPE labour-hours proxy)",
            "Role: diagnostic decomposition check, not a new headline equation",
            "Sample: exact row-level Eq. 2b support using the coord x ud intersection helper",
            f"Controls: {', '.join(controls)}",
            "Interpretation target: separate sample-loss attenuation from the extra attenuation caused by adding ud and the three-way term.",
            "Inference: country cluster headline; entity cluster + Driscoll-Kraay comparison",
        ],
    )

    eq2_coord_intersection = key_df.loc[key_df["term"] == "ln_robots_lag1:coord_pre_c"]
    if eq2_coord_intersection.empty:
        raise RuntimeError(
            f"Missing ln_robots_lag1:coord_pre_c in {RESULTS_SECONDARY_DIR / f'{prefix}_key_terms.csv'}"
        )
    eq2b_prefix = f"exploratory_wiod_eq2b_coord_ud_full_{args.capital_proxy}_continuous"
    eq2b_coord = load_eq2b_coord_term(eq2b_prefix)
    comparison = build_decomposition_table(
        eq2_coord_full_row=eq2_coord_full_row,
        eq2_coord_intersection_row=eq2_coord_intersection.iloc[0],
        eq2b_coord_row=eq2b_coord,
        sample=sample,
    )
    comparison.to_csv(COMPARISON_CSV_PATH, index=False)
    interpretation = classify_decomposition(comparison)
    write_comparison_markdown(comparison, interpretation)

    logger.info(
        "Coord decomposition saved to "
        f"{COMPARISON_CSV_PATH} and {COMPARISON_MD_PATH}"
    )
    logger.info(
        "Decomposition result: "
        + ", ".join(
            f"{row['comparison_id']}={row['coef_country_cluster']:.4f}"
            for _, row in comparison.iterrows()
        )
    )
    logger.info(f"Interpretation: {interpretation}")


if __name__ == "__main__":
    main()
