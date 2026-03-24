'''
WIOD exposed-vs-sheltered comparison models on the labour panel.

Eq. 5a: ln(H_EMPE)_ijt = beta1 ln(Robots)_{ijt-1}
                       + beta2 [ln(Robots)_{ijt-1} x Exposed_j]
                       + X_ijt + alpha_ij + delta_t + eps_ijt

Eq. 5b: ln(H_EMPE)_ijt = beta1 ln(Robots)_{ijt-1}
                       + beta2 [ln(Robots)_{ijt-1} x Exposed_j]
                       + beta3 [ln(Robots)_{ijt-1} x M_c]
                       + beta4 [ln(Robots)_{ijt-1} x M_c x Exposed_j]
                       + X_ijt + alpha_ij + delta_t + eps_ijt

Headline inference:
  - Country-clustered standard errors
  - Wild cluster bootstrap p-values for the key exposure terms

Secondary comparisons:
  - Entity-clustered SEs
  - Driscoll-Kraay SEs
'''

from __future__ import annotations

import argparse

from loguru import logger

from _wiod_model_utils import load_or_build_wiod_panel, write_model_bundle
from _wiod_panel_utils import (
    add_exposure_interactions,
    fit_all_inference,
    get_wiod_controls,
    moderator_to_columns,
    prepare_wiod_panel,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["eq5a", "eq5b"],
        default="eq5b",
        help="eq5a = exposure heterogeneity only, eq5b = exposure x institution.",
    )
    parser.add_argument(
        "--moderator",
        choices=["coord", "ud", "adjcov"],
        default="coord",
        help="Institutional moderator for eq5b.",
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
        help="Wild cluster bootstrap repetitions for the key exposure terms.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "eq5b" and args.moderator == "adjcov" and args.sample != "common":
        logger.info("Forcing common sample for adjcov Eq. 5b models")
        args.sample = "common"

    df = load_or_build_wiod_panel()
    controls = get_wiod_controls(
        capital_proxy=args.capital_proxy,
        include_gdp=not args.no_gdp,
    )

    mod_var = None
    has_var = None
    require = ["ln_h_empe", "ln_robots_lag1", "exposed_binary"] + controls
    if args.mode == "eq5b":
        mod_var, has_var, _ = moderator_to_columns(args.moderator, args.coord_mode)
        require.append(mod_var)

    sample = prepare_wiod_panel(df, require=require, sample=args.sample)
    if has_var and has_var in sample.columns:
        sample = sample[sample[has_var]].copy()

    exposure_terms = add_exposure_interactions(sample, mod_var=mod_var)
    rhs_terms = ["ln_robots_lag1"] + exposure_terms + controls
    key_terms = ["ln_robots_lag1"] + exposure_terms
    bootstrap_terms = exposure_terms.copy()
    title = "WIOD Eq. 5a exposed vs sheltered heterogeneity"
    if args.mode == "eq5b" and mod_var:
        interaction_term = f"ln_robots_lag1:{mod_var}"
        rhs_terms.insert(2, interaction_term)
        key_terms = ["ln_robots_lag1", "lr_exposed", interaction_term, "lr_mod_exposure"]
        bootstrap_terms = [interaction_term, "lr_mod_exposure"]
        title = f"WIOD Eq. 5b exposure x institution ({args.moderator})"

    exposure_balance = (
        sample.groupby("exposure_group", dropna=False)
        .agg(
            n_obs=("entity", "size"),
            n_entities=("entity", "nunique"),
            n_countries=("country_code", "nunique"),
        )
        .reset_index()
    )

    logger.info(
        f"WIOD {args.mode.upper()} exposure sample: "
        f"{len(sample)} obs, {sample['entity'].nunique()} entities, "
        f"{sample['country_code'].nunique()} countries"
    )
    result = fit_all_inference(sample, outcome="ln_h_empe", rhs_terms=rhs_terms)

    extra = [
        "Outcome: ln_h_empe (WIOD H_EMPE labour-hours proxy)",
        f"Controls: {', '.join(controls)}",
        "Exposure split balance:",
        exposure_balance.to_string(index=False),
        "Inference: country cluster headline; entity cluster + Driscoll-Kraay comparison",
    ]
    if mod_var:
        extra.insert(1, f"Moderator column: {mod_var}")

    prefix = (
        f"wiod_{args.mode}_{args.moderator}_{args.sample}_{args.capital_proxy}_{args.coord_mode}"
        if args.mode == "eq5b"
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
            "moderator": args.moderator if args.mode == "eq5b" else None,
            "sample": args.sample,
            "coord_mode": args.coord_mode if args.mode == "eq5b" else None,
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
