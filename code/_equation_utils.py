'''
Shared utilities for equation scripts.

All data comes from 2-build_panel.py output (cleaned_data.csv).
No data wrangling here; equation scripts use pre-built vars.

Single source of truth for bucket definitions, moderator registry
(three-channel: UD, Coord, AdjCov), CLI helpers, and post-estimation tools.

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

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CLEANED_PATH = DATA_DIR / "cleaned_data.csv"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "outputs"

BAR = "═" * 56
SEP = "─" * 56

# ---------------------------------------------------------------------------
# Bucket definitions (single source of truth)
# ---------------------------------------------------------------------------

NACE_TO_BUCKET = {
    "C29-C30": 1,   # Transport equipment (robot-intensive)
    "C26-C27": 2,   # Electro-mechanical capital goods (robot-intensive)
    "C28":     2,
    "C24-C25": 3,   # Metals
    "C19":     4,   # Process & materials
    "C20-C21": 4,
    "C22-C23": 4,
    "C10-C12": 5,   # Low-tech / traditional
    "C13-C15": 5,
    "C16-C18": 5,
    "C31-C33": 5,
}

BUCKET_NAMES = {
    1: "Transport equipment",
    2: "Electro-mechanical",
    3: "Metals",
    4: "Process & materials",
    5: "Low-tech / traditional",
}

REF_BUCKET = 5

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
# Bucket dummies
# ---------------------------------------------------------------------------


def get_bucket_dummies(df: pd.DataFrame, ref_bucket: int = REF_BUCKET) -> list[str]:
    """Create bucket dummy columns (reference bucket omitted). Returns list of column names."""
    buckets = sorted(b for b in BUCKET_NAMES if b != ref_bucket)
    cols = []
    for b in buckets:
        col = f"bucket_{b}"
        df[col] = (df["bucket"] == b).astype(int)
        cols.append(col)
    return cols


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
        "label": "Coordination (continuous)",
    },
    "adjcov": {
        "mod_var": "adjcov_pre_c",
        "continuous_var": "adjcov_pre",
        "centered_var": "adjcov_pre_c",
        "has_var": "has_adjcov",
        "is_binary": False,
        "label": "Adjusted Coverage",
    },
    "ud": {
        "mod_var": "ud_pre_c",
        "continuous_var": "ud_pre",
        "centered_var": "ud_pre_c",
        "has_var": "has_ud",
        "is_binary": False,
        "label": "Union Density",
    },
    "wstat": {
        "mod_var": "wstat_pre_c",
        "continuous_var": "wstat_pre",
        "centered_var": "wstat_pre_c",
        "has_var": "has_wstat",
        "is_binary": False,
        "label": "Statutory Bargaining Scope",
    },
    "wc": {
        "mod_var": "wc_pre_binary",
        "continuous_var": "wc_pre",
        "centered_var": None,
        "has_var": "has_wc",
        "is_binary": True,
        "label": "Works Council",
    },
    "spa_signed": {
        "mod_var": "spa_signed_pre_binary",
        "continuous_var": "spa_signed_pre",
        "centered_var": None,
        "has_var": "has_spa_signed",
        "is_binary": True,
        "label": "Social Pacts",
    },
}


MAINLINE_MODERATORS = ["coord", "ud", "adjcov"]


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
        "--trends", type=str, default="none", choices=["none", "bucket"],
        help="Linear trend specification (default: none)",
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
    """Optionally add bucket-specific linear trends to the formula."""
    if trends == "bucket" and "year_int" in df.columns:
        bucket_cols = [c for c in df.columns if c.startswith("bucket_") and c[7:].isdigit()]
        trend_terms = []
        for col in sorted(bucket_cols):
            trend_col = f"{col}_trend"
            df[trend_col] = df[col] * df["year_int"]
            trend_terms.append(trend_col)
        if trend_terms:
            formula = formula.replace(
                "EntityEffects + TimeEffects",
                " + ".join(trend_terms) + " + EntityEffects + TimeEffects",
            )
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
    out_dir.mkdir(exist_ok=True)
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
    out_dir.mkdir(exist_ok=True)
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
# Planned contrasts for heterogeneity scripts (A5)
# ---------------------------------------------------------------------------

PLANNED_CONTRASTS = [(3, 5), (1, 5), (2, 5), (3, 4)]


# ---------------------------------------------------------------------------
# Linear contrast / Wald test helper
# ---------------------------------------------------------------------------


def test_linear_contrast(res, R: np.ndarray, q: Optional[np.ndarray] = None,
                         label: str = "") -> dict:
    """
    Wald test for H0: R @ beta = q.

    Parameters
    ----------
    res : PanelOLS result
    R   : (k,) or (m, k) restriction matrix, where k = len(res.params)
    q   : (m,) vector (defaults to zeros)
    label : human-readable name for the contrast

    Returns
    -------
    dict with keys: label, stat, pval, df
    """
    from scipy import stats as sp_stats

    R = np.atleast_2d(R)
    m = R.shape[0]
    if q is None:
        q = np.zeros(m)
    q = np.atleast_1d(q)

    beta = np.array(res.params)
    V = np.array(res.cov)

    diff = R @ beta - q
    meat = R @ V @ R.T
    try:
        chi2 = float(diff @ np.linalg.solve(meat, diff))
    except np.linalg.LinAlgError:
        chi2 = np.nan
    pval = 1.0 - sp_stats.chi2.cdf(chi2, df=m) if not np.isnan(chi2) else np.nan

    return {"label": label, "stat": chi2, "pval": pval, "df": m}


def _restriction_row(param_names: list, target: str, sign: float = 1.0) -> np.ndarray:
    """Build a single restriction row that picks out `target` param with given sign."""
    row = np.zeros(len(param_names))
    if target in param_names:
        row[param_names.index(target)] = sign
    return row


def build_pairwise_contrasts(res, bucket_list: list[int],
                             param_template: str,
                             label_template: str = "Bucket {a} vs {b}") -> list[dict]:
    """
    For all pairs of buckets, test H0: coeff for bucket a == coeff for bucket b.

    param_template should contain '{b}' which will be replaced by bucket number,
    e.g. 'ln_robots_lag1:bucket_{b}'.
    For the reference bucket the coefficient is implicitly 0 (baseline).
    """
    param_names = list(res.params.index)
    results = []
    for i, a in enumerate(bucket_list):
        for b in bucket_list[i + 1:]:
            R = np.zeros(len(param_names))
            pa = param_template.format(b=a)
            pb = param_template.format(b=b)
            if pa in param_names:
                R[param_names.index(pa)] = 1.0
            if pb in param_names:
                R[param_names.index(pb)] = -1.0
            label = label_template.format(a=a, b=b)
            results.append(test_linear_contrast(res, R, label=label))
    return results


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


# ---------------------------------------------------------------------------
# Diagnostics: bucket-level (used by eq 4/5 heterogeneity scripts)
# ---------------------------------------------------------------------------


def run_diagnostics_bucket(df_full: pd.DataFrame) -> dict:
    """
    Bucket-level diagnostics for the pooled interaction model.

    Reports per-bucket sample counts, within-bucket variation in key regressors,
    and institution sub-report (Coord/AdjCov descriptives + binary split checks).
    """
    base = prepare_panel(df_full, require=["ln_hours", "ln_robots_lag1", "ln_va", "ln_cap", "bucket"])
    ctrl = get_controls(df_full)
    for c in ctrl:
        if c in base.columns:
            base = base.dropna(subset=[c])
    base = base.drop_duplicates(subset=["entity", "year_int"])

    logger.info(f"\n{BAR}\n  Bucket diagnostics\n{SEP}")

    # --- 1. Per-bucket sample counts ---
    logger.info("  1. Per-bucket sample counts")
    bucket_stats = {}
    for b in sorted(BUCKET_NAMES.keys()):
        sub = base[base["bucket"] == b]
        n_obs = len(sub)
        n_ent = sub["entity"].nunique()
        n_ctry = sub["country_code"].nunique() if "country_code" in sub.columns else 0
        countries = sorted(sub["country_code"].unique()) if "country_code" in sub.columns else []
        bucket_stats[b] = {
            "n_obs": n_obs, "n_entities": n_ent, "n_countries": n_ctry,
            "countries": countries,
        }
        ref_tag = " (REF)" if b == REF_BUCKET else ""
        logger.info(
            f"     Bucket {b} ({BUCKET_NAMES[b]}){ref_tag}: "
            f"{n_obs} obs, {n_ent} entities, {n_ctry} countries"
        )

    # --- 2. Within-bucket variation ---
    logger.info(f"\n  2. Within-bucket variation (entity-level std)")
    for b in sorted(BUCKET_NAMES.keys()):
        sub = base[base["bucket"] == b]
        if len(sub) < 2:
            logger.warning(f"     Bucket {b}: insufficient data")
            continue
        grp = sub.groupby(level="entity")
        robots_std = grp["ln_robots_lag1"].std().mean()
        li_std = grp["ln_hours"].std().mean()
        flag = " ⚠ low robot variation" if robots_std < 0.05 else ""
        logger.info(
            f"     Bucket {b}: ln_robots_lag1 mean_std={robots_std:.4f}, "
            f"ln_labour_input mean_std={li_std:.4f}{flag}"
        )

    # --- 3. Institution sub-report ---
    logger.info(f"\n  3. Institution moderator descriptives")

    # Overall
    for var, label in [("coord", "Coord"), ("adjcov", "AdjCov")]:
        if var not in base.columns:
            continue
        vals = base.groupby("country_code")[var].first().dropna()
        if len(vals) == 0:
            logger.info(f"     {label} (overall): no data")
            continue
        logger.info(
            f"     {label} (overall): N_countries={len(vals)}, "
            f"mean={vals.mean():.2f}, SD={vals.std():.2f}, "
            f"min={vals.min():.2f}, max={vals.max():.2f}, "
            f"p10={vals.quantile(0.1):.2f}, p50={vals.quantile(0.5):.2f}, p90={vals.quantile(0.9):.2f}"
        )

    # Per bucket
    logger.info(f"\n  4. Institution descriptives by bucket")
    for b in sorted(BUCKET_NAMES.keys()):
        sub = base[base["bucket"] == b]
        logger.info(f"     --- Bucket {b} ({BUCKET_NAMES[b]}) ---")
        for var, label in [("coord", "Coord"), ("adjcov", "AdjCov")]:
            if var not in sub.columns:
                continue
            vals = sub.groupby("country_code")[var].first().dropna()
            if len(vals) == 0:
                logger.info(f"       {label}: no data")
                continue
            n_distinct = vals.nunique()
            flag = ""
            if var == "coord" and n_distinct < 3:
                flag = " ⚠ <3 distinct values (fragile interaction)"
            if var == "adjcov" and vals.std() < 10:
                flag = " ⚠ SD<10pp (limited leverage for interaction)"
            logger.info(
                f"       {label}: N={len(vals)}, mean={vals.mean():.2f}, "
                f"SD={vals.std():.2f}, range=[{vals.min():.1f}, {vals.max():.1f}], "
                f"distinct={n_distinct}{flag}"
            )

    # --- 5. Binary split check (high_coord) ---
    if "high_coord" in base.columns:
        logger.info(f"\n  5. HighCoord binary split (Coord >= 4)")
        hc = base.dropna(subset=["high_coord"])
        overall_pct = hc["high_coord"].mean() * 100
        logger.info(f"     Overall: {overall_pct:.1f}% high-coord observations")
        for b in sorted(BUCKET_NAMES.keys()):
            sub = hc[hc["bucket"] == b]
            if len(sub) == 0:
                continue
            pct = sub["high_coord"].mean() * 100
            n_ctry_high = sub[sub["high_coord"] == 1]["country_code"].nunique()
            n_ctry_low = sub[sub["high_coord"] == 0]["country_code"].nunique()
            flag = ""
            if pct < 20 or pct > 80:
                flag = " ⚠ fragile split"
            logger.info(
                f"     Bucket {b}: {pct:.1f}% high-coord "
                f"({n_ctry_high} high-coord countries, {n_ctry_low} low-coord countries){flag}"
            )

    # --- Write to file ---
    OUTPUT_PATH.mkdir(exist_ok=True)
    txt_path = OUTPUT_PATH / "institution_diagnostics_by_bucket.txt"
    _write_institution_diagnostics_file(base, txt_path)
    logger.info(f"\n  Institution diagnostics saved: {txt_path}")

    logger.info(f"\n{BAR}\n")
    return bucket_stats


def _write_institution_diagnostics_file(df: pd.DataFrame, path: Path) -> None:
    """Write structured institution diagnostics to a text file."""
    lines = ["Institution Diagnostics by Bucket", "=" * 60, ""]

    for var, label in [("coord", "Coord"), ("adjcov", "AdjCov")]:
        if var not in df.columns:
            continue
        lines.append(f"--- {label} ---")
        vals = df.groupby("country_code")[var].first().dropna()
        if len(vals) > 0:
            lines.append(
                f"Overall: N={len(vals)}, mean={vals.mean():.2f}, SD={vals.std():.2f}, "
                f"min={vals.min():.2f}, max={vals.max():.2f}"
            )
        lines.append("")
        lines.append(f"{'Bucket':<30} {'N_ctry':>6} {'Mean':>8} {'SD':>8} {'Min':>8} {'Max':>8}")
        lines.append("-" * 70)
        for b in sorted(BUCKET_NAMES.keys()):
            sub = df[df["bucket"] == b]
            bvals = sub.groupby("country_code")[var].first().dropna()
            if len(bvals) == 0:
                lines.append(f"{b} {BUCKET_NAMES[b]:<27} {'--':>6}")
                continue
            lines.append(
                f"{b} {BUCKET_NAMES[b]:<27} {len(bvals):>6} {bvals.mean():>8.2f} "
                f"{bvals.std():>8.2f} {bvals.min():>8.2f} {bvals.max():>8.2f}"
            )
        lines.append("")

    if "high_coord" in df.columns:
        lines.append("--- HighCoord binary split ---")
        hc = df.dropna(subset=["high_coord"])
        lines.append(f"{'Bucket':<30} {'%High':>8} {'N_high':>8} {'N_low':>8}")
        lines.append("-" * 55)
        for b in sorted(BUCKET_NAMES.keys()):
            sub = hc[hc["bucket"] == b]
            if len(sub) == 0:
                continue
            pct = sub["high_coord"].mean() * 100
            n_h = sub[sub["high_coord"] == 1]["country_code"].nunique()
            n_l = sub[sub["high_coord"] == 0]["country_code"].nunique()
            lines.append(f"{b} {BUCKET_NAMES[b]:<27} {pct:>7.1f}% {n_h:>8} {n_l:>8}")
        lines.append("")

    path.write_text("\n".join(lines))
