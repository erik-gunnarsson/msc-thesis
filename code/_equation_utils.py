'''
Shared utilities for equation scripts.

All data comes from 2-cleaning-data.py output (cleaned_data.csv).
No data wrangling here; equation scripts use pre-built vars: adjcov_centered,
high_coord, high_robot_industry.
'''

import sys
from pathlib import Path
from typing import Optional

import pandas as pd

try:
    from linearmodels import PanelOLS
except ImportError:
    PanelOLS = None

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CLEANED_PATH = DATA_DIR / "cleaned_data.csv"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "outputs"

BAR = "═" * 56
SEP = "─" * 56


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


def run_panelols(formula: str, df: pd.DataFrame):
    if PanelOLS is None:
        raise RuntimeError("linearmodels not installed. Run: pip install linearmodels")
    mod = PanelOLS.from_formula(formula, data=df, drop_absorbed=True)
    return mod.fit(cov_type="clustered", cluster_entity=True)


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
    from loguru import logger

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


def run_diagnostics_industry(df_full: pd.DataFrame) -> dict:
    """Sample stats for industry heterogeneity models (high vs low robot industry)."""
    if "high_robot_industry" not in df_full.columns:
        return {}
    base = prepare_panel(df_full)
    ctrl = get_controls(df_full)
    for c in ctrl:
        if c in base.columns:
            base = base.dropna(subset=[c])
    base = base.drop_duplicates(subset=["entity", "year_int"])

    if len(base) == 0:
        return {"baseline": {"n_obs": 0}, "high_robot": {"n_obs": 0}, "low_robot": {"n_obs": 0}}

    high = base[base["high_robot_industry"] == 1]
    low = base[base["high_robot_industry"] == 0]

    def _stats(d, name):
        n_ent = d.index.get_level_values("entity").nunique() if len(d) > 0 else 0
        return {"name": name, "n_obs": len(d), "n_entities": n_ent}

    return {
        "baseline": _stats(base, "baseline"),
        "high_robot": _stats(high, "high_robot_industry"),
        "low_robot": _stats(low, "low_robot_industry"),
    }
