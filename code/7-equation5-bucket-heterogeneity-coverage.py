'''
Equation 5: Bucket Heterogeneity with Institutional Moderation (continuous)

Pooled model with bucket-specific robot effects and bucket-specific institutional
moderation (continuous moderator), estimated in a single regression:

  ln(LI)_ijt = β₁ ln(Robots)_{t-1}
             + Σ_b β₂b [ln(Robots)_{t-1} × Bucket_b]
             + β₃ [ln(Robots)_{t-1} × M_c]
             + Σ_b β₄b [ln(Robots)_{t-1} × M_c × Bucket_b]
             + controls + α_ij + δ_t + ε_ijt

where LI = labour input proxy and M_c is a centered predetermined moderator.
Defaults to adjcov_pre_c.  Bucket 5 (low-tech/traditional) is reference.

Post-estimation:
  Console  – Planned contrasts only (PLANNED_CONTRASTS)
  CSV      – Full pairwise Wald contrasts (appendix)
  CSV      – Marginal effects at mean, mean±1SD

CLI flags:
  --moderator coord|adjcov|ud|...   (default: adjcov)
  --sample full|common              (default: full)
  --se clustered|driscoll-kraay     (default: clustered)
  --trends none|bucket              (default: none)

Usage:
  python code/7-equation5-bucket-heterogeneity-coverage.py 2 --moderator adjcov --sample common
'''

import sys

import pandas as pd
import numpy as np
from loguru import logger

from _equation_utils import (
    CLEANED_PATH,
    OUTPUT_PATH,
    BUCKET_NAMES,
    REF_BUCKET,
    PLANNED_CONTRASTS,
    BAR,
    SEP,
    format_sample_header,
    get_controls,
    get_bucket_dummies,
    prepare_panel,
    run_panelols,
    run_diagnostics_bucket,
    test_linear_contrast,
    parse_args,
    moderator_to_columns,
    apply_sample_filter,
    add_trend_terms,
    write_sample_manifest,
    write_run_metadata,
)

STEPS = {1: "diagnostics", 2: "model", 3: "robustness"}
ALL_BUCKETS = sorted(BUCKET_NAMES.keys())
NON_REF_BUCKETS = [b for b in ALL_BUCKETS if b != REF_BUCKET]


# ---------------------------------------------------------------------------
# Step 1: diagnostics
# ---------------------------------------------------------------------------

def step_diagnostics(df: pd.DataFrame) -> None:
    run_diagnostics_bucket(df)


# ---------------------------------------------------------------------------
# Step 2: main model
# ---------------------------------------------------------------------------

def step_model(df_raw: pd.DataFrame, args) -> None:
    controls = get_controls(df_raw)
    controls_str = " + ".join(controls)

    mod_var, has_var, is_binary = moderator_to_columns(args.moderator, args.coord_mode)
    if is_binary:
        logger.warning(f"Eq5 expects a continuous moderator but {args.moderator} is binary. Proceeding anyway.")

    logger.info(f"Moderator: {args.moderator} → {mod_var}")

    df = apply_sample_filter(df_raw.copy(), args.sample)
    req = ["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap", mod_var, "bucket"]
    df = prepare_panel(df, require=req)
    for c in controls:
        if c in df.columns:
            df = df.dropna(subset=[c])
    df = df.drop_duplicates(subset=["entity", "year_int"]).copy()

    if has_var in df.columns:
        df = df[df[has_var]].copy()

    mod_sd = df[mod_var].std()
    if mod_sd < 5:
        logger.warning(f"  {mod_var} SD = {mod_sd:.2f} — limited leverage for interactions")

    bucket_cols = get_bucket_dummies(df)

    # Build interaction columns
    df["lr_mod"] = df["ln_robots_lag1"] * df[mod_var]
    for col in bucket_cols:
        df[f"lr_{col}"] = df["ln_robots_lag1"] * df[col]
        df[f"lr_mod_{col}"] = df["ln_robots_lag1"] * df[mod_var] * df[col]

    lr_bucket_terms = [f"lr_{c}" for c in bucket_cols]
    lr_mod_bucket_terms = [f"lr_mod_{c}" for c in bucket_cols]

    formula_parts = (
        ["ln_hours ~ ln_robots_lag1"]
        + lr_bucket_terms
        + ["lr_mod"]
        + lr_mod_bucket_terms
        + [controls_str]
        + ["EntityEffects + TimeEffects"]
    )
    formula = " + ".join(formula_parts)
    formula = add_trend_terms(df, formula, args.trends)

    logger.info(f"\n{BAR}")
    logger.info(f"  Equation 5: Bucket heterogeneity – {args.moderator} ({args.sample} sample)")
    logger.info(SEP)
    logger.info(f"  Formula: {formula}")
    logger.info(f"  Reference bucket: {REF_BUCKET} ({BUCKET_NAMES[REF_BUCKET]})")
    logger.info(f"  N obs: {len(df)}, N entities: {df['entity'].nunique()}")
    logger.info(f"  {mod_var} SD: {mod_sd:.2f}")

    res = run_panelols(formula, df, cov_type=args.se)
    print(res)

    OUTPUT_PATH.mkdir(exist_ok=True)
    with open(OUTPUT_PATH / f"equation5_bucket_{args.moderator}_{args.sample}sample_regression.txt", "w") as f:
        f.write(format_sample_header(df) + str(res))

    tag = f"eq5_{args.moderator}_{args.sample}"
    write_sample_manifest(df, tag, sample_mode=args.sample)
    write_run_metadata(
        "7-equation5-bucket-heterogeneity-coverage.py",
        {"moderator": args.moderator, "sample": args.sample,
         "se": args.se, "trends": args.trends},
        n_obs=res.nobs, n_entities=df["entity"].nunique(),
    )

    # --- Table 1: Marginal effects at mean, mean±1SD ---
    param_names = list(res.params.index)
    beta = res.params
    V = np.array(res.cov)

    eval_points = {"mean": 0.0, "mean-1SD": -mod_sd, "mean+1SD": mod_sd}
    marginal_rows = []

    for eval_label, val in eval_points.items():
        for b in ALL_BUCKETS:
            R = np.zeros(len(param_names))
            if "ln_robots_lag1" in param_names:
                R[param_names.index("ln_robots_lag1")] = 1.0
            if b != REF_BUCKET and f"lr_bucket_{b}" in param_names:
                R[param_names.index(f"lr_bucket_{b}")] = 1.0
            if "lr_mod" in param_names:
                R[param_names.index("lr_mod")] = val
            if b != REF_BUCKET and f"lr_mod_bucket_{b}" in param_names:
                R[param_names.index(f"lr_mod_bucket_{b}")] = val

            effect = float(R @ np.array(beta))
            se = np.sqrt(float(R @ V @ R))
            marginal_rows.append({
                "eval_point": eval_label, "mod_value": val,
                "bucket": b, "bucket_name": BUCKET_NAMES[b],
                "effect": effect, "se": se,
                "ci_lower": effect - 1.96 * se,
                "ci_upper": effect + 1.96 * se,
            })

    marg_df = pd.DataFrame(marginal_rows)
    marg_df.to_csv(OUTPUT_PATH / f"equation5_bucket_{args.moderator}_{args.sample}sample_marginal_effects.csv", index=False)

    logger.info(f"\n  Marginal effects by bucket:")
    for eval_label in eval_points:
        sub = marg_df[marg_df["eval_point"] == eval_label]
        logger.info(f"\n  At {eval_label}:")
        logger.info(f"  {'Bucket':<25} {'Effect':>10} {'SE':>10} {'95% CI':>24}")
        logger.info(f"  {'-'*70}")
        for _, r in sub.iterrows():
            logger.info(
                f"  {r['bucket']:.0f} {r['bucket_name']:<22} "
                f"{r['effect']:>10.4f} {r['se']:>10.4f} "
                f"[{r['ci_lower']:>8.4f}, {r['ci_upper']:>8.4f}]"
            )

    # --- Moderation slope per bucket ---
    logger.info(f"\n  Moderation slope (∂robot_effect/∂{args.moderator}) by bucket:")
    for b in ALL_BUCKETS:
        R_mod = np.zeros(len(param_names))
        if "lr_mod" in param_names:
            R_mod[param_names.index("lr_mod")] = 1.0
        if b != REF_BUCKET and f"lr_mod_bucket_{b}" in param_names:
            R_mod[param_names.index(f"lr_mod_bucket_{b}")] = 1.0
        mod_eff = float(R_mod @ np.array(beta))
        mod_se = np.sqrt(float(R_mod @ V @ R_mod))
        logger.info(f"  B{b} ({BUCKET_NAMES[b]}): {mod_eff:.4f} (SE={mod_se:.4f})")

    # --- Table 2: Pairwise contrasts ---
    contrast_results = []

    # Robot effect at mean: compare buckets
    for i, a in enumerate(ALL_BUCKETS):
        for b_cmp in ALL_BUCKETS[i + 1:]:
            R = np.zeros(len(param_names))
            if a != REF_BUCKET and f"lr_bucket_{a}" in param_names:
                R[param_names.index(f"lr_bucket_{a}")] = 1.0
            if b_cmp != REF_BUCKET and f"lr_bucket_{b_cmp}" in param_names:
                R[param_names.index(f"lr_bucket_{b_cmp}")] = -1.0
            result = test_linear_contrast(res, R, label=f"Robot (mean): B{a} vs B{b_cmp}")
            result.update({"type": "robot_mean", "bucket_a": a, "bucket_b": b_cmp})
            contrast_results.append(result)

    # Moderation slope: compare buckets
    for i, a in enumerate(ALL_BUCKETS):
        for b_cmp in ALL_BUCKETS[i + 1:]:
            R = np.zeros(len(param_names))
            if a != REF_BUCKET and f"lr_mod_bucket_{a}" in param_names:
                R[param_names.index(f"lr_mod_bucket_{a}")] = 1.0
            if b_cmp != REF_BUCKET and f"lr_mod_bucket_{b_cmp}" in param_names:
                R[param_names.index(f"lr_mod_bucket_{b_cmp}")] = -1.0
            result = test_linear_contrast(res, R, label=f"Moderation: B{a} vs B{b_cmp}")
            result.update({"type": "moderation_diff", "bucket_a": a, "bucket_b": b_cmp})
            contrast_results.append(result)

    contrasts_df = pd.DataFrame(contrast_results)

    # Add adjusted p-values (Holm)
    try:
        from statsmodels.stats.multitest import multipletests
        for ctype in contrasts_df["type"].unique():
            mask = contrasts_df["type"] == ctype
            pvals = contrasts_df.loc[mask, "pval"].values
            if len(pvals) > 1 and not np.all(np.isnan(pvals)):
                _, pvals_holm, _, _ = multipletests(np.nan_to_num(pvals, nan=1.0), method="holm")
                contrasts_df.loc[mask, "pval_holm"] = pvals_holm
    except ImportError:
        pass

    contrasts_df.to_csv(OUTPUT_PATH / f"equation5_bucket_{args.moderator}_{args.sample}sample_appendix_contrasts.csv", index=False)

    planned_set = set(PLANNED_CONTRASTS)
    for ctype in contrasts_df["type"].unique():
        sub = contrasts_df[contrasts_df["type"] == ctype]
        planned = sub[sub.apply(lambda r: (int(r["bucket_a"]), int(r["bucket_b"])) in planned_set, axis=1)]
        if planned.empty:
            continue
        logger.info(f"\n  Planned contrasts – {ctype}:")
        for _, r in planned.iterrows():
            sig = "*" if r["pval"] < 0.10 else ""
            logger.info(f"    B{r['bucket_a']} vs B{r['bucket_b']}: chi2={r['stat']:.3f}, p={r['pval']:.3f} {sig}")

    # --- Summary .txt (planned contrasts only) ---
    _write_summary(marg_df, contrasts_df, res, args, df, mod_sd)

    logger.info(f"\n  Outputs saved to {OUTPUT_PATH}/equation5_bucket_{args.moderator}_*")
    logger.info(BAR)


def _write_summary(marg_df, contrasts_df, res, args, df, mod_sd):
    """Write summary .txt with planned contrasts only."""
    countries = sorted(df["country_code"].unique()) if "country_code" in df.columns else []
    lines = [
        f"Equation 5: Bucket Heterogeneity – {args.moderator} ({args.sample} sample)",
        "=" * 70,
        f"N obs = {res.nobs:.0f}",
        f"Countries ({len(countries)}): {', '.join(countries)}",
        f"Reference bucket: {REF_BUCKET} ({BUCKET_NAMES[REF_BUCKET]})",
        f"Moderator: {args.moderator}, SD={mod_sd:.2f}",
        f"SE: {args.se}",
        "",
        "Marginal effects (robot slope at different moderator levels)",
        "-" * 70,
    ]
    for eval_pt in marg_df["eval_point"].unique():
        sub = marg_df[marg_df["eval_point"] == eval_pt]
        lines.append(f"\nAt {eval_pt}:")
        lines.append(f"  {'Bucket':<25} {'Effect':>10} {'SE':>10} {'95% CI':>24}")
        lines.append("  " + "-" * 70)
        for _, r in sub.iterrows():
            lines.append(
                f"  {r['bucket']:.0f} {r['bucket_name']:<22} "
                f"{r['effect']:>10.4f} {r['se']:>10.4f} "
                f"[{r['ci_lower']:>8.4f}, {r['ci_upper']:>8.4f}]"
            )

    lines.extend(["", "Planned contrasts (subset)", "-" * 70])
    planned_set = set(PLANNED_CONTRASTS)
    for ctype in contrasts_df["type"].unique():
        sub = contrasts_df[contrasts_df["type"] == ctype]
        planned = sub[sub.apply(lambda r: (int(r["bucket_a"]), int(r["bucket_b"])) in planned_set, axis=1)]
        if planned.empty:
            continue
        lines.append(f"\n  {ctype}:")
        for _, r in planned.iterrows():
            sig = "*" if r["pval"] < 0.10 else ""
            lines.append(f"    B{r['bucket_a']:.0f} vs B{r['bucket_b']:.0f}: chi2={r['stat']:.3f}, p={r['pval']:.3f} {sig}")

    path = OUTPUT_PATH / f"equation5_bucket_{args.moderator}_{args.sample}sample_summary.txt"
    path.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Step 3: robustness (per-bucket separate regressions)
# ---------------------------------------------------------------------------

def step_robustness(df_raw: pd.DataFrame, args) -> None:
    controls = get_controls(df_raw)
    controls_str = " + ".join(controls)

    mod_var, has_var, is_binary = moderator_to_columns(args.moderator, args.coord_mode)

    df = apply_sample_filter(df_raw.copy(), args.sample)
    req = ["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap", mod_var, "bucket"]
    df = prepare_panel(df, require=req)
    for c in controls:
        if c in df.columns:
            df = df.dropna(subset=[c])
    df = df.drop_duplicates(subset=["entity", "year_int"]).copy()

    if has_var in df.columns:
        df = df[df[has_var]].copy()

    logger.info(f"\n{BAR}")
    logger.info(f"  Robustness: Per-bucket separate regressions ({args.moderator})")
    logger.info(SEP)

    results = []
    for b in ALL_BUCKETS:
        df_b = df[df["bucket"] == b].copy()
        n_obs = len(df_b)
        n_ctry = df_b["country_code"].nunique()

        if n_obs < 30 or n_ctry < 3:
            logger.warning(f"  Bucket {b} ({BUCKET_NAMES[b]}): skipped (N={n_obs}, countries={n_ctry})")
            continue

        if not is_binary and df_b[mod_var].std() < 1e-10:
            logger.warning(f"  Bucket {b} ({BUCKET_NAMES[b]}): no variation in {mod_var}")
            continue

        interaction_col = f"lr_mod_rob"
        df_b[interaction_col] = df_b["ln_robots_lag1"] * df_b[mod_var]

        formula = f"ln_hours ~ ln_robots_lag1 + {interaction_col} + {controls_str} + EntityEffects + TimeEffects"
        try:
            res = run_panelols(formula, df_b, cov_type=args.se)
        except Exception as e:
            logger.error(f"  Bucket {b}: {e}")
            continue

        beta_robot = res.params.get("ln_robots_lag1", np.nan)
        beta_inter = res.params.get(interaction_col, np.nan)
        se_inter = res.std_errors.get(interaction_col, np.nan)
        pval_inter = res.pvalues.get(interaction_col, np.nan)

        stars = ""
        if not np.isnan(pval_inter):
            if pval_inter < 0.01: stars = "***"
            elif pval_inter < 0.05: stars = "**"
            elif pval_inter < 0.10: stars = "*"

        logger.info(
            f"  Bucket {b} ({BUCKET_NAMES[b]}): "
            f"β_robot={beta_robot:.4f}, β_interact={beta_inter:.4f} "
            f"(p={pval_inter:.3f}){stars}, N={n_obs}"
        )

        results.append({
            "bucket": b, "bucket_name": BUCKET_NAMES[b],
            "n_obs": int(res.nobs), "n_countries": n_ctry,
            "beta_robot": beta_robot,
            "beta_interaction": beta_inter,
            "se_interaction": se_inter,
            "pval_interaction": pval_inter,
        })

    if results:
        rob_df = pd.DataFrame(results)
        rob_df.to_csv(OUTPUT_PATH / f"equation5_robustness_per_bucket_{args.moderator}.csv", index=False)
        logger.info(f"\n  Robustness results saved.")

    logger.info(BAR)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args(default_moderator="adjcov")
    step = args.step
    logger.info(f"Step {step}: {STEPS.get(step, '?')}")

    df = pd.read_csv(CLEANED_PATH)

    if step >= 1:
        step_diagnostics(df)
    if step >= 2:
        step_model(df, args)
    if step >= 3:
        step_robustness(df, args)


if __name__ == "__main__":
    main()
