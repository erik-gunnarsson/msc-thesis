'''
Equation 1: Baseline Model

ln(Hours)_ijt = β₁ ln(Robots)_ijt-1 + X'_ijt γ + α_ij + δ_t + ε_ijt

- Two-way fixed effects (country-industry entity + year)
- Cluster-robust SEs at entity level
- Controls: ln(VA), ln(CAP), ln(GDP), unemployment
'''

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger

try:
    from linearmodels import PanelOLS
    from linearmodels.panel import compare
except ImportError:
    PanelOLS = None

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CLEANED_PATH = DATA_DIR / "cleaned_data.csv"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "outputs"


def main():
    logger.info("Loading cleaned data...")
    df = pd.read_csv(CLEANED_PATH)
    df = df.dropna(subset=["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap"])
    df = df.drop_duplicates(subset=["entity", "year_int"])

    # Panel structure: entity index, time index
    df = df.set_index(["entity", "year_int"], drop=False)
    df = df.sort_index()

    # Baseline: ln_hours ~ ln_robots_lag1 + controls + entity FE + year FE
    controls = ["ln_va", "ln_cap"]
    # Add ln_gdp, unemployment if available and non-null
    if "ln_gdp" in df.columns and df["ln_gdp"].notna().any():
        controls.append("ln_gdp")
    if "unemployment" in df.columns and df["unemployment"].notna().any():
        controls.append("unemployment")

    formula = "ln_hours ~ ln_robots_lag1 + " + " + ".join(controls)
    formula += " + EntityEffects + TimeEffects"

    logger.info(f"Formula: {formula}")

    if PanelOLS is None:
        logger.error("linearmodels not installed. Run: pip install linearmodels")
        return

    mod = PanelOLS.from_formula(
        formula,
        data=df,
        drop_absorbed=True,
    )

    res = mod.fit(cov_type="clustered", cluster_entity=True)

    logger.info("\n\n" + "=" * 60)
    logger.info("Baseline Model: ln(Hours) ~ ln(Robots)_{t-1} + controls + FE")
    logger.info("=" * 60)
    print(res)

    # Save results
    OUTPUT_PATH.mkdir(exist_ok=True)
    with open(OUTPUT_PATH / "equation1_baseline_regression.txt", "w") as f:
        f.write(str(res))

    logger.info(f"\nResults saved to {OUTPUT_PATH / 'equation1_baseline_regression.txt'}")

    # Brief summary
    beta_robots = res.params.get("ln_robots_lag1", np.nan)
    se_robots = res.std_errors.get("ln_robots_lag1", np.nan)
    logger.info(f"\nβ₁ (ln_robots_lag1): {beta_robots:.4f} (SE: {se_robots:.4f})")
    logger.info("Interpretation: 1% increase in robots/1000 workers → "
                f"{100*beta_robots:.2f}% change in labour input (hours proxy)")

    # --- Sanity checks ---
    _log_sanity_checks(df, res)


def _log_sanity_checks(df: pd.DataFrame, res) -> None:
    """Log structured sanity checks for the baseline model."""
    BAR = "═" * 54
    SEP = "─" * 54

    logger.info(f"\n{BAR}\n  Sanity Checks\n{SEP}")

    # 1. Within-entity variation (use index level to avoid entity-as-column ambiguity)
    grp = df.groupby(level="entity")
    ln_robots_std = grp["ln_robots_lag1"].std()
    ln_hours_std = grp["ln_hours"].std()

    logger.info("  1. Within-entity variation (std)")
    logger.info(f"     ln_robots_lag1: mean={ln_robots_std.mean():.4f}, min={ln_robots_std.min():.4f}, max={ln_robots_std.max():.4f}")
    logger.info(f"     ln_hours:       mean={ln_hours_std.mean():.4f}, min={ln_hours_std.min():.4f}, max={ln_hours_std.max():.4f}")

    low_var = (ln_robots_std < 0.01).sum()
    if low_var > 0:
        logger.warning(f"     ⚠ {low_var} entities have ln_robots_lag1 std < 0.01 (FE may absorb variation)")
    else:
        logger.info(f"     ✓ All entities have sufficient within variation in ln_robots_lag1")

    # 2. Industry-level correlations
    def _corr(g):
        c = g[["ln_robots_lag1", "ln_hours"]].corr().iloc[0, 1]
        return c if not np.isnan(c) else None

    industry_corr = df.groupby("nace_r2_code", group_keys=False).apply(_corr, include_groups=False).dropna()
    logger.info(f"\n  2. Industry-level correlation (ln_robots_lag1, ln_hours)")
    logger.info(f"     mean={industry_corr.mean():.4f}, min={industry_corr.min():.4f}, max={industry_corr.max():.4f}")
    neg = industry_corr.nsmallest(3)
    pos = industry_corr.nlargest(3)
    logger.info(f"     most negative: {', '.join(f'{k}={v:.3f}' for k, v in neg.items())}")
    logger.info(f"     most positive: {', '.join(f'{k}={v:.3f}' for k, v in pos.items())}")

    # 3. Variance decomposition (Pooled vs Within R²)
    mod_pooled = PanelOLS.from_formula(
        "ln_hours ~ ln_robots_lag1 + ln_va + ln_cap",
        data=df,
    ).fit(cov_type="clustered", cluster_entity=True)

    within_r2 = getattr(res, "rsquared_within", res.rsquared)
    logger.info(f"\n  3. R² decomposition")
    logger.info(f"     Pooled (no FE): {mod_pooled.rsquared:.4f}")
    logger.info(f"     Within:         {within_r2:.4f}")
    logger.info(f"     Overall:        {res.rsquared:.4f}")
    logger.info(f"\n{BAR}\n")


if __name__ == "__main__":
    main()

