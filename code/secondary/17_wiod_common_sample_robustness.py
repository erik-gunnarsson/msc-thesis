'''
Run a like-for-like WIOD common-sample robustness table on the exact
coord x ud intersection support.

This appendix-facing script estimates Eq. 1, Eq. 2 coord, Eq. 2 ud, and
Eq. 2b on the same 21-country sample so coefficient differences are due to
specification rather than sample composition.
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

from _paths import RESULTS_SECONDARY_DIR
from _wiod_model_utils import load_or_build_wiod_panel
from _wiod_panel_utils import (
    build_fe_formula,
    fit_all_inference,
    prepare_wiod_joint_coord_ud_sample,
    summarise_key_terms,
)


SUMMARY_CSV = RESULTS_SECONDARY_DIR / "wiod_common_sample_robustness.csv"
SUMMARY_MD = RESULTS_SECONDARY_DIR / "wiod_common_sample_robustness.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--capital-proxy",
        choices=["k", "capcomp"],
        default="k",
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
        help="Wild cluster bootstrap repetitions for focal terms.",
    )
    return parser.parse_args()


def restricted_formulas(rhs_terms: list[str], key_terms: list[str]) -> dict[str, str]:
    return {
        term: build_fe_formula("ln_h_empe", [rhs for rhs in rhs_terms if rhs != term])
        for term in key_terms
    }


def sample_support(sample: pd.DataFrame) -> dict[str, object]:
    return {
        "n_countries": int(sample["country_code"].nunique()),
        "n_entities": int(sample["entity"].nunique()),
        "n_observations": int(len(sample)),
        "years": f"{int(sample['year_int'].min())}-{int(sample['year_int'].max())}",
    }


def run_spec(
    sample: pd.DataFrame,
    *,
    model_id: str,
    title: str,
    rhs_terms: list[str],
    focal_terms: list[tuple[str, str]],
    bootstrap_reps: int,
) -> list[dict[str, object]]:
    result = fit_all_inference(sample, outcome="ln_h_empe", rhs_terms=rhs_terms)
    key_terms = [term for term, _ in focal_terms]
    summary = summarise_key_terms(
        result,
        key_terms=key_terms,
        restricted_formulas=restricted_formulas(rhs_terms, key_terms),
        bootstrap_reps=bootstrap_reps,
    )
    support = sample_support(sample)
    rows: list[dict[str, object]] = []
    for term, label in focal_terms:
        row = summary.loc[summary["term"] == term]
        if row.empty:
            raise RuntimeError(f"Missing focal term {term} for {model_id}")
        key = row.iloc[0]
        rows.append(
            {
                "model_id": model_id,
                "title": title,
                "term": term,
                "term_label": label,
                **support,
                "coef_country_cluster": float(key["coef_country_cluster"]),
                "se_country_cluster": float(key["se_country_cluster"]),
                "p_country_cluster": float(key["p_country_cluster"]),
                "p_wild_cluster": float(key["p_wild_cluster"]),
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    RESULTS_SECONDARY_DIR.mkdir(parents=True, exist_ok=True)

    panel = load_or_build_wiod_panel()
    sample, controls = prepare_wiod_joint_coord_ud_sample(
        panel,
        capital_proxy=args.capital_proxy,
        include_gdp=not args.no_gdp,
    )
    support = sample_support(sample)
    expected = {"n_countries": 21, "n_entities": 206, "n_observations": 2068, "years": "2001-2014"}
    if support != expected:
        raise RuntimeError(f"Unexpected common-sample support. Expected {expected}, got {support}.")

    rows: list[dict[str, object]] = []
    rows.extend(
        run_spec(
            sample,
            model_id="EQ1_COMMON",
            title="WIOD Eq. 1 baseline on exact coord x ud common sample",
            rhs_terms=["ln_robots_lag1"] + controls,
            focal_terms=[("ln_robots_lag1", "Eq. 1 robot coefficient")],
            bootstrap_reps=args.bootstrap_reps,
        )
    )
    rows.extend(
        run_spec(
            sample,
            model_id="EQ2_COORD_COMMON",
            title="WIOD Eq. 2 coordination moderation on exact coord x ud common sample",
            rhs_terms=["ln_robots_lag1", "ln_robots_lag1:coord_pre_c"] + controls,
            focal_terms=[("ln_robots_lag1:coord_pre_c", "Eq. 2 coord interaction")],
            bootstrap_reps=args.bootstrap_reps,
        )
    )
    rows.extend(
        run_spec(
            sample,
            model_id="EQ2_UD_COMMON",
            title="WIOD Eq. 2 union-density reference on exact coord x ud common sample",
            rhs_terms=["ln_robots_lag1", "ln_robots_lag1:ud_pre_c"] + controls,
            focal_terms=[("ln_robots_lag1:ud_pre_c", "Eq. 2 ud interaction")],
            bootstrap_reps=args.bootstrap_reps,
        )
    )
    rows.extend(
        run_spec(
            sample,
            model_id="EQ2B_COMMON",
            title="WIOD Eq. 2b joint coord x ud moderation on exact common sample",
            rhs_terms=[
                "ln_robots_lag1",
                "ln_robots_lag1:coord_pre_c",
                "ln_robots_lag1:ud_pre_c",
                "ln_robots_lag1:coord_pre_c:ud_pre_c",
            ]
            + controls,
            focal_terms=[
                ("ln_robots_lag1:coord_pre_c", "Eq. 2b coord term"),
                ("ln_robots_lag1:ud_pre_c", "Eq. 2b ud term"),
                ("ln_robots_lag1:coord_pre_c:ud_pre_c", "Eq. 2b Hawk-Dove three-way"),
            ],
            bootstrap_reps=args.bootstrap_reps,
        )
    )

    summary = pd.DataFrame(rows)
    summary["review_order"] = summary["model_id"].map(
        {
            "EQ1_COMMON": 1,
            "EQ2_COORD_COMMON": 2,
            "EQ2_UD_COMMON": 3,
            "EQ2B_COMMON": 4,
        }
    )
    summary = summary.sort_values(["review_order", "term"]).reset_index(drop=True)
    summary.to_csv(SUMMARY_CSV, index=False)

    md_lines = [
        "# WIOD Common-Sample Robustness Table",
        "",
        "All specifications below use the exact 21-country coord x ud intersection sample, so coefficient differences are specification-driven rather than sample-driven.",
        "",
        f"Support: {support['n_countries']} countries, {support['n_entities']} entities, {support['n_observations']} observations, {support['years']}",
        "",
        "| model_id | term_label | coef_country_cluster | se_country_cluster | p_country_cluster | p_wild_cluster |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for _, row in summary.iterrows():
        md_lines.append(
            "| "
            + " | ".join(
                [
                    str(row["model_id"]),
                    str(row["term_label"]),
                    f"{float(row['coef_country_cluster']):.6f}",
                    f"{float(row['se_country_cluster']):.6f}",
                    f"{float(row['p_country_cluster']):.6f}",
                    f"{float(row['p_wild_cluster']):.6f}",
                ]
            )
            + " |"
        )
    SUMMARY_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    logger.info(
        "WIOD common-sample robustness table saved to "
        f"{SUMMARY_CSV} and {SUMMARY_MD}"
    )


if __name__ == "__main__":
    main()
