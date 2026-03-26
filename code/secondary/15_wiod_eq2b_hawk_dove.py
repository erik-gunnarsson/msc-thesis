'''
WIOD Eq. 2b joint coord x ud moderation (Hawk-Dove extension).

This script estimates a continuous three-way interaction:

ln_h_empe_ijt = beta1 ln_robots_lag1_ijt
              + beta2 [ln_robots_lag1_ijt x coord_pre_c]
              + beta3 [ln_robots_lag1_ijt x ud_pre_c]
              + beta4 [ln_robots_lag1_ijt x coord_pre_c x ud_pre_c]
              + X_ijt + alpha_ij + delta_t + eps_ijt

The binary Hawk-Dove classification is diagnostic only and is handled by the
separate exploration gate script under code/exploration/wiod_feasibility.
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
from _wiod_panel_utils import (
    fit_all_inference,
    prepare_wiod_joint_coord_ud_sample,
)


COMPARISON_CSV_PATH = RESULTS_SECONDARY_DIR / "wiod_eq2b_coord_ud_comparison.csv"
COMPARISON_MD_PATH = RESULTS_SECONDARY_DIR / "wiod_eq2b_coord_ud_comparison.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--capital-proxy",
        choices=["k", "capcomp"],
        default="k",
        help="WIOD capital control; K is the frozen default for the Eq. 2b extension.",
    )
    parser.add_argument(
        "--no-gdp",
        action="store_true",
        help="Omit GDP growth from the control set.",
    )
    parser.add_argument(
        "--bootstrap-reps",
        type=int,
        default=199,
        help="Wild cluster bootstrap repetitions for the joint interaction terms.",
    )
    return parser.parse_args()


def build_eq2b_rhs_terms() -> list[str]:
    return [
        "ln_robots_lag1",
        "ln_robots_lag1:coord_pre_c",
        "ln_robots_lag1:ud_pre_c",
        "ln_robots_lag1:coord_pre_c:ud_pre_c",
    ]


def collect_eq2b_comparison(prefix: str, sample: pd.DataFrame) -> pd.DataFrame:
    summary_path = RESULTS_CORE_DIR / "wiod_first_results_summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError(
            "Eq. 2b comparison requires results/core/wiod_first_results_summary.csv. "
            "Run code/core/14_wiod_first_results.py first."
        )

    summary = pd.read_csv(summary_path)
    needed = ["EQ1", "EQ2_COORD", "EQ2_UD"]
    missing = [model_id for model_id in needed if model_id not in set(summary["model_id"])]
    if missing:
        raise RuntimeError(
            "Eq. 2b comparison is missing baseline first-results rows for: "
            + ", ".join(missing)
        )

    eq2b_key_terms = pd.read_csv(RESULTS_SECONDARY_DIR / f"{prefix}_key_terms.csv")
    eq2b_terms = {
        "ln_robots_lag1:coord_pre_c": "Eq. 2b coord slope term",
        "ln_robots_lag1:ud_pre_c": "Eq. 2b ud slope term",
        "ln_robots_lag1:coord_pre_c:ud_pre_c": "Eq. 2b Hawk-Dove three-way term",
    }

    rows: list[dict[str, object]] = []
    for model_id in needed:
        row = summary.loc[summary["model_id"] == model_id].iloc[0]
        rows.append(
            {
                "review_order": int(row["review_order"]),
                "model_id": row["model_id"],
                "title": row["title"],
                "role": row["role"],
                "term": row["focal_term"],
                "term_label": row["focal_term"],
                "n_countries": int(row["n_countries"]),
                "n_entities": int(row["n_entities"]),
                "n_observations": int(row["n_observations"]),
                "years": row["years"],
                "coef_country_cluster": row["coef_country_cluster"],
                "se_country_cluster": row["se_country_cluster"],
                "p_country_cluster": row["p_country_cluster"],
                "p_wild_cluster": row["p_wild_cluster"],
            }
        )

    for order, (term, label) in enumerate(eq2b_terms.items(), start=4):
        key_row = eq2b_key_terms.loc[eq2b_key_terms["term"] == term]
        if key_row.empty:
            raise RuntimeError(f"Eq. 2b key term {term} missing from {prefix}_key_terms.csv")
        key = key_row.iloc[0]
        rows.append(
            {
                "review_order": order,
                "model_id": "EQ2B_COORD_UD",
                "title": "WIOD Eq. 2b joint coord x ud moderation",
                "role": "exploratory Hawk-Dove extension",
                "term": term,
                "term_label": label,
                "n_countries": int(sample["country_code"].nunique()),
                "n_entities": int(sample["entity"].nunique()),
                "n_observations": int(len(sample)),
                "years": f"{int(sample['year_int'].min())}-{int(sample['year_int'].max())}",
                "coef_country_cluster": key["coef_country_cluster"],
                "se_country_cluster": key["se_country_cluster"],
                "p_country_cluster": key["p_country_cluster"],
                "p_wild_cluster": key["p_wild_cluster"],
            }
        )

    comparison = pd.DataFrame(rows).sort_values(["review_order", "term"]).reset_index(drop=True)
    comparison.to_csv(COMPARISON_CSV_PATH, index=False)

    md_lines = [
        "# WIOD Eq. 2b Comparison",
        "",
        "This table compares the current first-results package to the exploratory joint coord x ud extension.",
        "",
        "| model_id | title | term_label | n_countries | n_entities | n_observations | coef_country_cluster | se_country_cluster | p_country_cluster | p_wild_cluster |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for _, row in comparison.iterrows():
        md_lines.append(
            "| "
            + " | ".join(
                [
                    str(row["model_id"]),
                    str(row["title"]),
                    str(row["term_label"]),
                    str(int(row["n_countries"])),
                    str(int(row["n_entities"])),
                    str(int(row["n_observations"])),
                    f"{float(row['coef_country_cluster']):.6f}",
                    f"{float(row['se_country_cluster']):.6f}",
                    f"{float(row['p_country_cluster']):.6f}",
                    f"{float(row['p_wild_cluster']):.6f}",
                ]
            )
            + " |"
        )
    COMPARISON_MD_PATH.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return comparison


def main() -> None:
    args = parse_args()
    df = load_or_build_wiod_panel()
    sample, controls = prepare_wiod_joint_coord_ud_sample(
        df,
        capital_proxy=args.capital_proxy,
        include_gdp=not args.no_gdp,
    )

    rhs_terms = build_eq2b_rhs_terms() + controls
    prefix = f"exploratory_wiod_eq2b_coord_ud_full_{args.capital_proxy}_continuous"

    logger.info(
        "WIOD Eq. 2b sample: "
        f"{len(sample)} obs, {sample['entity'].nunique()} entities, "
        f"{sample['country_code'].nunique()} countries"
    )
    result = fit_all_inference(
        sample,
        outcome="ln_h_empe",
        rhs_terms=rhs_terms,
    )

    key_df = write_model_bundle(
        prefix=prefix,
        title="WIOD Eq. 2b joint coord x ud moderation (exploratory Hawk-Dove extension)",
        result=result,
        rhs_terms=rhs_terms,
        key_terms=[
            "ln_robots_lag1",
            "ln_robots_lag1:coord_pre_c",
            "ln_robots_lag1:ud_pre_c",
            "ln_robots_lag1:coord_pre_c:ud_pre_c",
        ],
        flags={
            "capital_proxy": args.capital_proxy,
            "include_gdp": not args.no_gdp,
            "headline_se": "country_cluster",
            "secondary_se": ["entity_cluster", "driscoll_kraay"],
            "wild_cluster_bootstrap_reps": args.bootstrap_reps,
            "equation": "eq2b_hawk_dove",
        },
        sample_mode="full",
        bootstrap_reps=args.bootstrap_reps,
        out_dir=RESULTS_SECONDARY_DIR,
        extra_lines=[
            "Outcome: ln_h_empe (WIOD H_EMPE labour-hours proxy)",
            "Role: exploratory theory-testing extension after the main Eq. 2 results",
            "Moderators: coord_pre_c and ud_pre_c jointly included as centered continuous moderators",
            f"Controls: {', '.join(controls)}",
            "Interpret the three-way term as the Hawk-Dove slope contrast, not as a replacement for the focal coordination model.",
            "Inference: country cluster headline; entity cluster + Driscoll-Kraay comparison",
        ],
    )

    comparison = collect_eq2b_comparison(prefix, sample)
    logger.info(f"Eq. 2b key terms rows: {len(key_df)}")
    logger.info(f"Comparison table -> {COMPARISON_CSV_PATH}")
    logger.info(f"Comparison note -> {COMPARISON_MD_PATH}")
    logger.info(
        "Eq. 2b focal terms: "
        + ", ".join(
            f"{row['term']}={row['coef_country_cluster']:.4f}"
            for _, row in key_df.loc[
                key_df["term"].isin(
                    [
                        "ln_robots_lag1:coord_pre_c",
                        "ln_robots_lag1:ud_pre_c",
                        "ln_robots_lag1:coord_pre_c:ud_pre_c",
                    ]
                )
            ].iterrows()
        )
    )
    logger.info(f"Comparison rows saved: {len(comparison)}")


if __name__ == "__main__":
    main()
