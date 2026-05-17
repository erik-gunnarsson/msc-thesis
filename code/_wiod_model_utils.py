from __future__ import annotations

"""WIOD regression helpers: panel load, restricted-formula bootstrap pairs, table assembly.

``write_model_bundle`` emits ``*_key_terms.csv``, ``*_table_terms.csv``,
``*_table_meta.json``, ``*_results.txt``, ``sample_manifest_*.txt``, and
``run_metadata_*.json`` for a given artefact *prefix*.

**Provenance note:** ``write_run_metadata`` is called with ``f"{prefix}.py"`` so the
JSON ``script`` field matches the output stem — it is **not** always the Python file
you ran (e.g. ``14_wiod_first_results.py`` coordinates estimates produced by
``10_*`` / ``11_*``). Use ``wiod_first_results_run_manifest.json`` and per-model
``*_table_meta.json`` for sample/formula detail.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

from _paths import RESULTS_CORE_DIR, ensure_results_dirs
from _shared_utils import BAR, SEP
from _wiod_panel_utils import (
    WIOD_PANEL_PATH,
    build_fe_formula,
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
    """Map each bootstrapped term to a restricted formula (H0: coefficient is zero).

    For every ``term`` in ``key_terms``, the restricted model uses the same outcome
    and fixed effects as the full spec, but the RHS drops **only** ``term`` (all
    other ``rhs_terms`` unchanged). Used by ``wild_cluster_bootstrap_pvalue`` with
    restricted residual resampling under that null.
    """
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


def is_absorbed_fe_term(term: str) -> bool:
    return term == "Intercept" or term.startswith("C(entity)") or term.startswith("C(year_int)")


def summarise_table_terms(
    result,
    *,
    p_wild_by_term: dict[str, float] | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    p_wild_by_term = p_wild_by_term or {}

    for term in result.headline.params.index:
        if is_absorbed_fe_term(term):
            continue

        row = {
            "term": term,
            "coef_country_cluster": float(result.headline.params.get(term, np.nan)),
            "se_country_cluster": float(result.headline.bse.get(term, np.nan)),
            "p_country_cluster": float(result.headline.pvalues.get(term, np.nan)),
            "coef_entity_cluster": float(result.entity_clustered.params.get(term, np.nan)),
            "se_entity_cluster": float(result.entity_clustered.bse.get(term, np.nan)),
            "p_entity_cluster": float(result.entity_clustered.pvalues.get(term, np.nan)),
            "coef_driscoll_kraay": np.nan,
            "se_driscoll_kraay": np.nan,
            "p_driscoll_kraay": np.nan,
            "p_wild_cluster": float(p_wild_by_term.get(term, np.nan)),
        }
        if result.driscoll_kraay is not None and term in result.driscoll_kraay.params.index:
            row["coef_driscoll_kraay"] = float(result.driscoll_kraay.params.get(term, np.nan))
            row["se_driscoll_kraay"] = float(result.driscoll_kraay.std_errors.get(term, np.nan))
            row["p_driscoll_kraay"] = float(result.driscoll_kraay.pvalues.get(term, np.nan))
        rows.append(row)

    return pd.DataFrame(rows)


def build_table_metadata(
    *,
    prefix: str,
    title: str,
    result,
    stats: dict[str, object],
    flags: dict[str, object],
    sample_mode: str,
    key_terms: list[str],
) -> dict[str, object]:
    year_min = stats["year_min"]
    year_max = stats["year_max"]
    years = None if year_min is None or year_max is None else f"{year_min}-{year_max}"
    return {
        "prefix": prefix,
        "title": title,
        "sample_mode": sample_mode,
        "formula": result.formula,
        "panel_formula": result.panel_formula,
        "n_observations": stats["n_obs"],
        "n_entities": stats["n_entities"],
        "n_countries": stats["n_countries"],
        "countries": stats["countries"],
        "year_min": year_min,
        "year_max": year_max,
        "years": years,
        "r_squared": float(getattr(result.headline, "rsquared", np.nan)),
        "adj_r_squared": float(getattr(result.headline, "rsquared_adj", np.nan)),
        "fixed_effects": {
            "country_industry": True,
            "year": True,
        },
        "key_terms": key_terms,
        "flags": flags,
    }


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
    bootstrap_reps: int = 999,
    bootstrap_seed: int = 123,
    bootstrap_show_progress: bool = True,
    extra_lines: list[str] | None = None,
    out_dir: Path | None = None,
) -> pd.DataFrame:
    ensure_results_dirs()
    target_dir = out_dir or RESULTS_CORE_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    bootstrap_terms = bootstrap_terms or key_terms
    flags = {
        **flags,
        "effective_bootstrap_seed_by_term": {
            term: int(bootstrap_seed + idx) for idx, term in enumerate(key_terms)
        },
    }
    restricted = build_restricted_formulas("ln_h_empe", rhs_terms, bootstrap_terms)
    key_df = summarise_key_terms(
        result,
        key_terms=key_terms,
        restricted_formulas=restricted,
        bootstrap_reps=bootstrap_reps,
        bootstrap_seed=bootstrap_seed,
        bootstrap_show_progress=bootstrap_show_progress,
    )
    key_df = add_ci_columns(key_df)
    key_df.to_csv(target_dir / f"{prefix}_key_terms.csv", index=False)

    stats = sample_stats(result.sample)
    table_terms = summarise_table_terms(
        result,
        p_wild_by_term=key_df.set_index("term")["p_wild_cluster"].to_dict(),
    )
    table_terms = add_ci_columns(table_terms)
    table_terms.to_csv(target_dir / f"{prefix}_table_terms.csv", index=False)

    table_metadata = build_table_metadata(
        prefix=prefix,
        title=title,
        result=result,
        stats=stats,
        flags=flags,
        sample_mode=sample_mode,
        key_terms=key_terms,
    )
    (target_dir / f"{prefix}_table_meta.json").write_text(
        json.dumps(table_metadata, indent=2),
        encoding="utf-8",
    )

    write_sample_manifest(result.sample, prefix, sample_mode=sample_mode, out_dir=target_dir)
    # run_metadata "script" is the artifact prefix + ".py" (stable stem), not necessarily the invoking file — see module docstring.
    write_run_metadata(
        f"{prefix}.py",
        flags,
        n_obs=stats["n_obs"],
        n_entities=stats["n_entities"],
        out_dir=target_dir,
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
    (target_dir / f"{prefix}_results.txt").write_text(text, encoding="utf-8")

    logger.info(
        f"{title}: saved key terms to {target_dir / f'{prefix}_key_terms.csv'}, "
        f"table terms to {target_dir / f'{prefix}_table_terms.csv'}, "
        f"table metadata to {target_dir / f'{prefix}_table_meta.json'}, "
        f"and results to {target_dir / f'{prefix}_results.txt'}"
    )
    return key_df
