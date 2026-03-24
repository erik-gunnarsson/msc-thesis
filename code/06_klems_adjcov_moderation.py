'''
KLEMS AdjCov moderation runner.

Thesis mapping: restricted-sample institutional moderation specification.

ln(LI) = β₁ ln(Robots)_{t-1} + β₂[ln(Robots) × AdjCov_pre_c] + controls + FE

where LI = labour input proxy.
AdjCov: collective bargaining coverage (continuous, centered, predetermined).
This script defaults to the restricted (common) sample — countries with
AdjCov data.  Results are explicitly labeled as restricted-sample.

CLI flags:
  --moderator coord|adjcov|ud|...   (default: adjcov)
  --sample full|common              (default: full)
  --se clustered|driscoll-kraay     (default: clustered)
  --trends none|bucket              (default: none)

Usage:
  python code/06_klems_adjcov_moderation.py 2 --moderator adjcov --sample common
  python code/06_klems_adjcov_moderation.py 3   # coverage plot only
'''

import sys

import pandas as pd
import numpy as np
from loguru import logger

from _klems_utils import (
    CLEANED_PATH,
    OUTPUT_PATH,
    BAR,
    SEP,
    format_sample_header,
    get_controls,
    prepare_panel,
    run_panelols,
    log_diagnostics,
    parse_args,
    moderator_to_columns,
    apply_sample_filter,
    add_trend_terms,
    get_bucket_dummies,
    write_sample_manifest,
    write_run_metadata,
)

STEPS = {1: "diagnostics", 2: "coverage_model", 3: "coverage_plot"}


def step_diagnostics(df: pd.DataFrame) -> None:
    log_diagnostics(df)


def step_coverage_model(df_raw: pd.DataFrame, args) -> None:
    controls = get_controls(df_raw)
    controls_str = " + ".join(controls)

    mod_var, has_var, is_binary = moderator_to_columns(args.moderator, args.coord_mode)
    logger.info(f"Moderator: {args.moderator} → {mod_var} (binary={is_binary})")

    df = apply_sample_filter(df_raw.copy(), args.sample)
    req = ["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap", mod_var]
    df = prepare_panel(df, require=req)
    for c in controls:
        if c in df.columns:
            df = df.dropna(subset=[c])
    df = df.drop_duplicates(subset=["entity", "year_int"]).copy()

    if has_var in df.columns:
        df = df[df[has_var]].copy()

    if args.trends == "bucket":
        get_bucket_dummies(df)

    interaction_col = f"ln_robots_{args.moderator}"
    df[interaction_col] = df["ln_robots_lag1"] * df[mod_var]

    formula = f"ln_hours ~ ln_robots_lag1 + {interaction_col} + {controls_str} + EntityEffects + TimeEffects"
    formula = add_trend_terms(df, formula, args.trends)
    logger.info(f"Formula: {formula}")

    res = run_panelols(formula, df, cov_type=args.se)

    tag = f"eq3_{args.moderator}_{args.sample}"
    write_sample_manifest(df, tag, sample_mode=args.sample)
    write_run_metadata(
        "06_klems_adjcov_moderation.py",
        {"moderator": args.moderator, "sample": args.sample,
         "se": args.se, "trends": args.trends},
        n_obs=res.nobs, n_entities=df["entity"].nunique(),
    )

    sample_label = f"{args.sample} sample"
    if args.moderator == "adjcov":
        sample_label += " — RESTRICTED (AdjCov countries only)"
    logger.info(f"\n{BAR}\n  Coverage moderation ({args.moderator}, {sample_label})\n{SEP}")
    print(res)

    OUTPUT_PATH.mkdir(exist_ok=True)
    restricted_tag = "_restricted" if args.moderator == "adjcov" else ""
    out_name = f"equation3_{args.moderator}_moderation_{args.sample}sample{restricted_tag}.txt"
    with open(OUTPUT_PATH / out_name, "w") as f:
        f.write(format_sample_header(df) + str(res))

    b1 = res.params.get("ln_robots_lag1", np.nan)
    b2 = res.params.get(interaction_col, np.nan)

    if is_binary:
        logger.info(f"\nMarginal effects:")
        logger.info(f"  {mod_var}=0: {b1:.4f}")
        logger.info(f"  {mod_var}=1: {b1 + b2:.4f}")
    else:
        logger.info(f"\nβ₁ (ln_robots_lag1):      {b1:.4f}")
        logger.info(f"β₂ (ln_robots × {args.moderator}): {b2:.4f}")
        logger.info(f"  (β₁ = effect at mean {args.moderator})")

    logger.info(f"Sample: {res.nobs} obs\n{BAR}\n")


def step_coverage_plot(df_raw: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt

    adj_by_country = df_raw.groupby("country_code")["adjcov"].first().dropna()
    if len(adj_by_country) == 0:
        logger.warning("No AdjCov data for plot.")
        return

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(adj_by_country, bins=15, edgecolor="black", alpha=0.7)
    ax.set_xlabel("Collective bargaining coverage (%, baseline)")
    ax.set_ylabel("Number of countries")
    ax.set_title("Distribution of AdjCov across countries")
    OUTPUT_PATH.mkdir(exist_ok=True)
    fig.savefig(OUTPUT_PATH / "coverage_distribution.png", dpi=100, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved {OUTPUT_PATH / 'coverage_distribution.png'}")


def main():
    args = parse_args(default_moderator="adjcov")
    step = args.step
    logger.info(f"Step {step}: {STEPS.get(step, '?')}")

    df = pd.read_csv(CLEANED_PATH)

    if step == 1:
        step_diagnostics(df)
        return

    if step == 2:
        step_diagnostics(df)
        step_coverage_model(df, args)
        return

    if step == 3:
        step_coverage_plot(df)
        return

    logger.error(f"Unknown step {step}. Use 1, 2, or 3.")
    sys.exit(1)


if __name__ == "__main__":
    main()
