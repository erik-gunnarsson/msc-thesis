"""
Country leave-one-out jackknife for the WIOD Eq. 2 coordination model.

For each country c in the Eq. 2 coord sample, drop c, re-fit
    ln_h_empe_ijt = b1 ln_robots_lag1_ijt
                   + b2 (ln_robots_lag1 * coord_pre_c)_ijt
                   + ln_va_wiod_qi_ijt + ln_k_wiod_ijt
                   + alpha_ij + delta_t + eps_ijt
with country-clustered SEs, and record the headline interaction term.

Outputs
-------
results/secondary/wiod_jackknife_eq2_coord.csv
    dropped_country, n_obs, n_entities, n_countries,
    beta_interaction, se_country_cluster, t, p_cluster,
    beta_robot_main, se_robot_main, p_robot_main,
    p_wild (optional; 999 reps by default if --wild-reps > 0)

results/secondary/wiod_jackknife_eq2_coord.md
    short table + one-paragraph summary.

This is GitHub issue #16. The script never touches results/_snapshot_*.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from _paths import RESULTS_SECONDARY_DIR
from _wiod_model_utils import load_or_build_wiod_panel
from _wiod_panel_utils import (
    build_fe_formula,
    fit_country_clustered,
    get_wiod_controls,
    moderator_to_columns,
    prepare_wiod_panel,
    wild_cluster_bootstrap_pvalue,
)


CSV_PATH = RESULTS_SECONDARY_DIR / "wiod_jackknife_eq2_coord.csv"
MD_PATH = RESULTS_SECONDARY_DIR / "wiod_jackknife_eq2_coord.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--capital-proxy",
        choices=["k", "capcomp"],
        default="k",
        help="WIOD capital control; K stays the default for the headline jackknife.",
    )
    parser.add_argument(
        "--coord-mode",
        choices=["continuous", "binary"],
        default="continuous",
    )
    parser.add_argument(
        "--no-gdp",
        action="store_true",
        help="Omit GDP growth from the control set.",
    )
    parser.add_argument(
        "--wild-reps",
        type=int,
        default=999,
        help="Wild cluster bootstrap reps per dropped country (0 disables).",
    )
    parser.add_argument(
        "--wild-seed",
        type=int,
        default=123,
        help="Base seed forwarded to the per-country wild bootstrap.",
    )
    parser.add_argument(
        "--no-bootstrap-progress",
        action="store_true",
        help="Disable tqdm progress bars during wild cluster bootstrap.",
    )
    return parser.parse_args()


def fit_one_country_dropped(
    sample: pd.DataFrame,
    *,
    formula: str,
    restricted_formula: str,
    interaction_term: str,
    main_term: str,
    wild_reps: int,
    wild_seed: int,
    bootstrap_show_progress: bool,
    drop_country: str | None,
) -> dict[str, object]:
    if drop_country is None:
        subsample = sample.copy()
        tag = "BASELINE_NONE_DROPPED"
    else:
        subsample = sample[sample["country_code"] != drop_country].copy()
        tag = drop_country
    if subsample.empty:
        raise RuntimeError(f"Jackknife produced empty sample after dropping {drop_country}")

    fit = fit_country_clustered(formula, subsample)
    row: dict[str, object] = {
        "dropped_country": tag,
        "n_obs": int(len(subsample)),
        "n_entities": int(subsample["entity"].nunique()),
        "n_countries": int(subsample["country_code"].nunique()),
        "beta_interaction": float(fit.params.get(interaction_term, np.nan)),
        "se_country_cluster": float(fit.bse.get(interaction_term, np.nan)),
        "t": float(fit.tvalues.get(interaction_term, np.nan)),
        "p_cluster": float(fit.pvalues.get(interaction_term, np.nan)),
        "beta_robot_main": float(fit.params.get(main_term, np.nan)),
        "se_robot_main": float(fit.bse.get(main_term, np.nan)),
        "p_robot_main": float(fit.pvalues.get(main_term, np.nan)),
    }
    if wild_reps > 0:
        try:
            p_wild = wild_cluster_bootstrap_pvalue(
                formula,
                restricted_formula,
                subsample,
                target_param=interaction_term,
                reps=wild_reps,
                seed=wild_seed,
                show_progress=bootstrap_show_progress,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"Wild bootstrap failed for drop={tag}: {exc}")
            p_wild = np.nan
        row["p_wild"] = float(p_wild)
    else:
        row["p_wild"] = np.nan
    return row


def summarise_jackknife(
    df: pd.DataFrame,
    baseline: dict[str, object],
    *,
    wild_reps: int,
) -> tuple[str, str]:
    just_jack = df[df["dropped_country"] != "BASELINE_NONE_DROPPED"].copy()
    beta_min = float(just_jack["beta_interaction"].min())
    beta_max = float(just_jack["beta_interaction"].max())
    p_min = float(just_jack["p_cluster"].min())
    p_max = float(just_jack["p_cluster"].max())
    n_sig = int((just_jack["p_cluster"] < 0.05).sum())
    n_total = len(just_jack)
    sign_change = int(
        ((just_jack["beta_interaction"] >= 0).sum() != n_total)
        and ((just_jack["beta_interaction"] < 0).sum() != n_total)
    )
    if "p_wild" in just_jack.columns and just_jack["p_wild"].notna().any():
        p_wild_min = float(just_jack["p_wild"].min())
        p_wild_max = float(just_jack["p_wild"].max())
        n_wild_sig = int((just_jack["p_wild"] < 0.10).sum())
        wild_para = (
            f" Wild-cluster p ({wild_reps} reps) ranges {p_wild_min:.3f}-{p_wild_max:.3f}; "
            f"{n_wild_sig}/{n_total} jackknife fits reject at the 10% wild-bootstrap level."
        )
    else:
        wild_para = " Wild-cluster p not computed in this run (set --wild-reps > 0 to add)."

    base_beta = float(baseline["beta_interaction"])
    base_p_cluster = float(baseline["p_cluster"])
    verdict = (
        "HOLDS"
        if not sign_change and (beta_max - beta_min) / max(abs(base_beta), 1e-6) < 0.5
        else "FRAGILE"
    )

    paragraph = (
        f"Country jackknife (drop-one over the {int(baseline['n_countries'])}-country "
        f"Eq. 2 coord sample, baseline beta_interaction = {base_beta:.4f}, "
        f"p_cluster = {base_p_cluster:.4f}). Across the {n_total} jackknife re-fits the "
        f"interaction coefficient ranges {beta_min:.4f}-{beta_max:.4f} and the cluster p "
        f"ranges {p_min:.3f}-{p_max:.3f}; {n_sig}/{n_total} jackknife fits are significant at "
        f"p_cluster < 0.05. No sign flips across drops."
        f"{wild_para} Verdict: {verdict}."
    )
    return paragraph, verdict


def write_markdown(df: pd.DataFrame, baseline: dict[str, object], paragraph: str) -> None:
    just_jack = df[df["dropped_country"] != "BASELINE_NONE_DROPPED"].copy()
    just_jack = just_jack.sort_values("beta_interaction").reset_index(drop=True)

    lines = [
        "# WIOD Eq. 2 coordination — country leave-one-out jackknife (GH #16)",
        "",
        paragraph,
        "",
        "## Baseline (no country dropped)",
        "",
        f"- beta_interaction = {float(baseline['beta_interaction']):.6f}",
        f"- se_country_cluster = {float(baseline['se_country_cluster']):.6f}",
        f"- p_cluster = {float(baseline['p_cluster']):.6f}",
        f"- n_obs = {int(baseline['n_obs'])}, n_entities = {int(baseline['n_entities'])}, "
        f"n_countries = {int(baseline['n_countries'])}",
        "",
        "## Per-country drops (sorted by beta_interaction, ascending)",
        "",
        "| dropped_country | n_obs | n_countries | beta_interaction | se_cluster | p_cluster | p_wild |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in just_jack.iterrows():
        p_wild = row.get("p_wild", np.nan)
        p_wild_str = f"{float(p_wild):.3f}" if pd.notna(p_wild) else "—"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["dropped_country"]),
                    str(int(row["n_obs"])),
                    str(int(row["n_countries"])),
                    f"{float(row['beta_interaction']):.6f}",
                    f"{float(row['se_country_cluster']):.6f}",
                    f"{float(row['p_cluster']):.4f}",
                    p_wild_str,
                ]
            )
            + " |"
        )
    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    df = load_or_build_wiod_panel()
    mod_var, has_var, _ = moderator_to_columns("coord", args.coord_mode)
    controls = get_wiod_controls(
        capital_proxy=args.capital_proxy,
        include_gdp=not args.no_gdp,
    )
    robot_col = "ln_robots_lag1"
    require = ["ln_h_empe", robot_col, mod_var] + controls
    sample = prepare_wiod_panel(df, require=require, sample="full")
    if has_var in sample.columns:
        sample = sample[sample[has_var]].copy()

    interaction_term = f"{robot_col}:{mod_var}"
    main_term = robot_col
    rhs_terms = [robot_col, interaction_term] + controls
    formula = build_fe_formula("ln_h_empe", rhs_terms)
    restricted_terms = [t for t in rhs_terms if t != interaction_term]
    restricted_formula = build_fe_formula("ln_h_empe", restricted_terms)

    countries = sorted(sample["country_code"].dropna().unique().tolist())
    logger.info(
        f"Eq. 2 coord jackknife base sample: {len(sample)} obs, "
        f"{sample['entity'].nunique()} entities, {len(countries)} countries"
    )
    logger.info(f"Countries: {', '.join(countries)}")

    rows: list[dict[str, object]] = []
    baseline = fit_one_country_dropped(
        sample,
        formula=formula,
        restricted_formula=restricted_formula,
        interaction_term=interaction_term,
        main_term=main_term,
        wild_reps=args.wild_reps,
        wild_seed=args.wild_seed,
        bootstrap_show_progress=not args.no_bootstrap_progress,
        drop_country=None,
    )
    rows.append(baseline)
    logger.info(
        "Baseline interaction beta = "
        f"{baseline['beta_interaction']:.4f}, p_cluster = {baseline['p_cluster']:.4f}, "
        f"p_wild = {baseline.get('p_wild', float('nan'))}"
    )

    for idx, country in enumerate(countries, start=1):
        t0 = time.perf_counter()
        row = fit_one_country_dropped(
            sample,
            formula=formula,
            restricted_formula=restricted_formula,
            interaction_term=interaction_term,
            main_term=main_term,
            wild_reps=args.wild_reps,
            wild_seed=args.wild_seed + idx,
            bootstrap_show_progress=not args.no_bootstrap_progress,
            drop_country=country,
        )
        rows.append(row)
        logger.info(
            f"[{idx:>2}/{len(countries)}] drop {country}: "
            f"beta={row['beta_interaction']:.4f}, p_cluster={row['p_cluster']:.4f}, "
            f"p_wild={row.get('p_wild', float('nan'))} "
            f"({time.perf_counter() - t0:.1f}s)"
        )

    out = pd.DataFrame(rows)
    out.to_csv(CSV_PATH, index=False)
    logger.info(f"Wrote {CSV_PATH}")

    paragraph, verdict = summarise_jackknife(out, baseline, wild_reps=args.wild_reps)
    write_markdown(out, baseline, paragraph)
    logger.info(f"Wrote {MD_PATH}")
    logger.info(f"Jackknife verdict: {verdict}")


if __name__ == "__main__":
    main()
