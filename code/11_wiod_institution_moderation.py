'''
WIOD institutional moderation on labour input.

ln(H_EMPE)_ijt = beta1 ln(Robots)_{ijt-1}
               + beta2 [ln(Robots)_{ijt-1} x M_c]
               + X_ijt + alpha_ij + delta_t + eps_ijt

Headline inference:
  - Country-clustered standard errors
  - Wild cluster bootstrap p-values for the robot and interaction terms

Secondary comparisons:
  - Entity-clustered SEs
  - Driscoll-Kraay SEs
'''

from __future__ import annotations

import argparse

from loguru import logger

from _wiod_model_utils import load_or_build_wiod_panel, write_model_bundle
from _wiod_panel_utils import (
    fit_all_inference,
    get_wiod_controls,
    moderator_to_columns,
    prepare_wiod_panel,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--moderator",
        choices=["coord", "ud", "adjcov"],
        default="coord",
        help="Institutional moderator.",
    )
    parser.add_argument(
        "--sample",
        choices=["full", "common"],
        default="full",
        help="Use full sample or adjcov-common sample.",
    )
    parser.add_argument(
        "--coord-mode",
        choices=["continuous", "binary"],
        default="continuous",
        help="Binary coord is a robustness recode (Coord >= 4).",
    )
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
        default=99,
        help="Wild cluster bootstrap repetitions for the key terms.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.moderator == "adjcov" and args.sample != "common":
        logger.info("Forcing common sample for adjcov models")
        args.sample = "common"

    df = load_or_build_wiod_panel()
    mod_var, has_var, is_binary = moderator_to_columns(args.moderator, args.coord_mode)
    controls = get_wiod_controls(
        capital_proxy=args.capital_proxy,
        include_gdp=not args.no_gdp,
    )
    require = ["ln_h_empe", "ln_robots_lag1", mod_var] + controls
    sample = prepare_wiod_panel(df, require=require, sample=args.sample)
    if has_var in sample.columns:
        sample = sample[sample[has_var]].copy()

    interaction_term = f"ln_robots_lag1:{mod_var}"
    rhs_terms = ["ln_robots_lag1", interaction_term] + controls

    logger.info(
        "WIOD Eq. 2 sample: "
        f"{len(sample)} obs, {sample['entity'].nunique()} entities, "
        f"{sample['country_code'].nunique()} countries"
    )
    result = fit_all_inference(sample, outcome="ln_h_empe", rhs_terms=rhs_terms)

    write_model_bundle(
        prefix=f"wiod_eq2_{args.moderator}_{args.sample}_{args.capital_proxy}_{args.coord_mode}",
        title=f"WIOD Eq. 2 institutional moderation ({args.moderator})",
        result=result,
        rhs_terms=rhs_terms,
        key_terms=["ln_robots_lag1", interaction_term],
        flags={
            "moderator": args.moderator,
            "sample": args.sample,
            "coord_mode": args.coord_mode,
            "capital_proxy": args.capital_proxy,
            "include_gdp": not args.no_gdp,
            "moderator_is_binary": is_binary,
            "headline_se": "country_cluster",
            "secondary_se": ["entity_cluster", "driscoll_kraay"],
            "wild_cluster_bootstrap_reps": args.bootstrap_reps,
        },
        sample_mode=args.sample,
        bootstrap_reps=args.bootstrap_reps,
        extra_lines=[
            "Outcome: ln_h_empe (WIOD H_EMPE labour-hours proxy)",
            f"Moderator column: {mod_var}",
            f"Controls: {', '.join(controls)}",
            "Inference: country cluster headline; entity cluster + Driscoll-Kraay comparison",
        ],
    )


if __name__ == "__main__":
    main()
