'''
KLEMS institutional moderation runner.

Thesis mapping: Equation 2 for the main moderator specifications.

ln(LI) = β₁ ln(Robots)_{t-1} + β₂[ln(Robots) × M_c] + controls + FE

where LI = labour input proxy and M_c is a predetermined institutional
moderator (usually ud_pre_c or coord_pre_c, with adjcov also supported).

Coord is continuous by default; binary (Coord ≥ 4) available via
--coord-mode binary as robustness.

CLI flags:
  --moderator coord|adjcov|ud|...   (default: coord)
  --sample full|common              (default: full)
  --coord-mode continuous|binary    (default: continuous)
  --se clustered|driscoll-kraay     (default: clustered)
  --trends none|bucket              (default: none)

Usage:
  python code/05_klems_institution_moderation.py 2 --moderator ud --sample full
  python code/05_klems_institution_moderation.py 2 --moderator coord --sample common
  python code/05_klems_institution_moderation.py 2 --moderator adjcov --sample common
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

STEPS = {1: "diagnostics", 2: "moderation_model"}


def step_diagnostics(df: pd.DataFrame) -> None:
    log_diagnostics(df)


def step_coordination_model(df_raw: pd.DataFrame, args) -> None:
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

    interaction_col = f"ln_robots_lag1:{mod_var}"
    formula = f"ln_hours ~ ln_robots_lag1 + {interaction_col} + {controls_str} + EntityEffects + TimeEffects"
    formula = add_trend_terms(df, formula, args.trends)
    logger.info(f"Formula: {formula}")

    res = run_panelols(formula, df, cov_type=args.se)

    tag = f"eq2_{args.moderator}_{args.sample}"
    write_sample_manifest(df, tag, sample_mode=args.sample)
    write_run_metadata(
        "05_klems_institution_moderation.py",
        {"moderator": args.moderator, "sample": args.sample,
         "coord_mode": args.coord_mode, "se": args.se, "trends": args.trends},
        n_obs=res.nobs, n_entities=df["entity"].nunique(),
    )

    logger.info(f"\n{BAR}\n  Institutional moderation ({args.moderator}, {args.sample} sample)\n{SEP}")
    print(res)

    OUTPUT_PATH.mkdir(exist_ok=True)
    out_name = f"equation2_{args.moderator}_moderation_{args.sample}sample.txt"
    with open(OUTPUT_PATH / out_name, "w") as f:
        f.write(format_sample_header(df) + str(res))

    eff_base = res.params.get("ln_robots_lag1", np.nan)
    eff_inter = res.params.get(interaction_col, 0)

    if is_binary:
        logger.info(f"\nMarginal effects:")
        logger.info(f"  Low coordination ({mod_var}=0): {eff_base:.4f}")
        logger.info(f"  High coordination ({mod_var}=1): {eff_base + eff_inter:.4f}")
        logger.info(f"  Difference (interaction):    {eff_inter:.4f}")
    else:
        logger.info(f"\nβ₁ (ln_robots_lag1): {eff_base:.4f}")
        logger.info(f"β (interaction): {eff_inter:.4f}")
        logger.info(f"  (Effect at mean moderator = β₁; each unit ↑ moderator shifts slope by β_inter)")

    logger.info(f"Sample: {res.nobs} obs\n{BAR}\n")


def main():
    args = parse_args(default_moderator="coord")
    step = args.step
    logger.info(f"Step {step}: {STEPS.get(step, '?')}")

    df = pd.read_csv(CLEANED_PATH)

    if step == 1:
        step_diagnostics(df)
        return

    if step == 2:
        step_diagnostics(df)
        step_coordination_model(df, args)
        return

    logger.error(f"Unknown step {step}. Use 1 or 2.")
    sys.exit(1)


if __name__ == "__main__":
    main()
