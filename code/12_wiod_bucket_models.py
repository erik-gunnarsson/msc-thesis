'''
WIOD bucket heterogeneity models on the labour panel.

Eq. 3: ln(H_EMPE)_ijt = beta1 ln(Robots)_{ijt-1}
                      + sum_b beta2b [ln(Robots)_{ijt-1} x Bucket_b]
                      + X_ijt + alpha_ij + delta_t + eps_ijt

Eq. 4: ln(H_EMPE)_ijt = beta1 ln(Robots)_{ijt-1}
                      + sum_b beta2b [ln(Robots)_{ijt-1} x Bucket_b]
                      + beta3 [ln(Robots)_{ijt-1} x M_c]
                      + sum_b beta4b [ln(Robots)_{ijt-1} x M_c x Bucket_b]
                      + X_ijt + alpha_ij + delta_t + eps_ijt

Headline inference:
  - Country-clustered standard errors
  - Wild cluster bootstrap p-values for the key heterogeneity terms

Secondary comparisons:
  - Entity-clustered SEs
  - Driscoll-Kraay SEs
'''

from __future__ import annotations

import argparse

from loguru import logger

from _wiod_model_utils import load_or_build_wiod_panel, write_model_bundle
from _wiod_panel_utils import (
    BUCKET_NAMES,
    add_bucket_interactions,
    fit_all_inference,
    get_wiod_controls,
    moderator_to_columns,
    prepare_wiod_panel,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["eq3", "eq4"],
        default="eq4",
        help="eq3 = bucket heterogeneity only, eq4 = bucket x institution.",
    )
    parser.add_argument(
        "--moderator",
        choices=["coord", "ud", "adjcov"],
        default="coord",
        help="Institutional moderator for eq4.",
    )
    parser.add_argument(
        "--sample",
        choices=["full", "common"],
        default="full",
    )
    parser.add_argument(
        "--coord-mode",
        choices=["continuous", "binary"],
        default="continuous",
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
        help="Wild cluster bootstrap repetitions for the key heterogeneity terms.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "eq4" and args.moderator == "adjcov" and args.sample != "common":
        logger.info("Forcing common sample for adjcov Eq. 4 models")
        args.sample = "common"

    df = load_or_build_wiod_panel()
    controls = get_wiod_controls(
        capital_proxy=args.capital_proxy,
        include_gdp=not args.no_gdp,
    )

    mod_var = None
    has_var = None
    require = ["ln_h_empe", "ln_robots_lag1", "bucket"] + controls
    if args.mode == "eq4":
        mod_var, has_var, _ = moderator_to_columns(args.moderator, args.coord_mode)
        require.append(mod_var)

    sample = prepare_wiod_panel(df, require=require, sample=args.sample)
    if has_var and has_var in sample.columns:
        sample = sample[sample[has_var]].copy()

    created_terms = add_bucket_interactions(sample, mod_var=mod_var)
    bucket_terms = [term for term in created_terms if term.startswith("lr_bucket_")]
    triple_terms = [term for term in created_terms if term.startswith("lr_mod_bucket_")]

    if sample["bucket"].nunique() < len(BUCKET_NAMES):
        logger.warning(
            "Not all five buckets are populated in this sample: "
            f"{sorted(sample['bucket'].dropna().unique().tolist())}"
        )

    rhs_terms = ["ln_robots_lag1"] + bucket_terms
    key_terms = ["ln_robots_lag1"] + bucket_terms
    bootstrap_terms = bucket_terms.copy()
    title = "WIOD Eq. 3 bucket heterogeneity"

    if args.mode == "eq4" and mod_var:
        interaction_term = f"ln_robots_lag1:{mod_var}"
        rhs_terms += [interaction_term] + triple_terms
        key_terms = ["ln_robots_lag1", interaction_term] + bucket_terms + triple_terms
        bootstrap_terms = [interaction_term] + triple_terms
        title = f"WIOD Eq. 4 bucket x institution ({args.moderator})"

    rhs_terms += controls

    logger.info(
        f"WIOD {args.mode.upper()} bucket sample: "
        f"{len(sample)} obs, {sample['entity'].nunique()} entities, "
        f"{sample['country_code'].nunique()} countries"
    )
    result = fit_all_inference(sample, outcome="ln_h_empe", rhs_terms=rhs_terms)

    extra = [
        "Outcome: ln_h_empe (WIOD H_EMPE labour-hours proxy)",
        f"Controls: {', '.join(controls)}",
        (
            "Bucket coverage: "
            + ", ".join(
                f"B{bucket}={sample.loc[sample['bucket'] == bucket, 'country_code'].nunique()} countries"
                for bucket in sorted(BUCKET_NAMES)
            )
        ),
        "Inference: country cluster headline; entity cluster + Driscoll-Kraay comparison",
    ]
    if mod_var:
        extra.insert(1, f"Moderator column: {mod_var}")

    prefix = (
        f"wiod_{args.mode}_{args.moderator}_{args.sample}_{args.capital_proxy}_{args.coord_mode}"
        if args.mode == "eq4"
        else f"wiod_{args.mode}_nomod_{args.sample}_{args.capital_proxy}"
    )

    write_model_bundle(
        prefix=prefix,
        title=title,
        result=result,
        rhs_terms=rhs_terms,
        key_terms=key_terms,
        bootstrap_terms=bootstrap_terms,
        flags={
            "mode": args.mode,
            "moderator": args.moderator if args.mode == "eq4" else None,
            "sample": args.sample,
            "coord_mode": args.coord_mode if args.mode == "eq4" else None,
            "capital_proxy": args.capital_proxy,
            "include_gdp": not args.no_gdp,
            "headline_se": "country_cluster",
            "secondary_se": ["entity_cluster", "driscoll_kraay"],
            "wild_cluster_bootstrap_reps": args.bootstrap_reps,
        },
        sample_mode=args.sample,
        bootstrap_reps=args.bootstrap_reps,
        extra_lines=extra,
    )


if __name__ == "__main__":
    main()
