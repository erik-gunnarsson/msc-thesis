from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

from _klems_utils import BAR, OUTPUT_PATH, SEP
from _wiod_panel_utils import (
    WIOD_PANEL_PATH,
    build_fe_formula,
    ensure_output_dir,
    load_wiod_panel,
    sample_header,
    save_wiod_panel,
    summarise_key_terms,
    write_run_metadata,
    write_sample_manifest,
)


def load_or_build_wiod_panel() -> pd.DataFrame:
    if WIOD_PANEL_PATH.exists():
        return load_wiod_panel()
    logger.info("WIOD panel cache missing; building data/cleaned_data_wiod.csv")
    return save_wiod_panel()


def sample_stats(df: pd.DataFrame) -> dict[str, object]:
    countries = sorted(df["country_code"].dropna().unique().tolist())
    years = sorted(df["year_int"].dropna().astype(int).unique().tolist())
    return {
        "n_obs": int(len(df)),
        "n_entities": int(df["entity"].nunique()),
        "n_countries": int(len(countries)),
        "countries": countries,
        "year_min": int(min(years)) if years else None,
        "year_max": int(max(years)) if years else None,
    }


def build_restricted_formulas(
    outcome: str,
    rhs_terms: list[str],
    key_terms: list[str],
) -> dict[str, str]:
    restricted: dict[str, str] = {}
    for term in key_terms:
        reduced_terms = [rhs for rhs in rhs_terms if rhs != term]
        restricted[term] = build_fe_formula(outcome, reduced_terms)
    return restricted


def add_ci_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ci95_low_country_cluster"] = out["coef_country_cluster"] - 1.96 * out["se_country_cluster"]
    out["ci95_high_country_cluster"] = out["coef_country_cluster"] + 1.96 * out["se_country_cluster"]
    return out


def write_model_bundle(
    *,
    prefix: str,
    title: str,
    result,
    rhs_terms: list[str],
    key_terms: list[str],
    bootstrap_terms: list[str] | None = None,
    flags: dict[str, object],
    sample_mode: str = "full",
    bootstrap_reps: int = 99,
    bootstrap_seed: int = 123,
    extra_lines: list[str] | None = None,
) -> pd.DataFrame:
    ensure_output_dir()
    OUTPUT_PATH.mkdir(exist_ok=True)

    bootstrap_terms = bootstrap_terms or key_terms
    restricted = build_restricted_formulas("ln_h_empe", rhs_terms, bootstrap_terms)
    key_df = summarise_key_terms(
        result,
        key_terms=key_terms,
        restricted_formulas=restricted,
        bootstrap_reps=bootstrap_reps,
        bootstrap_seed=bootstrap_seed,
    )
    key_df = add_ci_columns(key_df)
    key_df.to_csv(OUTPUT_PATH / f"{prefix}_key_terms.csv", index=False)

    stats = sample_stats(result.sample)
    write_sample_manifest(result.sample, prefix, sample_mode=sample_mode)
    write_run_metadata(
        f"{prefix}.py",
        flags,
        n_obs=stats["n_obs"],
        n_entities=stats["n_entities"],
    )

    lines = [
        title,
        BAR,
        f"Formula: {result.formula}",
        f"Panel formula: {result.panel_formula}",
        (
            f"Sample: {stats['n_obs']} obs, {stats['n_entities']} entities, "
            f"{stats['n_countries']} countries, {stats['year_min']}-{stats['year_max']}"
        ),
        SEP,
    ]
    if extra_lines:
        lines.extend(extra_lines)
        lines.append(SEP)
    lines.extend(
        [
            "Country-clustered FE summary",
            result.headline.summary().as_text(),
            "",
            "Key terms (country cluster, entity cluster, DK, wild cluster bootstrap)",
            key_df.to_string(index=False),
            "",
        ]
    )
    if result.driscoll_kraay is not None:
        lines.extend(
            [
                "Driscoll-Kraay comparison",
                str(result.driscoll_kraay.summary),
                "",
            ]
        )
    lines.extend(
        [
            "Entity-clustered comparison",
            result.entity_clustered.summary().as_text(),
            "",
        ]
    )

    text = sample_header(result.sample) + "\n".join(lines) + "\n"
    (OUTPUT_PATH / f"{prefix}_results.txt").write_text(text, encoding="utf-8")

    logger.info(
        f"{title}: saved key terms to {OUTPUT_PATH / f'{prefix}_key_terms.csv'} "
        f"and results to {OUTPUT_PATH / f'{prefix}_results.txt'}"
    )
    return key_df
