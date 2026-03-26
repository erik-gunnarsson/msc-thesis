'''
ROBUSTNESS / LEGACY — KLEMS overlap specification.

KLEMS pooled bucket-moderation runner.

Thesis mapping: main bucket heterogeneity model (Equation 4 family).

Pooled model with bucket-specific robot effects and bucket-specific institutional
moderation, estimated in a single regression:

  ln(LI)_ijt = β₁ ln(Robots)_{t-1}
             + Σ_b β₂b [ln(Robots)_{t-1} × Bucket_b]
             + β₃ [ln(Robots)_{t-1} × M_c]
             + Σ_b β₄b [ln(Robots)_{t-1} × M_c × Bucket_b]
             + controls + α_ij + δ_t + ε_ijt

where LI = labour input proxy and M_c ∈ {coord_pre_c, adjcov_pre_c, ud_pre_c}.
Bucket 5 (low-tech/traditional) is the reference category.
Coord is continuous by default; binary (Coord ≥ 4) via --coord-mode binary.

Post-estimation:
  Console  – Planned contrasts only (PLANNED_CONTRASTS)
  CSV      – Full pairwise Wald contrasts (appendix)
  CSV      – Marginal effects by bucket

CLI flags:
  --moderator coord|adjcov|ud|...   (default: coord)
  --sample full|common              (default: full)
  --coord-mode continuous|binary    (default: continuous)
  --se clustered|driscoll-kraay     (default: clustered)
  --trends none|bucket              (default: none)

Usage:
  python code/07_klems_bucket_moderation.py 2 --moderator coord --sample common
  python code/07_klems_bucket_moderation.py 2 --moderator adjcov --sample common
  python code/07_klems_bucket_moderation.py 2 --moderator ud --sample full
'''

import sys

import pandas as pd
import numpy as np
from loguru import logger

from _klems_utils import (
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
    build_pairwise_contrasts,
    parse_args,
    moderator_to_columns,
    get_moderator,
    moderator_role_summary,
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

    mod_info = get_moderator(args.moderator)
    mod_var, has_var, is_binary = moderator_to_columns(args.moderator, args.coord_mode)
    logger.info(f"Moderator: {args.moderator} → {mod_var} (binary={is_binary})")
    logger.info(f"Moderator role: {moderator_role_summary(args.moderator)}")

    df = apply_sample_filter(df_raw.copy(), args.sample)
    req = ["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap", mod_var, "bucket"]
    df = prepare_panel(df, require=req)
    for c in controls:
        if c in df.columns:
            df = df.dropna(subset=[c])
    df = df.drop_duplicates(subset=["entity", "year_int"]).copy()

    if has_var in df.columns:
        df = df[df[has_var]].copy()

    bucket_cols = get_bucket_dummies(df)

    # Build interaction columns
    for col in bucket_cols:
        df[f"lr_{col}"] = df["ln_robots_lag1"] * df[col]
        df[f"lr_mod_{col}"] = df["ln_robots_lag1"] * df[mod_var] * df[col]

    lr_bucket_terms = [f"lr_{c}" for c in bucket_cols]
    lr_mod_bucket_terms = [f"lr_mod_{c}" for c in bucket_cols]

    formula_parts = (
        ["ln_hours ~ ln_robots_lag1"]
        + lr_bucket_terms
        + [f"ln_robots_lag1:{mod_var}"]
        + lr_mod_bucket_terms
        + [controls_str]
        + ["EntityEffects + TimeEffects"]
    )
    formula = " + ".join(formula_parts)
    formula = add_trend_terms(df, formula, args.trends)

    logger.info(f"\n{BAR}")
    logger.info(
        f"  Equation 4: Bucket heterogeneity – {args.moderator} ({args.sample} sample)"
        f" [{mod_info['role_label']}]"
    )
    logger.info(f"  Theory note: {mod_info['theory_note']}")
    logger.info(SEP)
    logger.info(f"  Formula: {formula}")
    logger.info(f"  Reference bucket: {REF_BUCKET} ({BUCKET_NAMES[REF_BUCKET]})")
    logger.info(f"  N obs: {len(df)}, N entities: {df['entity'].nunique()}")

    res = run_panelols(formula, df, cov_type=args.se)
    print(res)

    OUTPUT_PATH.mkdir(exist_ok=True)
    with open(OUTPUT_PATH / f"equation4_bucket_{args.moderator}_{args.sample}sample_regression.txt", "w") as f:
        header = format_sample_header(df)
        header += f"Institutional role: {mod_info['role_label']}\n"
        header += f"Theory note: {mod_info['theory_note']}\n"
        header += f"Sample note: {mod_info['sample_caveat']}\n{SEP}\n"
        f.write(header + str(res))

    tag = f"eq4_{args.moderator}_{args.sample}"
    write_sample_manifest(df, tag, sample_mode=args.sample)
    write_run_metadata(
        "07_klems_bucket_moderation.py",
        {"moderator": args.moderator, "sample": args.sample,
         "coord_mode": args.coord_mode, "se": args.se, "trends": args.trends},
        n_obs=res.nobs, n_entities=df["entity"].nunique(),
    )

    interaction_param = f"ln_robots_lag1:{mod_var}"

    # --- Table 1: Marginal effects ---
    param_names = list(res.params.index)
    beta = res.params
    V = np.array(res.cov)

    if is_binary:
        marg_df = _marginal_effects_binary(
            res, param_names, beta, V, mod_var, interaction_param,
        )
    else:
        mod_sd = df[mod_var].std()
        marg_df = _marginal_effects_continuous(
            res, param_names, beta, V, mod_var, interaction_param, mod_sd,
        )

    marg_df.to_csv(OUTPUT_PATH / f"equation4_bucket_{args.moderator}_{args.sample}sample_marginal_effects.csv", index=False)

    # --- Table 2: Pairwise contrasts ---
    contrasts_df = _pairwise_contrasts(res, param_names, beta, V, mod_var, interaction_param, is_binary)

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

    contrasts_df.to_csv(OUTPUT_PATH / f"equation4_bucket_{args.moderator}_{args.sample}sample_appendix_contrasts.csv", index=False)

    # --- Summary .txt (planned contrasts only) ---
    _write_summary(marg_df, contrasts_df, res, args, df)

    logger.info(f"\n  Outputs saved to {OUTPUT_PATH}/equation4_bucket_{args.moderator}_*")
    logger.info(BAR)


def _marginal_effects_binary(res, param_names, beta, V, mod_var, interaction_param):
    """Marginal effects for binary moderator (low=0 / high=1)."""
    rows = []
    for b in ALL_BUCKETS:
        effect_low = beta.get("ln_robots_lag1", 0.0)
        if b != REF_BUCKET:
            effect_low += beta.get(f"lr_bucket_{b}", 0.0)

        effect_high = effect_low + beta.get(interaction_param, 0.0)
        if b != REF_BUCKET:
            effect_high += beta.get(f"lr_mod_bucket_{b}", 0.0)

        moderation = beta.get(interaction_param, 0.0)
        if b != REF_BUCKET:
            moderation += beta.get(f"lr_mod_bucket_{b}", 0.0)

        se_low = _se_linear_combo(param_names, V, _build_R_low(param_names, b))
        R_mod = _build_R_mod(param_names, b, interaction_param)
        se_mod = _se_linear_combo(param_names, V, R_mod)
        R_high = _build_R_low(param_names, b) + R_mod
        se_high = _se_linear_combo(param_names, V, R_high)

        rows.append({
            "bucket": b, "bucket_name": BUCKET_NAMES[b],
            "effect_low": effect_low, "se_low": se_low,
            "effect_high": effect_high, "se_high": se_high,
            "moderation": moderation, "se_moderation": se_mod,
        })

    marg_df = pd.DataFrame(rows)
    logger.info(f"\n  Marginal effects by bucket:")
    logger.info(f"  {'Bucket':<25} {'Low':>10} {'High':>10} {'Δ':>10}")
    logger.info(f"  {'-'*60}")
    for _, r in marg_df.iterrows():
        logger.info(
            f"  {r['bucket']:.0f} {r['bucket_name']:<22} "
            f"{r['effect_low']:>10.4f} {r['effect_high']:>10.4f} {r['moderation']:>10.4f}"
        )
    return marg_df


def _marginal_effects_continuous(res, param_names, beta, V, mod_var, interaction_param, mod_sd):
    """Marginal effects for continuous moderator at mean, ±1SD."""
    eval_points = {"mean": 0.0, "mean-1SD": -mod_sd, "mean+1SD": mod_sd}
    rows = []
    for eval_label, val in eval_points.items():
        for b in ALL_BUCKETS:
            R = np.zeros(len(param_names))
            if "ln_robots_lag1" in param_names:
                R[param_names.index("ln_robots_lag1")] = 1.0
            if b != REF_BUCKET and f"lr_bucket_{b}" in param_names:
                R[param_names.index(f"lr_bucket_{b}")] = 1.0
            if interaction_param in param_names:
                R[param_names.index(interaction_param)] = val
            if b != REF_BUCKET and f"lr_mod_bucket_{b}" in param_names:
                R[param_names.index(f"lr_mod_bucket_{b}")] = val

            effect = float(R @ np.array(beta))
            se = np.sqrt(float(R @ V @ R))
            rows.append({
                "eval_point": eval_label, "mod_value": val,
                "bucket": b, "bucket_name": BUCKET_NAMES[b],
                "effect": effect, "se": se,
            })

    marg_df = pd.DataFrame(rows)
    for label in eval_points:
        sub = marg_df[marg_df["eval_point"] == label]
        logger.info(f"\n  Robot effect at {label}:")
        for _, r in sub.iterrows():
            logger.info(f"    B{r['bucket']:.0f} ({r['bucket_name']}): {r['effect']:.4f} (SE={r['se']:.4f})")
    return marg_df


def _build_R_low(param_names, b):
    R = np.zeros(len(param_names))
    if "ln_robots_lag1" in param_names:
        R[param_names.index("ln_robots_lag1")] = 1.0
    if b != REF_BUCKET and f"lr_bucket_{b}" in param_names:
        R[param_names.index(f"lr_bucket_{b}")] = 1.0
    return R


def _build_R_mod(param_names, b, interaction_param):
    R = np.zeros(len(param_names))
    if interaction_param in param_names:
        R[param_names.index(interaction_param)] = 1.0
    if b != REF_BUCKET and f"lr_mod_bucket_{b}" in param_names:
        R[param_names.index(f"lr_mod_bucket_{b}")] = 1.0
    return R


def _se_linear_combo(param_names, V, R):
    return np.sqrt(float(R @ V @ R))


def _pairwise_contrasts(res, param_names, beta, V, mod_var, interaction_param, is_binary):
    """All pairwise contrasts for robot effects and moderation."""
    results = []

    # Robot effect (at low/mean moderator): bucket differences
    for i, a in enumerate(ALL_BUCKETS):
        for b_cmp in ALL_BUCKETS[i + 1:]:
            R = np.zeros(len(param_names))
            if a != REF_BUCKET and f"lr_bucket_{a}" in param_names:
                R[param_names.index(f"lr_bucket_{a}")] = 1.0
            if b_cmp != REF_BUCKET and f"lr_bucket_{b_cmp}" in param_names:
                R[param_names.index(f"lr_bucket_{b_cmp}")] = -1.0
            result = test_linear_contrast(res, R, label=f"Robot base: B{a} vs B{b_cmp}")
            result.update({"type": "robot_base", "bucket_a": a, "bucket_b": b_cmp})
            results.append(result)

    # Moderation effect: bucket differences
    for i, a in enumerate(ALL_BUCKETS):
        for b_cmp in ALL_BUCKETS[i + 1:]:
            R = np.zeros(len(param_names))
            if a != REF_BUCKET and f"lr_mod_bucket_{a}" in param_names:
                R[param_names.index(f"lr_mod_bucket_{a}")] = 1.0
            if b_cmp != REF_BUCKET and f"lr_mod_bucket_{b_cmp}" in param_names:
                R[param_names.index(f"lr_mod_bucket_{b_cmp}")] = -1.0
            result = test_linear_contrast(res, R, label=f"Moderation: B{a} vs B{b_cmp}")
            result.update({"type": "moderation_diff", "bucket_a": a, "bucket_b": b_cmp})
            results.append(result)

    contrasts_df = pd.DataFrame(results)

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

    return contrasts_df


def _write_summary(marg_df, contrasts_df, res, args, df):
    """Write summary .txt with planned contrasts only."""
    countries = sorted(df["country_code"].unique()) if "country_code" in df.columns else []
    lines = [
        f"Equation 4: Bucket Heterogeneity – {args.moderator} ({args.sample} sample)",
        "=" * 70,
        f"N obs = {res.nobs:.0f}",
        f"Countries ({len(countries)}): {', '.join(countries)}",
        f"Reference bucket: {REF_BUCKET} ({BUCKET_NAMES[REF_BUCKET]})",
        f"Moderator: {args.moderator} (coord_mode={args.coord_mode})",
        f"SE: {args.se}",
        "",
        "Marginal effects",
        "-" * 70,
    ]
    for _, r in marg_df.iterrows():
        cols = [c for c in r.index if c not in ("bucket", "bucket_name", "eval_point", "mod_value")]
        vals = ", ".join(f"{c}={r[c]:.4f}" for c in cols)
        lines.append(f"  B{r['bucket']:.0f} ({r['bucket_name']}): {vals}")

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

    path = OUTPUT_PATH / f"equation4_bucket_{args.moderator}_{args.sample}sample_summary.txt"
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

        if is_binary and df_b[mod_var].nunique() < 2:
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
        rob_df.to_csv(OUTPUT_PATH / f"equation4_robustness_per_bucket_{args.moderator}.csv", index=False)
        logger.info(f"\n  Robustness results saved.")

    logger.info(BAR)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args(default_moderator="coord")
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
