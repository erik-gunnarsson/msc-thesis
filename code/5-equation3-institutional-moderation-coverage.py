'''
Equation 3: Institutional Moderation – Coverage

ln(Hours) = β₁ ln(Robots)_{t-1} + β₂[ln(Robots) × AdjCov_c] + controls + FE
- AdjCov: collective bargaining coverage (continuous, centered)
- Data from 2-cleaning-data.py (adjcov_centered pre-built)

Usage (run from project root):
  python code/5-equation3-institutional-moderation-coverage.py 1   # diagnostics
  python code/5-equation3-institutional-moderation-coverage.py 2   # diagnostics + model
  python code/5-equation3-institutional-moderation-coverage.py 3   # coverage plot only
'''

import sys

import pandas as pd
import numpy as np
from loguru import logger

from _equation_utils import (
    CLEANED_PATH,
    OUTPUT_PATH,
    BAR,
    SEP,
    get_step,
    get_controls,
    prepare_panel,
    run_panelols,
    log_diagnostics,
)

STEPS = {1: "diagnostics", 2: "coverage_model", 3: "coverage_plot"}


def step_diagnostics(df: pd.DataFrame) -> None:
    log_diagnostics(df)


def step_coverage_model(df_raw: pd.DataFrame) -> None:
    controls = get_controls(df_raw)
    controls_str = " + ".join(controls)

    df = prepare_panel(df_raw, require=["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap", "adjcov"])
    for c in controls:
        if c in df.columns:
            df = df.dropna(subset=[c])
    df = df.drop_duplicates(subset=["entity", "year_int"]).copy()

    if "adjcov_centered" not in df.columns:
        logger.warning("adjcov_centered missing; computing from adjcov. Re-run 2-cleaning-data.py.")
        df["adjcov_centered"] = df["adjcov"] - df["adjcov"].mean()
    df["ln_robots_adjcov"] = df["ln_robots_lag1"] * df["adjcov_centered"]

    formula = f"ln_hours ~ ln_robots_lag1 + ln_robots_adjcov + {controls_str} + EntityEffects + TimeEffects"
    logger.info(f"Formula: {formula}")

    res = run_panelols(formula, df)

    logger.info(f"\n{BAR}\n  Coverage (AdjCov centered)\n{SEP}")
    print(res)

    OUTPUT_PATH.mkdir(exist_ok=True)
    with open(OUTPUT_PATH / "equation3_coverage_moderation.txt", "w") as f:
        f.write(str(res))

    b1 = res.params.get("ln_robots_lag1", np.nan)
    b2 = res.params.get("ln_robots_adjcov", np.nan)
    logger.info(f"\nβ₁ (ln_robots_lag1):      {b1:.4f}")
    logger.info(f"β₂ (ln_robots × AdjCov_c): {b2:.4f}")
    logger.info(f"Sample: {res.nobs} obs (β₁ = effect at mean AdjCov)\n{BAR}\n")


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
    step = get_step(1)
    logger.info(f"Step {step}: {STEPS.get(step, '?')}")

    df = pd.read_csv(CLEANED_PATH)

    if step == 1:
        step_diagnostics(df)
        return

    if step == 2:
        step_diagnostics(df)
        step_coverage_model(df)
        return

    if step == 3:
        step_coverage_plot(df)
        return

    logger.error(f"Unknown step {step}. Use 1, 2, or 3.")
    sys.exit(1)


if __name__ == "__main__":
    main()
