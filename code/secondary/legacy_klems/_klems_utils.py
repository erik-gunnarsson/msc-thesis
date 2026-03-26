'''
Shared utilities for the legacy KLEMS robustness scripts.

All data comes from 02_build_klems_panel.py output (cleaned_data.csv).
No data wrangling here; equation scripts use pre-built vars.

Single source of truth for the moderator registry
(bargaining coordination primary, adjusted coverage secondary, union density
reference), CLI helpers, and post-estimation tools.

Dependent variable: ln(LAB_QI) — labour input proxy (column: ln_hours).
Moderators use predetermined (1990-1995) values with _pre_c (centered) suffix.
Coord is continuous by default; binary (high_coord_pre) is robustness only.
'''

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from loguru import logger

try:
    from linearmodels import PanelOLS
except ImportError:
    PanelOLS = None

ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
CLEANED_PATH = DATA_DIR / "cleaned_data.csv"
OUTPUT_PATH = ROOT_DIR / "results" / "secondary" / "legacy_klems"

BAR = "═" * 56
SEP = "─" * 56

# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------


def get_step(default: int = 1) -> int:
    """Parse step from STEP env var or first CLI arg. E.g. STEP=2 or python script.py 2"""
    step = default
    if len(sys.argv) > 1:
        try:
            step = int(sys.argv[1])
        except ValueError:
            pass
    return step


def get_controls(df: pd.DataFrame) -> list:
    controls = ["ln_va", "ln_cap"]
    if "ln_gdp" in df.columns and df["ln_gdp"].notna().any():
        controls.append("ln_gdp")
    if "unemployment" in df.columns and df["unemployment"].notna().any():
        controls.append("unemployment")
    return controls


def prepare_panel(df: pd.DataFrame, require: Optional[list] = None) -> pd.DataFrame:
    """Prepare panel: dropna on required cols, dedupe, set index."""
    require = require or ["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap"]
    df = df.dropna(subset=require).copy()
    df = df.drop_duplicates(subset=["entity", "year_int"])
    df = df.set_index(["entity", "year_int"], drop=False)
    return df.sort_index()


def run_panelols(formula: str, df: pd.DataFrame, cov_type: str = "clustered"):
    """Estimate PanelOLS. cov_type: 'clustered' (default) or 'kernel' (Driscoll-Kraay)."""
    if PanelOLS is None:
        raise RuntimeError("linearmodels not installed. Run: uv pip install linearmodels")
    mod = PanelOLS.from_formula(formula, data=df, drop_absorbed=True)
    if cov_type == "driscoll-kraay":
        return mod.fit(cov_type="kernel", kernel="bartlett", bandwidth=5)
    return mod.fit(cov_type="clustered", cluster_entity=True)


# ---------------------------------------------------------------------------
# Moderator registry & CLI helpers
# ---------------------------------------------------------------------------

MODERATOR_REGISTRY = {
    "coord": {
        "mod_var": "coord_pre_c",
        "continuous_var": "coord_pre",
        "centered_var": "coord_pre_c",
        "binary_var": "high_coord_pre",
        "has_var": "has_coord",
        "is_binary": False,
        "label": "Bargaining coordination",
        "role_label": "primary focal moderator",
        "workflow_tier": "primary",
        "active_workflow": True,
        "priority_rank": 1,
        "theory_note": "Bargaining coordination is the headline institutional channel because it combines strong theory fit with workable country coverage.",
        "sample_caveat": "Preferred focal specification in both WIOD and KLEMS workflows.",
    },
    "adjcov": {
        "mod_var": "adjcov_pre_c",
        "continuous_var": "adjcov_pre",
        "centered_var": "adjcov_pre_c",
        "has_var": "has_adjcov",
        "is_binary": False,
        "label": "Adjusted collective-bargaining coverage",
        "role_label": "secondary focal moderator",
        "workflow_tier": "secondary",
        "active_workflow": True,
        "priority_rank": 2,
        "theory_note": "Adjusted collective-bargaining coverage is theoretically important, but inference is constrained by the smaller common-sample country set.",
        "sample_caveat": "Restricted/common-sample specification in practice.",
    },
    "ud": {
        "mod_var": "ud_pre_c",
        "continuous_var": "ud_pre",
        "centered_var": "ud_pre_c",
        "has_var": "has_ud",
        "is_binary": False,
        "label": "Union Density",
        "role_label": "reference benchmark",
        "workflow_tier": "reference",
        "active_workflow": True,
        "priority_rank": 3,
        "theory_note": "Union density is retained as a reference comparison because it has broader coverage, but it is not a focal institutional channel in the thesis theory.",
        "sample_caveat": "Reference benchmark only; do not treat as co-equal with coord or adjcov.",
    },
    "wstat": {
        "mod_var": "wstat_pre_c",
        "continuous_var": "wstat_pre",
        "centered_var": "wstat_pre_c",
        "has_var": "has_wstat",
        "is_binary": False,
        "label": "Statutory Bargaining Scope",
        "role_label": "appendix candidate",
        "workflow_tier": "appendix",
        "active_workflow": False,
        "priority_rank": 10,
        "theory_note": "Appendix-only institutional candidate retained for diagnostic screening.",
        "sample_caveat": "Not part of the active thesis workflow.",
    },
    "wc": {
        "mod_var": "wc_pre_binary",
        "continuous_var": "wc_pre",
        "centered_var": None,
        "has_var": "has_wc",
        "is_binary": True,
        "label": "Works Council",
        "role_label": "appendix candidate",
        "workflow_tier": "appendix",
        "active_workflow": False,
        "priority_rank": 11,
        "theory_note": "Appendix-only institutional candidate retained for diagnostic screening.",
        "sample_caveat": "Not part of the active thesis workflow.",
    },
    "spa_signed": {
        "mod_var": "spa_signed_pre_binary",
        "continuous_var": "spa_signed_pre",
        "centered_var": None,
        "has_var": "has_spa_signed",
        "is_binary": True,
        "label": "Social Pacts",
        "role_label": "appendix candidate",
        "workflow_tier": "appendix",
        "active_workflow": False,
        "priority_rank": 12,
        "theory_note": "Appendix-only institutional candidate retained for diagnostic screening.",
        "sample_caveat": "Not part of the active thesis workflow.",
    },
}


MAINLINE_MODERATORS = ["coord", "adjcov", "ud"]


def ordered_moderator_keys(keys: Optional[list[str]] = None, *, active_only: bool = False) -> list[str]:
    """Return moderator keys in declared theory/workflow order."""
    key_list = list(keys or MODERATOR_REGISTRY.keys())
    if active_only:
        key_list = [key for key in key_list if MODERATOR_REGISTRY[key].get("active_workflow", False)]
    return sorted(
        key_list,
        key=lambda key: (
            MODERATOR_REGISTRY[key].get("priority_rank", 999),
            MODERATOR_REGISTRY[key].get("label", key),
        ),
    )


def add_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Add shared CLI flags used by multiple equation scripts."""
    parser.add_argument("step", nargs="?", type=int, default=1, help="Pipeline step")
    parser.add_argument(
        "--moderator", type=str, default=None,
        choices=list(MODERATOR_REGISTRY.keys()),
        help="Moderator variable (default depends on script)",
    )
    parser.add_argument(
        "--sample", type=str, default="full", choices=["full", "common"],
        help="Sample: full (default) or common (countries with AdjCov data)",
    )
    parser.add_argument(
        "--coord-mode", type=str, default="continuous", choices=["binary", "continuous"],
        help="Coordination specification: continuous (default) or binary (Coord≥4, robustness)",
    )
    parser.add_argument(
        "--se", type=str, default="clustered", choices=["clustered", "driscoll-kraay"],
        help="Standard error estimator (default: entity-clustered)",
    )
    parser.add_argument(
        "--trends", type=str, default="none", choices=["none"],
        help="Legacy placeholder; bucket-trend variants were archived with Eq. 3/4.",
    )
    return parser


def parse_args(default_moderator: str = "coord") -> argparse.Namespace:
    """Parse CLI arguments with common flags.

    When moderator is 'adjcov', sample is forced to 'common' because
    adjcov is only available for a subset of countries.
    """
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    args = parser.parse_args()
    if args.moderator is None:
        args.moderator = default_moderator
    if args.moderator == "adjcov" and args.sample != "common":
        logger.info("Forcing --sample common (adjcov requires countries with AdjCov data)")
        args.sample = "common"
    return args


def get_moderator(mod_key: str = "coord") -> dict:
    """Return moderator info dict from the registry."""
    if mod_key not in MODERATOR_REGISTRY:
        raise ValueError(f"Unknown moderator '{mod_key}'. Choose from: {list(MODERATOR_REGISTRY.keys())}")
    return MODERATOR_REGISTRY[mod_key]


def moderator_role_summary(mod_key: str) -> str:
    """Return a one-line summary of moderator role and theory note."""
    info = get_moderator(mod_key)
    return f"{info['role_label']} — {info['theory_note']}"


def moderator_to_columns(mod_key: str, coord_mode: str = "continuous") -> tuple:
    """
    Map moderator key to (mod_var, has_var, is_binary).

    For coord with coord_mode='binary', returns high_coord_pre (robustness).
    Default is continuous (coord_pre_c).
    """
    info = get_moderator(mod_key)
    mod_var = info["mod_var"]
    if mod_key == "coord" and coord_mode == "binary":
        mod_var = info["binary_var"]
        return mod_var, info["has_var"], True
    return mod_var, info["has_var"], info["is_binary"]


def apply_sample_filter(df: pd.DataFrame, sample: str = "full") -> pd.DataFrame:
    """Apply common-sample filter: restrict to countries with AdjCov data."""
    if sample == "common" and "has_adjcov" in df.columns:
        before = len(df)
        df = df[df["has_adjcov"]].copy()
        logger.info(f"Common sample filter: {before} → {len(df)} rows (countries with AdjCov)")
    return df


def moderator_diagnostics(df: pd.DataFrame, mod_key: str) -> dict:
    """Return descriptive stats for a moderator variable (country-level)."""
    info = get_moderator(mod_key)
    pre_col = info["continuous_var"]
    has_col = info["has_var"]

    if pre_col not in df.columns:
        return {"moderator": mod_key, "n_countries": 0, "error": f"column {pre_col} not found"}

    vals = df.groupby("country_code")[pre_col].first().dropna()
    n_ctry = len(vals)
    if n_ctry == 0:
        return {"moderator": mod_key, "n_countries": 0}

    return {
        "moderator": mod_key,
        "label": info["label"],
        "role_label": info.get("role_label"),
        "workflow_tier": info.get("workflow_tier"),
        "active_workflow": info.get("active_workflow"),
        "priority_rank": info.get("priority_rank"),
        "theory_note": info.get("theory_note"),
        "sample_caveat": info.get("sample_caveat"),
        "n_countries": n_ctry,
        "mean": float(vals.mean()),
        "std": float(vals.std()),
        "min": float(vals.min()),
        "max": float(vals.max()),
        "p10": float(vals.quantile(0.10)),
        "p90": float(vals.quantile(0.90)),
        "n_distinct": int(vals.nunique()),
        "pct_missing": float(1 - df[has_col].mean()) * 100 if has_col in df.columns else np.nan,
    }


def add_trend_terms(df: pd.DataFrame, formula: str, trends: str = "none") -> str:
    """Legacy no-op kept for interface stability after bucket-model archival."""
    if trends != "none":
        logger.info("Ignoring archived trend option; only 'none' remains active.")
    return formula


# ---------------------------------------------------------------------------
# Sample manifest & run metadata (C10, C11)
# ---------------------------------------------------------------------------


def format_sample_header(df: pd.DataFrame) -> str:
    """Return sample header (N obs, entities, countries) for regression outputs."""
    countries = sorted(df["country_code"].unique()) if "country_code" in df.columns else []
    n_obs = len(df)
    n_ent = df["entity"].nunique() if "entity" in df.columns else 0
    return (
        f"Sample: {n_obs} obs, {n_ent} entities\n"
        f"Countries ({len(countries)}): {', '.join(countries)}\n"
        f"{'─' * 56}\n"
    )


def write_sample_manifest(df: pd.DataFrame, tag: str,
                          sample_mode: str = "full",
                          out_dir: Optional[Path] = None) -> Path:
    """Write a sample manifest for the regression run."""
    out_dir = out_dir or OUTPUT_PATH
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"sample_manifest_{tag}.txt"

    countries = sorted(df["country_code"].unique()) if "country_code" in df.columns else []
    n_entities = df["entity"].nunique() if "entity" in df.columns else 0
    n_obs = len(df)
    yr_min = int(df["year_int"].min()) if "year_int" in df.columns else None
    yr_max = int(df["year_int"].max()) if "year_int" in df.columns else None

    lines = [
        f"Sample manifest: {tag}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Sample mode: {sample_mode}",
        "=" * 50,
        f"Observations: {n_obs}",
        f"Entities: {n_entities}",
        f"Countries ({len(countries)}): {', '.join(countries)}",
        f"Year range: {yr_min}-{yr_max}",
        "",
        "Key variable missingness:",
    ]
    for col in ["ln_robots_lag1", "ln_hours", "ud_pre_c", "coord_pre_c", "adjcov_pre_c",
                 "coord_pre", "adjcov_pre", "ud_pre", "wstat_pre"]:
        if col in df.columns:
            n_miss = df[col].isna().sum()
            pct = n_miss / n_obs * 100
            lines.append(f"  {col}: {n_miss} missing ({pct:.1f}%)")

    path.write_text("\n".join(lines))
    logger.info(f"Sample manifest → {path}")
    return path


def write_run_metadata(script_name: str, flags: dict, n_obs: int,
                       n_entities: int, out_dir: Optional[Path] = None) -> Path:
    """Write run metadata (timestamp, git hash, flags) as JSON."""
    out_dir = out_dir or OUTPUT_PATH
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = Path(script_name).stem
    path = out_dir / f"run_metadata_{tag}.json"

    try:
        git_hash = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip() or "unknown"
    except Exception:
        git_hash = "unknown"

    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_hash,
        "script": script_name,
        "flags": flags,
        "n_obs": n_obs,
        "n_entities": n_entities,
    }
    path.write_text(json.dumps(meta, indent=2))
    logger.info(f"Run metadata → {path}")
    return path


# ---------------------------------------------------------------------------
# Diagnostics: baseline vs coverage vs coord samples (used by eq 2/3)
# ---------------------------------------------------------------------------


def run_diagnostics(df_full: pd.DataFrame) -> dict:
    """Compare baseline vs coverage vs coord samples. Return sample stats."""
    baseline = prepare_panel(df_full)
    coverage = prepare_panel(df_full, require=["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap", "adjcov"])
    coord = prepare_panel(df_full, require=["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap", "coord"])

    ctrl = get_controls(df_full)
    for c in ctrl:
        if c in baseline.columns:
            baseline = baseline.dropna(subset=[c])
            coverage = coverage.dropna(subset=[c])
            coord = coord.dropna(subset=[c])

    baseline = baseline.drop_duplicates(subset=["entity", "year_int"])
    coverage = coverage.drop_duplicates(subset=["entity", "year_int"])
    coord = coord.dropna(subset=["entity", "year_int"]).drop_duplicates(subset=["entity", "year_int"])

    def _stats(d, name):
        return {
            "name": name,
            "n_obs": len(d),
            "n_entities": d.index.get_level_values("entity").nunique() if hasattr(d.index, "get_level_values") else d["entity"].nunique(),
            "countries": sorted(d["country_code"].unique()) if "country_code" in d.columns else [],
        }

    base_ind = baseline.groupby("nace_r2_code").size()
    cov_ind = coverage.groupby("nace_r2_code").size().reindex(base_ind.index, fill_value=0)
    pct_by_ind = (cov_ind / base_ind * 100).round(1)

    return {
        "baseline": _stats(baseline, "baseline"),
        "coverage": _stats(coverage, "coverage"),
        "coord": _stats(coord, "coordination"),
        "dropped_countries_cov": set(baseline["country_code"].unique()) - set(coverage["country_code"].unique()),
        "pct_kept_cov": len(coverage) / len(baseline) * 100 if len(baseline) > 0 else 0,
        "pct_kept_coord": len(coord) / len(baseline) * 100 if len(baseline) > 0 else 0,
        "ind_baseline": base_ind,
        "ind_coverage": cov_ind,
        "ind_pct": pct_by_ind,
    }


def log_diagnostics(df_full: pd.DataFrame) -> dict:
    """Log diagnostic output. Return diagnostics dict for use in models."""
    diag = run_diagnostics(df_full)

    logger.info(f"\n{BAR}\n  Sample diagnostics\n{SEP}")

    b, c, co = diag["baseline"], diag["coverage"], diag["coord"]
    logger.info(f"  1. Sample sizes")
    logger.info(f"     Baseline:    {b['n_obs']} obs, {b['n_entities']} entities")
    logger.info(f"     Coverage:    {c['n_obs']} obs, {c['n_entities']} entities  ({diag['pct_kept_cov']:.1f}% of baseline)")
    logger.info(f"     Coord:      {co['n_obs']} obs, {co['n_entities']} entities  ({diag['pct_kept_coord']:.1f}% of baseline)")

    dropped = diag["dropped_countries_cov"]
    if dropped:
        logger.warning(f"\n  2. Countries DROPPED in coverage model (no AdjCov): {sorted(dropped)}")
    else:
        logger.info(f"\n  2. No countries dropped (AdjCov available for all)")

    logger.info(f"\n  3. AdjCov missing by country (raw cleaned_data)")
    miss = df_full.groupby("country_code")["adjcov"].apply(lambda x: x.isna().sum())
    for cc in sorted(df_full["country_code"].unique()):
        n = miss.get(cc, 0)
        status = "⚠ missing" if n > 0 else "✓"
        logger.info(f"     {cc}: {n} rows missing  {status}")

    logger.info(f"\n  4. Coordination (Coord) missing by country")
    miss_coord = df_full.groupby("country_code")["coord"].apply(lambda x: x.isna().sum())
    for cc in sorted(df_full["country_code"].unique()):
        n = miss_coord.get(cc, 0)
        status = "⚠ missing" if n > 0 else "✓"
        logger.info(f"     {cc}: {n} rows missing  {status}")

    base_ind = diag["ind_baseline"]
    cov_ind = diag["ind_coverage"]
    pct_by_ind = diag["ind_pct"]
    logger.info(f"\n  5. Observations by industry (baseline vs coverage, % kept)")
    for nace in base_ind.index[:10]:
        logger.info(f"     {nace}: baseline={int(base_ind.get(nace,0))}, coverage={int(cov_ind.get(nace,0))}, {pct_by_ind.get(nace,0):.0f}%")
    if len(base_ind) > 10:
        logger.info(f"     ... and {len(base_ind)-10} more industries")

    logger.info(f"\n{BAR}\n")
    return diag
