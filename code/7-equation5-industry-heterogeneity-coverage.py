'''
Equation 5: Industry-by-Industry Coverage Moderation

For EACH industry separately:
  ln(Hours) = β₁ ln(Robots) + β₂[ln(Robots)×AdjCov_c] + controls + FE

Runs separate regressions per NACE industry to reveal heterogeneity in how
bargaining coverage moderates the robot–hours relationship across industries.

Note: Sample drops to ~73% of baseline due to missing coverage data for ~6 countries.

Usage (run from project root):
  python code/7-equation5-industry-heterogeneity-coverage.py 1   # diagnostics
  python code/7-equation5-industry-heterogeneity-coverage.py 2   # diagnostics + model
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

STEPS = {1: "diagnostics", 2: "model"}

MIN_COUNTRIES = 5
MIN_OBS = 50


def step_diagnostics(df: pd.DataFrame) -> None:
    log_diagnostics(df)
    if "nace_r2_code" in df.columns:
        industries = sorted(df["nace_r2_code"].dropna().unique())
        logger.info(f"  Industries available: {len(industries)}")
        for ind in industries:
            n = len(df[df["nace_r2_code"] == ind])
            n_cov = df[(df["nace_r2_code"] == ind) & df["adjcov"].notna()].shape[0] if "adjcov" in df.columns else 0
            logger.info(f"    {ind}: {n} rows (raw), {n_cov} with coverage data")
        logger.info("")


def step_model(df_raw: pd.DataFrame) -> None:
    controls = get_controls(df_raw)
    controls_str = " + ".join(controls)

    req = ["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap", "adjcov", "nace_r2_code"]
    df = prepare_panel(df_raw, require=req)
    for c in controls:
        if c in df.columns:
            df = df.dropna(subset=[c])
    df = df.drop_duplicates(subset=["entity", "year_int"]).copy()

    if "adjcov_centered" not in df.columns:
        logger.warning("adjcov_centered missing; computing from adjcov. Re-run 2-cleaning-data.py.")
        df["adjcov_centered"] = df["adjcov"] - df["adjcov"].mean()
    df = df[df["adjcov_centered"].notna()].copy()

    industries = sorted(df["nace_r2_code"].unique())
    logger.info(f"\n{BAR}")
    logger.info(f"  Running industry-by-industry coverage moderation...")
    logger.info(f"  Industries to test: {len(industries)}")
    logger.info(SEP)

    results = []
    skipped = []
    failed = []

    for ind in industries:
        df_ind = df[df["nace_r2_code"] == ind].copy()
        n_obs = len(df_ind)
        n_countries = df_ind["country_code"].nunique() if "country_code" in df_ind.columns else df_ind.index.get_level_values("entity").nunique()

        if n_countries < MIN_COUNTRIES:
            msg = f"  Skipping {ind}: only {n_countries} countries"
            logger.warning(msg)
            skipped.append({"industry": ind, "reason": f"only {n_countries} countries", "n_obs": n_obs})
            continue

        if n_obs < MIN_OBS:
            msg = f"  Skipping {ind}: only {n_obs} observations"
            logger.warning(msg)
            skipped.append({"industry": ind, "reason": f"only {n_obs} obs", "n_obs": n_obs})
            continue

        if df_ind["adjcov_centered"].std() < 1e-10:
            msg = f"  Skipping {ind}: no variation in adjcov_centered"
            logger.warning(msg)
            skipped.append({"industry": ind, "reason": "no variation in moderator", "n_obs": n_obs})
            continue

        df_ind["ln_robots_adjcov"] = df_ind["ln_robots_lag1"] * df_ind["adjcov_centered"]

        formula = (
            f"ln_hours ~ ln_robots_lag1 + ln_robots_adjcov"
            f" + {controls_str} + EntityEffects + TimeEffects"
        )

        try:
            res = run_panelols(formula, df_ind)
        except Exception as e:
            msg = f"  {ind}: {str(e)}"
            logger.error(msg)
            failed.append({"industry": ind, "reason": str(e), "n_obs": n_obs})
            continue

        beta_robot = res.params.get("ln_robots_lag1", np.nan)
        beta_interaction = res.params.get("ln_robots_adjcov", np.nan)
        se_interaction = res.std_errors.get("ln_robots_adjcov", np.nan)
        pval_interaction = res.pvalues.get("ln_robots_adjcov", np.nan)

        ci_lower = beta_interaction - 1.96 * se_interaction
        ci_upper = beta_interaction + 1.96 * se_interaction

        significant = pval_interaction < 0.10 if not np.isnan(pval_interaction) else False

        stars = ""
        if not np.isnan(pval_interaction):
            if pval_interaction < 0.01:
                stars = "***"
            elif pval_interaction < 0.05:
                stars = "**"
            elif pval_interaction < 0.10:
                stars = "*"

        sign = "+" if beta_interaction >= 0 else ""
        logger.info(
            f"  {ind}: beta_cov={sign}{beta_interaction:.4f} (p={pval_interaction:.3f}){stars}, "
            f"N={n_obs}, countries={n_countries}"
        )

        results.append({
            "industry": ind,
            "n_obs": int(res.nobs),
            "n_countries": n_countries,
            "beta_robot_baseline": beta_robot,
            "beta_coverage": beta_interaction,
            "se_coverage": se_interaction,
            "pval_coverage": pval_interaction,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "significant": significant,
        })

    logger.info(SEP)

    n_completed = len(results)
    n_total = len(industries)
    n_positive = sum(1 for r in results if r["beta_coverage"] >= 0)
    n_negative = sum(1 for r in results if r["beta_coverage"] < 0)
    n_sig = sum(1 for r in results if r["significant"])

    logger.info(f"  Completed: {n_completed}/{n_total} industries")
    logger.info(f"    Positive coverage effects: {n_positive}")
    logger.info(f"    Negative coverage effects: {n_negative}")
    logger.info(f"    Significant (p<0.10): {n_sig}")
    if skipped:
        logger.info(f"    Skipped: {len(skipped)}")
    if failed:
        logger.info(f"    Failed: {len(failed)}")
    logger.info(BAR)

    OUTPUT_PATH.mkdir(exist_ok=True)

    if results:
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values("pval_coverage")
        csv_path = OUTPUT_PATH / "industry_by_industry_coverage.csv"
        results_df.to_csv(csv_path, index=False)
        logger.info(f"\n  Results CSV saved: {csv_path}")

        txt_path = OUTPUT_PATH / "equation5_industry_coverage_summary.txt"
        with open(txt_path, "w") as f:
            f.write("Equation 5: Industry-by-Industry Coverage Moderation\n")
            f.write("=" * 80 + "\n")
            f.write(f"Model: ln_hours ~ ln_robots_lag1 + ln_robots_lag1*adjcov_centered + controls + FE\n")
            f.write(f"Each row = separate regression for one NACE industry\n")
            f.write(f"beta_coverage = change in robot effect per 1pp increase in bargaining coverage\n")
            f.write("-" * 80 + "\n\n")
            f.write(f"{'Industry':<12} {'N_obs':>6} {'N_ctry':>6} {'beta_cov':>12} "
                    f"{'SE':>10} {'p-value':>10} {'95% CI':>24} {'Sig':>5}\n")
            f.write("-" * 90 + "\n")
            for _, row in results_df.iterrows():
                sig_mark = "*" if row["significant"] else ""
                f.write(
                    f"{row['industry']:<12} {row['n_obs']:>6} {row['n_countries']:>6} "
                    f"{row['beta_coverage']:>12.4f} {row['se_coverage']:>10.4f} "
                    f"{row['pval_coverage']:>10.4f} "
                    f"[{row['ci_lower']:>10.4f}, {row['ci_upper']:>10.4f}] "
                    f"{sig_mark:>5}\n"
                )
            f.write("-" * 90 + "\n\n")
            f.write(f"Summary:\n")
            f.write(f"  Industries estimated: {n_completed}/{n_total}\n")
            f.write(f"  Positive coverage effects: {n_positive}\n")
            f.write(f"  Negative coverage effects: {n_negative}\n")
            f.write(f"  Significant at 10%: {n_sig}\n")
            if skipped:
                f.write(f"\nSkipped industries:\n")
                for s in skipped:
                    f.write(f"  {s['industry']}: {s['reason']} (N={s['n_obs']})\n")
            if failed:
                f.write(f"\nFailed industries:\n")
                for fl in failed:
                    f.write(f"  {fl['industry']}: {fl['reason']} (N={fl['n_obs']})\n")
        logger.info(f"  Summary TXT saved: {txt_path}")

        logger.info(f"\n  Top significant results:")
        sig_df = results_df[results_df["significant"]]
        if len(sig_df) > 0:
            for _, row in sig_df.head(10).iterrows():
                sign = "+" if row["beta_coverage"] >= 0 else ""
                logger.info(
                    f"    {row['industry']}: {sign}{row['beta_coverage']:.4f} "
                    f"(p={row['pval_coverage']:.3f})"
                )
        else:
            logger.info("    (none at p<0.10)")
    else:
        logger.warning("  No industries produced valid results.")

    logger.info("")


def main():
    step = get_step(1)
    logger.info(f"Step {step}: {STEPS.get(step, '?')}")

    df = pd.read_csv(CLEANED_PATH)

    if step == 1:
        step_diagnostics(df)
        return

    if step == 2:
        step_diagnostics(df)
        step_model(df)
        return

    logger.error(f"Unknown step {step}. Use 1 or 2.")
    sys.exit(1)


if __name__ == "__main__":
    main()
