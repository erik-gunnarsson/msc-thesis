'''
Equation 2: Institutional Moderation – Coordination

ln(Hours) = β₁ ln(Robots)_{t-1} + β₃[ln(Robots) × HighCoord] + controls + FE
- HighCoord: 1 if Coord ≥ 4 (Garnero 2021)
- Data from 2-cleaning-data.py (high_coord pre-built)

Usage (run from project root):
  python code/4-equation2-institutional-moderation-coordination.py 1   # diagnostics only
  python code/4-equation2-institutional-moderation-coordination.py 2   # diagnostics + model
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

STEPS = {1: "diagnostics", 2: "coordination_model"}


def step_diagnostics(df: pd.DataFrame) -> None:
    log_diagnostics(df)


def step_coordination_model(df_raw: pd.DataFrame) -> None:
    controls = get_controls(df_raw)
    controls_str = " + ".join(controls)

    df = prepare_panel(df_raw, require=["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap", "coord"])
    for c in controls:
        if c in df.columns:
            df = df.dropna(subset=[c])
    df = df.drop_duplicates(subset=["entity", "year_int"]).copy()

    # high_coord from 2-cleaning-data.py; fallback if using old cleaned_data
    if "high_coord" not in df.columns:
        logger.warning("high_coord missing in cleaned_data; computing from coord. Re-run 2-cleaning-data.py for pre-built column.")
        df["high_coord"] = np.where(df["coord"].notna(), (df["coord"] >= 4).astype(int), np.nan)
    df = df.dropna(subset=["high_coord"])

    formula = f"ln_hours ~ ln_robots_lag1 + ln_robots_lag1:high_coord + {controls_str} + EntityEffects + TimeEffects"
    logger.info(f"Formula: {formula}")

    res = run_panelols(formula, df)

    logger.info(f"\n{BAR}\n  Coordination (HighCoord ≥ 4)\n{SEP}")
    print(res)

    OUTPUT_PATH.mkdir(exist_ok=True)
    with open(OUTPUT_PATH / "equation2_coordination_moderation.txt", "w") as f:
        f.write(str(res))

    eff_low = res.params.get("ln_robots_lag1", np.nan)
    eff_high = eff_low + res.params.get("ln_robots_lag1:high_coord", 0)
    logger.info(f"\nMarginal effects:")
    logger.info(f"  Low coordination (Coord<4):  {eff_low:.4f}")
    logger.info(f"  High coordination (Coord≥4): {eff_high:.4f}")
    logger.info(f"  Difference (interaction):    {res.params.get('ln_robots_lag1:high_coord', np.nan):.4f}")
    logger.info(f"Sample: {res.nobs} obs\n{BAR}\n")


def main():
    step = get_step(1)
    logger.info(f"Step {step}: {STEPS.get(step, '?')}")

    df = pd.read_csv(CLEANED_PATH)

    if step == 1:
        step_diagnostics(df)
        return

    if step == 2:
        step_diagnostics(df)
        step_coordination_model(df)
        return

    logger.error(f"Unknown step {step}. Use 1 or 2.")
    sys.exit(1)


if __name__ == "__main__":
    main()
