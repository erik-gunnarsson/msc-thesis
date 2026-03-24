'''
ICTWSS Moderator Triage (diagnostic only)

Screens candidate ICTWSS institutional variables using:
  Step 1 — Descriptive leverage: dispersion, distinct values, missingness
  Step 2 — Single-interaction screening regressions (full + common sample)
  Step 3 — Diagnostic summary (no moderator selection; mainline set is pre-declared)

Mainline moderators (coord, ud, adjcov) are chosen on theoretical and
data-quality grounds, NOT by t-stat ranking from this triage.
Results are saved for transparency and appendix documentation.

Run after 02_build_klems_panel.py, before committing to moderators in Eq2-Eq5.

Usage:
  python code/03_ictwss_moderator_triage.py
'''

import pandas as pd
import numpy as np
from loguru import logger

from _klems_utils import (
    CLEANED_PATH,
    OUTPUT_PATH,
    MODERATOR_REGISTRY,
    MAINLINE_MODERATORS,
    BAR,
    SEP,
    get_controls,
    prepare_panel,
    run_panelols,
    moderator_diagnostics,
    apply_sample_filter,
)

CANDIDATES = list(MODERATOR_REGISTRY.keys())


def step_descriptive(df: pd.DataFrame) -> pd.DataFrame:
    """Step 1: descriptive leverage for each candidate moderator."""
    logger.info(f"\n{BAR}\n  Step 1: Descriptive leverage\n{SEP}")
    rows = []
    for mod_key in CANDIDATES:
        diag = moderator_diagnostics(df, mod_key)
        diag["is_binary"] = MODERATOR_REGISTRY[mod_key]["is_binary"]
        diag["missing_pct"] = diag.get("pct_missing", np.nan)
        rows.append(diag)
        if diag.get("n_countries", 0) == 0:
            logger.info(f"  {mod_key}: NO DATA")
            continue
        logger.info(
            f"  {mod_key} ({diag.get('label', '')}): "
            f"N_ctry={diag['n_countries']}, SD={diag.get('std', 0):.2f}, "
            f"distinct={diag.get('n_distinct', 0)}, "
            f"missing={diag.get('pct_missing', 0):.1f}%, "
            f"binary={diag['is_binary']}"
        )
        if diag.get("n_distinct", 0) < 4:
            logger.warning(f"    ⚠ <4 distinct values — limited leverage")
        if diag.get("pct_missing", 0) > 25:
            logger.warning(f"    ⚠ >25% countries missing")
    logger.info(f"\n{BAR}")
    return pd.DataFrame(rows)


def step_screening(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Step 2: single-interaction screening regressions."""
    logger.info(f"\n{BAR}\n  Step 2: Screening regressions\n{SEP}")
    controls = get_controls(df_raw)
    controls_str = " + ".join(controls)
    results = []

    for sample_mode in ["full", "common"]:
        df_s = apply_sample_filter(df_raw.copy(), sample_mode)
        for mod_key in CANDIDATES:
            info = MODERATOR_REGISTRY[mod_key]
            is_binary = info["is_binary"]
            mod_var = info["mod_var"]
            has_var = info["has_var"]

            if mod_var not in df_s.columns:
                logger.info(f"  {mod_key} [{sample_mode}]: column {mod_var} not in data — skip")
                continue

            df_m = df_s.copy()
            if has_var in df_m.columns:
                df_m = df_m[df_m[has_var]].copy()

            req = ["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap", mod_var]
            try:
                df_m = prepare_panel(df_m, require=req)
            except Exception as e:
                logger.warning(f"  {mod_key} [{sample_mode}]: prepare_panel failed — {e}")
                continue

            for c in controls:
                if c in df_m.columns:
                    df_m = df_m.dropna(subset=[c])
            df_m = df_m.drop_duplicates(subset=["entity", "year_int"]).copy()

            if len(df_m) < 50:
                logger.info(f"  {mod_key} [{sample_mode}]: N={len(df_m)} < 50 — skip")
                continue

            interaction_col = f"lr_{mod_key}"
            df_m[interaction_col] = df_m["ln_robots_lag1"] * df_m[mod_var]

            formula = (
                f"ln_hours ~ ln_robots_lag1 + {interaction_col} + "
                f"{controls_str} + EntityEffects + TimeEffects"
            )

            try:
                res = run_panelols(formula, df_m)
            except Exception as e:
                logger.warning(f"  {mod_key} [{sample_mode}]: regression failed — {e}")
                continue

            beta = res.params.get(interaction_col, np.nan)
            se = res.std_errors.get(interaction_col, np.nan)
            t = beta / se if se and se > 0 else np.nan
            pval = res.pvalues.get(interaction_col, np.nan)
            r2w = getattr(res, "rsquared_within", res.rsquared)

            n_ctry = df_m["country_code"].nunique() if "country_code" in df_m.columns else 0

            logger.info(
                f"  {mod_key} [{sample_mode}]: β={beta:.4f}, SE={se:.4f}, "
                f"t={t:.2f}, p={pval:.4f}, R²w={r2w:.4f}, N={res.nobs}, Ctry={n_ctry}"
            )

            countries_list = sorted(df_m["country_code"].unique()) if "country_code" in df_m.columns else []
            countries_str = ",".join(countries_list)
            miss_pct = float(1 - df_m[has_var].mean()) * 100 if has_var in df_m.columns else np.nan
            results.append({
                "moderator": mod_key,
                "label": info["label"],
                "sample": sample_mode,
                "beta": beta,
                "se": se,
                "t_stat": t,
                "pval": pval,
                "r2_within": r2w,
                "n_obs": res.nobs,
                "n_countries": n_ctry,
                "missing_pct": miss_pct,
                "countries": countries_str,
                "is_binary": is_binary,
            })

    logger.info(f"\n{BAR}")
    return pd.DataFrame(results)


def main():
    logger.info("ICTWSS Moderator Triage")
    logger.info("Using pre-sample (1990-1995) institution measures from cleaned_data.")
    df = pd.read_csv(CLEANED_PATH)

    desc_df = step_descriptive(df)
    screen_df = step_screening(df)

    OUTPUT_PATH.mkdir(exist_ok=True)

    if not screen_df.empty:
        screen_df = screen_df.sort_values("pval", ascending=True)
        out_path = OUTPUT_PATH / "ictwss_moderator_triage.csv"
        screen_df.to_csv(out_path, index=False)
        logger.info(f"\nTriage results → {out_path}")

        logger.info(f"\n{BAR}\n  Step 3: Diagnostic summary\n{SEP}")
        logger.info("  Screening results (for transparency — NOT a selection criterion):")
        for _, row in screen_df.iterrows():
            tag = "MAINLINE" if row["moderator"] in MAINLINE_MODERATORS else "appendix"
            logger.info(
                f"  {row['moderator']:>12} [{row['sample']:>6}]: "
                f"|t|={abs(row['t_stat']):.2f}, p={row['pval']:.4f}  ({tag})"
            )

        mainline_str = ", ".join(MAINLINE_MODERATORS)
        appendix_mods = [m for m in CANDIDATES if m not in MAINLINE_MODERATORS]
        appendix_str = ", ".join(appendix_mods) if appendix_mods else "(none)"
        logger.info(f"\n  Pre-declared mainline set: {mainline_str}")
        logger.info(f"  Appendix-only (if at all):  {appendix_str}")
        logger.info(f"  Moderators are chosen on theoretical and data-quality grounds,")
        logger.info(f"  not by t-stat ranking from this triage.")
        logger.info(f"\n{BAR}")

    if not desc_df.empty:
        desc_path = OUTPUT_PATH / "ictwss_moderator_descriptives.csv"
        desc_df.to_csv(desc_path, index=False)
        logger.info(f"Descriptive stats → {desc_path}")

    if not screen_df.empty:
        cl_rows = []
        for _, row in screen_df.iterrows():
            for cc in (row.get("countries", "") or "").split(","):
                cc = cc.strip()
                if cc:
                    cl_rows.append({
                        "moderator": row["moderator"],
                        "sample": row["sample"],
                        "country_code": cc,
                    })
        if cl_rows:
            cl_df = pd.DataFrame(cl_rows)
            cl_path = OUTPUT_PATH / "ictwss_country_lists.csv"
            cl_df.to_csv(cl_path, index=False)
            logger.info(f"Country lists per moderator/sample → {cl_path}")


if __name__ == "__main__":
    main()
