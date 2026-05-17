from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from loguru import logger
from tqdm import tqdm

try:
    from linearmodels import PanelOLS
except ImportError:  # pragma: no cover
    PanelOLS = None

from _paths import (
    DATA_DIR,
    RESULTS_CORE_DIR,
    RESULTS_EXPLORATION_TRADE_DIR,
    ensure_results_dirs,
)
from _shared_utils import (
    BAR,
    MODERATOR_REGISTRY,
)


ROOT_DIR = Path(__file__).resolve().parent.parent
WIOD_PANEL_PATH = DATA_DIR / "cleaned_data_wiod.csv"
WIOD_TRADE_CACHE = RESULTS_EXPLORATION_TRADE_DIR / "wiod_trade_panel.csv"
SEA_PATH = DATA_DIR / "WIOTS_SEA" / "Socio_Economic_Accounts.xlsx"
EXPOSURE_BASELINE_START = 2000
EXPOSURE_BASELINE_END = 2002

WIOD_EUROPE_CANDIDATE_ISO2 = {
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR",
    "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO",
    "SE", "SI", "SK", "UK", "NO", "CH", "TR", "RU", "IC",
}
WIOD_EUROPE_ISO3_TO_ISO2 = {
    "AUT": "AT",
    "BEL": "BE",
    "BGR": "BG",
    "CHE": "CH",
    "CYP": "CY",
    "CZE": "CZ",
    "DEU": "DE",
    "DNK": "DK",
    "ESP": "ES",
    "EST": "EE",
    "FIN": "FI",
    "FRA": "FR",
    "GBR": "UK",
    "GRC": "EL",
    "HRV": "HR",
    "HUN": "HU",
    "ISL": "IC",
    "IRL": "IE",
    "ITA": "IT",
    "LTU": "LT",
    "LUX": "LU",
    "LVA": "LV",
    "MLT": "MT",
    "NLD": "NL",
    "NOR": "NO",
    "POL": "PL",
    "PRT": "PT",
    "ROU": "RO",
    "RUS": "RU",
    "SVK": "SK",
    "SVN": "SI",
    "SWE": "SE",
    "TUR": "TR",
}
EUROSTAT_GEO_TO_ISO2 = {
    "Albania": "AL",
    "Austria": "AT",
    "Belgium": "BE",
    "Bosnia and Herzegovina": "BA",
    "Bulgaria": "BG",
    "Croatia": "HR",
    "Cyprus": "CY",
    "Czechia": "CZ",
    "Czech Republic": "CZ",
    "Denmark": "DK",
    "Estonia": "EE",
    "Finland": "FI",
    "France": "FR",
    "Germany": "DE",
    "Greece": "EL",
    "Hungary": "HU",
    "Iceland": "IC",
    "Ireland": "IE",
    "Italy": "IT",
    "Kosovo*": "XK",
    "Latvia": "LV",
    "Liechtenstein": "LI",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Malta": "MT",
    "Montenegro": "ME",
    "Netherlands": "NL",
    "North Macedonia": "MK",
    "Norway": "NO",
    "Poland": "PL",
    "Portugal": "PT",
    "Romania": "RO",
    "Serbia": "RS",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "Spain": "ES",
    "Sweden": "SE",
    "Switzerland": "CH",
    "Turkey": "TR",
    "Türkiye": "TR",
    "Ukraine": "UA",
    "United Kingdom": "UK",
}
IFR_TO_NACE = {
    "10-12": "C10-C12",
    "13-15": "C13-C15",
    "16": "C16-C18",
    "17-18": "C16-C18",
    "19": "C19",
    "19-22": "C20-C21",
    "20": "C20-C21",
    "20-21": "C20-C21",
    "20-23": "C20-C21",
    "22": "C22-C23",
    "23": "C22-C23",
    "24": "C24-C25",
    "24-25": "C24-C25",
    "25": "C24-C25",
    "26": "C26-C27",
    "26-27": "C26-C27",
    "27": "C26-C27",
    "28": "C28",
    "29": "C29-C30",
    "29-30": "C29-C30",
    "30": "C29-C30",
    "D_other": "C31-C33",
}
SEA_TO_NACE = {
    "C10-C12": "C10-C12",
    "C13-C15": "C13-C15",
    "C16": "C16-C18",
    "C17": "C16-C18",
    "C18": "C16-C18",
    "C19": "C19",
    "C20": "C20-C21",
    "C21": "C20-C21",
    "C22": "C22-C23",
    "C23": "C22-C23",
    "C24": "C24-C25",
    "C25": "C24-C25",
    "C26": "C26-C27",
    "C27": "C26-C27",
    "C28": "C28",
    "C29": "C29-C30",
    "C30": "C29-C30",
    "C31_C32": "C31-C33",
    "C33": "C31-C33",
}


@dataclass
class WiodModelResult:
    headline: object
    entity_clustered: object
    driscoll_kraay: object | None
    formula: str
    panel_formula: str
    sample: pd.DataFrame


def ensure_output_dir() -> None:
    ensure_results_dirs()


def load_wiod_panel(path: Path = WIOD_PANEL_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"WIOD panel not found: {path}")
    df = pd.read_csv(path)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    if "year_int" in df.columns:
        df["year_int"] = pd.to_numeric(df["year_int"], errors="coerce")
    return df


def load_wiod_trade_panel() -> pd.DataFrame:
    if WIOD_TRADE_CACHE.exists():
        return pd.read_csv(WIOD_TRADE_CACHE)

    import importlib.util

    common_path = ROOT_DIR / "code" / "exploration" / "wiod_feasibility" / "_common.py"
    spec = importlib.util.spec_from_file_location("wiod_feasibility_common", common_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load trade-feasibility common module from {common_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    build_wiod_trade_panel = module.build_wiod_trade_panel
    return build_wiod_trade_panel(cache_path=WIOD_TRADE_CACHE)


def load_ifr_panel() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "IFR_karol.csv")
    df["country_code"] = df["country_code"].replace({"GR": "EL"})
    df["industry_code"] = df["industry_code"].astype(str)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["robot_wrkr_stock_95"] = pd.to_numeric(df["robot_wrkr_stock_95"], errors="coerce")
    df["robot_stock"] = pd.to_numeric(df["robot_stock"], errors="coerce")
    df = df[
        df["country_code"].isin(WIOD_EUROPE_CANDIDATE_ISO2)
        & df["industry_code"].isin(IFR_TO_NACE)
        & df["year"].between(2000, 2014)
    ].copy()
    df["nace_r2_code"] = df["industry_code"].map(IFR_TO_NACE)
    df["ln_robots"] = np.log(df["robot_wrkr_stock_95"].replace(0, np.nan))
    df["ln_robots_lag1"] = df.groupby(["country_code", "industry_code"])["ln_robots"].shift(1)
    collapsed = (
        df.groupby(["country_code", "nace_r2_code", "year"], as_index=False)
        .agg(
            robot_wrkr_stock_95=("robot_wrkr_stock_95", "mean"),
            robot_stock=("robot_stock", "mean"),
            ln_robots=("ln_robots", "mean"),
            n_ifr_rows=("industry_code", "size"),
        )
        .sort_values(["country_code", "nace_r2_code", "year"])
        .reset_index(drop=True)
    )
    collapsed["entity_nace"] = collapsed["country_code"] + "_" + collapsed["nace_r2_code"]
    collapsed["ln_robot_stock"] = np.log(collapsed["robot_stock"].replace(0, np.nan))
    collapsed["ln_robots_lag1"] = collapsed.groupby("entity_nace")["ln_robots"].shift(1)
    collapsed["ln_robot_stock_lag1"] = collapsed.groupby("entity_nace")["ln_robot_stock"].shift(1)
    return collapsed.drop(columns=["entity_nace"])


def load_wiod_sea_long() -> pd.DataFrame:
    if not SEA_PATH.exists():
        raise FileNotFoundError(f"Missing WIOD SEA workbook: {SEA_PATH}")
    df = pd.read_excel(SEA_PATH, sheet_name="DATA")
    keep_vars = ["H_EMPE", "VA_QI", "K", "CAP", "GO"]
    df = df[
        df["country"].isin(WIOD_EUROPE_ISO3_TO_ISO2)
        & df["code"].isin(SEA_TO_NACE)
        & df["variable"].isin(keep_vars)
    ].copy()
    long = df.melt(
        id_vars=["country", "variable", "code"],
        value_vars=list(range(2000, 2015)),
        var_name="year",
        value_name="value",
    )
    long["country_code"] = long["country"].map(WIOD_EUROPE_ISO3_TO_ISO2)
    long["nace_r2_code"] = long["code"].map(SEA_TO_NACE)
    long["year"] = pd.to_numeric(long["year"], errors="coerce")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    return long


def build_wiod_sea_panel() -> pd.DataFrame:
    long = load_wiod_sea_long()
    wide = (
        long.groupby(["country_code", "nace_r2_code", "year", "variable"], as_index=False)["value"]
        .sum(min_count=1)
        .pivot(index=["country_code", "nace_r2_code", "year"], columns="variable", values="value")
        .reset_index()
        .sort_values(["country_code", "nace_r2_code", "year"])
        .reset_index(drop=True)
    )
    wide.columns.name = None
    wide["ln_h_empe"] = np.log(pd.to_numeric(wide["H_EMPE"], errors="coerce").clip(lower=0.1))
    wide["ln_va_wiod_qi"] = np.log(pd.to_numeric(wide["VA_QI"], errors="coerce").clip(lower=0.1))
    wide["ln_k_wiod"] = np.log(pd.to_numeric(wide["K"], errors="coerce").clip(lower=0.1))
    wide["ln_capcomp_wiod"] = np.log(pd.to_numeric(wide["CAP"], errors="coerce").clip(lower=0.1))
    wide["expint_current"] = pd.to_numeric(wide["GO"], errors="coerce")
    return wide


def load_ictwss() -> tuple[pd.DataFrame, pd.DataFrame]:
    ict = pd.read_csv(DATA_DIR / "ictwss_institutions.csv")
    ict["country_code"] = ict["iso3"].map(WIOD_EUROPE_ISO3_TO_ISO2)
    ict = ict[ict["country_code"].isin(WIOD_EUROPE_CANDIDATE_ISO2)].copy()
    ict["year"] = pd.to_numeric(ict["year"], errors="coerce")
    candidates = ["Coord", "AdjCov", "UD", "Wstat", "WC", "SPA_signed"]
    for col in candidates:
        if col in ict.columns:
            ict[col] = pd.to_numeric(ict[col], errors="coerce")
            ict.loc[ict[col] == -99, col] = np.nan

    # ICTWSS institutional baseline: country means over 1990–1995 only (pre-sample vs 2001–2014 panel).
    # Timing follows Leibrecht et al. (2023); intentionally not parameterised—no alternate-window appendix loop.
    base = ict[ict["year"].between(1990, 1995)].copy()
    baseline = (
        base.groupby("country_code", as_index=False)
        .agg(
            ud_pre=("UD", _safe_mean),
            coord_pre=("Coord", _safe_mean),
            adjcov_pre=("AdjCov", _safe_mean),
        )
        .sort_values("country_code")
        .reset_index(drop=True)
    )
    for col in ["ud", "coord", "adjcov"]:
        raw = f"{col}_pre"
        baseline[f"has_{col}"] = baseline[raw].notna()
        baseline[f"{col}_pre_c"] = baseline[raw] - baseline[raw].mean()
    baseline["high_coord_pre"] = np.where(
        baseline["coord_pre"].notna(),
        (baseline["coord_pre"] >= 4).astype(int),
        np.nan,
    )

    timevarying = ict[["country_code", "year"]].copy()
    timevarying["ud"] = ict["UD"]
    timevarying["coord"] = ict["Coord"]
    timevarying["adjcov"] = ict["AdjCov"]
    return baseline, timevarying


def load_macro_controls() -> tuple[pd.DataFrame, pd.DataFrame]:
    gdp = pd.read_csv(DATA_DIR / "eurostata_gdp_nama_10_gdp.csv")
    gdp["country_code"] = gdp["geo"].map(EUROSTAT_GEO_TO_ISO2)
    gdp["year"] = pd.to_numeric(gdp["TIME_PERIOD"], errors="coerce")
    gdp["gdp"] = pd.to_numeric(gdp["OBS_VALUE"], errors="coerce")
    gdp = gdp[["country_code", "year", "gdp"]].dropna(subset=["country_code", "year"])
    gdp = gdp[gdp["country_code"].isin(WIOD_EUROPE_CANDIDATE_ISO2)].copy()
    gdp = gdp.groupby(["country_code", "year"], as_index=False)["gdp"].first()
    gdp = gdp.sort_values(["country_code", "year"]).reset_index(drop=True)
    gdp["gdp_growth"] = gdp.groupby("country_code")["gdp"].transform(
        lambda s: np.log(s.clip(lower=0.1)).diff()
    )

    une = pd.read_csv(DATA_DIR / "eurostat_employment_une_rt_a.csv")
    une["country_code"] = une["geo"].map(EUROSTAT_GEO_TO_ISO2)
    une["year"] = pd.to_numeric(une["TIME_PERIOD"], errors="coerce")
    une["unemployment"] = pd.to_numeric(une["OBS_VALUE"], errors="coerce")
    une = une[["country_code", "year", "unemployment"]].dropna(subset=["country_code", "year"])
    une = une[une["country_code"].isin(WIOD_EUROPE_CANDIDATE_ISO2)].copy()
    une = une.groupby(["country_code", "year"], as_index=False)["unemployment"].first()
    return gdp, une


def add_exposure_variables(
    df: pd.DataFrame,
    *,
    baseline_start: int = EXPOSURE_BASELINE_START,
    baseline_end: int = EXPOSURE_BASELINE_END,
) -> pd.DataFrame:
    out = df.copy()
    out["expint_current"] = out["gross_exports_usd_m"] / out["GO"].clip(lower=0.1)

    baseline = (
        out[out["year"].between(baseline_start, baseline_end)]
        .groupby(["country_code", "nace_r2_code"], as_index=False)["expint_current"]
        .mean()
        .rename(columns={"expint_current": "expint_pre_ij"})
    )
    out = out.merge(baseline, on=["country_code", "nace_r2_code"], how="left")

    industry_exp = (
        baseline.groupby("nace_r2_code", as_index=False)["expint_pre_ij"]
        .mean()
        .rename(columns={"expint_pre_ij": "expint_pre_j"})
    )
    median_exp = industry_exp["expint_pre_j"].median()
    industry_exp["exposed_binary"] = (industry_exp["expint_pre_j"] >= median_exp).astype(int)
    industry_exp["exposure_group"] = np.where(industry_exp["exposed_binary"] == 1, "exposed", "sheltered")
    out = out.merge(industry_exp, on="nace_r2_code", how="left")
    return out


def build_wiod_panel() -> pd.DataFrame:
    ifr = load_ifr_panel()
    sea = build_wiod_sea_panel()
    trade = load_wiod_trade_panel()
    baseline, _ = load_ictwss()
    gdp, une = load_macro_controls()

    df = ifr.merge(sea, on=["country_code", "nace_r2_code", "year"], how="inner")
    df = df.merge(trade, on=["country_code", "nace_r2_code", "year"], how="left")
    df = df.merge(gdp[["country_code", "year", "gdp", "gdp_growth"]], on=["country_code", "year"], how="left")
    df = df.merge(une, on=["country_code", "year"], how="left")
    df = df.merge(baseline, on="country_code", how="left")
    df = add_exposure_variables(df)

    df["year_int"] = df["year"].astype(int)
    df["entity"] = df["country_code"] + "_" + df["nace_r2_code"]
    df["panel_source"] = "wiod"

    out_cols = [
        "country_code", "nace_r2_code", "year", "year_int", "entity",
        "robot_wrkr_stock_95", "robot_stock", "ln_robots", "ln_robot_stock",
        "ln_robots_lag1", "ln_robot_stock_lag1", "n_ifr_rows",
        "H_EMPE", "ln_h_empe", "VA_QI", "ln_va_wiod_qi", "K", "ln_k_wiod",
        "CAP", "ln_capcomp_wiod", "GO", "gross_exports_usd_m", "trade_available",
        "expint_current", "expint_pre_ij", "expint_pre_j", "exposed_binary", "exposure_group",
        "gdp", "gdp_growth", "unemployment",
        "ud_pre", "ud_pre_c", "has_ud", "coord_pre", "coord_pre_c", "has_coord",
        "adjcov_pre", "adjcov_pre_c", "has_adjcov", "high_coord_pre",
        "panel_source",
    ]
    out_cols = [col for col in out_cols if col in df.columns]
    return df[out_cols].sort_values(["country_code", "nace_r2_code", "year"]).reset_index(drop=True)


def save_wiod_panel(path: Path = WIOD_PANEL_PATH) -> pd.DataFrame:
    ensure_output_dir()
    panel = build_wiod_panel()
    panel.to_csv(path, index=False)
    logger.info(f"Saved {len(panel)} rows to {path}")
    logger.info(
        f"WIOD panel: {panel['country_code'].nunique()} countries, "
        f"{panel['entity'].nunique()} entities, "
        f"{int(panel['year'].min())}-{int(panel['year'].max())}"
    )
    return panel


def get_wiod_controls(capital_proxy: str = "k", include_gdp: bool = False) -> list[str]:
    controls = ["ln_va_wiod_qi"]
    controls.append("ln_k_wiod" if capital_proxy == "k" else "ln_capcomp_wiod")
    if include_gdp:
        controls.append("gdp_growth")
    return controls


def moderator_to_columns(mod_key: str, coord_mode: str = "continuous") -> tuple[str, str, bool]:
    info = MODERATOR_REGISTRY[mod_key]
    mod_var = info["mod_var"]
    if mod_key == "coord" and coord_mode == "binary":
        return info["binary_var"], info["has_var"], True
    return mod_var, info["has_var"], info["is_binary"]


def apply_wiod_sample_filter(df: pd.DataFrame, sample: str = "full") -> pd.DataFrame:
    if sample == "common" and "has_adjcov" in df.columns:
        before = len(df)
        df = df[df["has_adjcov"]].copy()
        logger.info(f"Common sample filter: {before} -> {len(df)} rows")
    return df


def prepare_wiod_panel(
    df: pd.DataFrame,
    *,
    require: list[str],
    sample: str = "full",
    exclude_years: list[int] | None = None,
) -> pd.DataFrame:
    out = apply_wiod_sample_filter(df.copy(), sample)
    out = out[out["year"].between(2001, 2014)].copy()
    if exclude_years:
        out = out[~out["year_int"].isin(exclude_years)].copy()
        logger.info(f"Excluded years {exclude_years} -> {len(out)} rows remain")
    out = out.dropna(subset=require)
    out = out.drop_duplicates(subset=["entity", "year_int"]).copy()
    return out.sort_values(["entity", "year_int"]).reset_index(drop=True)


def prepare_wiod_joint_coord_ud_sample(
    df: pd.DataFrame,
    *,
    capital_proxy: str = "k",
    include_gdp: bool = True,
) -> tuple[pd.DataFrame, list[str]]:
    controls = get_wiod_controls(capital_proxy=capital_proxy, include_gdp=include_gdp)
    require = ["ln_h_empe", "ln_robots_lag1", "coord_pre_c", "ud_pre_c"] + controls
    sample = prepare_wiod_panel(df, require=require, sample="full")
    if "has_coord" in sample.columns:
        sample = sample[sample["has_coord"]].copy()
    if "has_ud" in sample.columns:
        sample = sample[sample["has_ud"]].copy()
    return sample.reset_index(drop=True), controls


def add_exposure_interactions(df: pd.DataFrame, mod_var: str | None = None) -> list[str]:
    df["lr_exposed"] = df["ln_robots_lag1"] * df["exposed_binary"]
    terms = ["lr_exposed"]
    if mod_var is not None:
        df["lr_mod_exposure"] = df["ln_robots_lag1"] * df[mod_var] * df["exposed_binary"]
        terms.append("lr_mod_exposure")
    return terms


def build_fe_formula(outcome: str, rhs_terms: list[str]) -> str:
    return f"{outcome} ~ {' + '.join(rhs_terms)} + C(entity) + C(year_int)"


def build_panel_formula(outcome: str, rhs_terms: list[str]) -> str:
    return f"{outcome} ~ {' + '.join(rhs_terms)} + EntityEffects + TimeEffects"


def fit_country_clustered(formula: str, df: pd.DataFrame, cluster_col: str = "country_code"):
    return smf.ols(formula, data=df).fit(
        cov_type="cluster",
        cov_kwds={"groups": df[cluster_col]},
    )


def fit_entity_clustered(formula: str, df: pd.DataFrame):
    return smf.ols(formula, data=df).fit(
        cov_type="cluster",
        cov_kwds={"groups": df["entity"]},
    )


def fit_driscoll_kraay(panel_formula: str, df: pd.DataFrame):
    if PanelOLS is None:
        return None
    panel = df.set_index(["entity", "year_int"], drop=False)
    model = PanelOLS.from_formula(panel_formula, data=panel, drop_absorbed=True)
    return model.fit(cov_type="kernel", kernel="bartlett", bandwidth=3)


def fit_all_inference(
    df: pd.DataFrame,
    *,
    outcome: str,
    rhs_terms: list[str],
) -> WiodModelResult:
    formula = build_fe_formula(outcome, rhs_terms)
    panel_formula = build_panel_formula(outcome, rhs_terms)
    headline = fit_country_clustered(formula, df)
    entity_clustered = fit_entity_clustered(formula, df)
    dk = fit_driscoll_kraay(panel_formula, df)
    return WiodModelResult(
        headline=headline,
        entity_clustered=entity_clustered,
        driscoll_kraay=dk,
        formula=formula,
        panel_formula=panel_formula,
        sample=df.copy(),
    )


def wild_cluster_bootstrap_pvalue(
    formula: str,
    restricted_formula: str,
    df: pd.DataFrame,
    *,
    target_param: str,
    reps: int = 99,
    seed: int = 123,
    cluster_col: str = "country_code",
    show_progress: bool = True,
) -> float:
    """Wild-cluster bootstrap p-value (Rademacher weights) for one regression coefficient.

    Implements the restricted-residual wild bootstrap under the null that the
    *target_param* coefficient is zero (Cameron, Gelbach & Miller 2008; see also
    MacKinnon & Webb on few-cluster behaviour). Steps:

    1. Fit **homoskedastic OLS** for the unrestricted model (``formula``) and for
       the restricted model (``restricted_formula``) that omits *target_param*
       from the RHS but is otherwise the same FE structure.
    2. Let ``\\hat y_r`` and ``\\hat u_r`` be restricted fitted values and residuals.
       For each rep, draw ``v_g \\in \\{-1,+1\\}`` i.i.d. for each cluster ``g`` in
       ``cluster_col`` (Rademacher), map to observations ``w``, and set
       ``y* = \\hat y_r + \\hat u_r \\odot w``.
    3. Refit the **unrestricted** design on ``y*`` with **cluster-robust** errors
       (same clustering); compare ``|t*|`` to ``|t|`` from the real-data clustered
       unrestricted fit.
    4. Return the two-sided bootstrap p-value as the fraction of reps with
       ``|t*| \\ge |t|`` (``hits / reps``).

    See also ``build_restricted_formulas`` in ``_wiod_model_utils.py`` for how
    ``restricted_formula`` is constructed per focal term.
    """
    unrestricted = smf.ols(formula, data=df).fit()
    restricted = smf.ols(restricted_formula, data=df).fit()
    observed = smf.ols(formula, data=df).fit(
        cov_type="cluster",
        cov_kwds={"groups": df[cluster_col]},
    )
    obs_t = float(observed.tvalues[target_param])

    X_u = pd.DataFrame(unrestricted.model.exog, columns=unrestricted.model.exog_names, index=df.index)
    clusters = df[cluster_col]
    unique_clusters = clusters.drop_duplicates().tolist()
    rng = np.random.default_rng(seed)

    boot_hits = 0
    iterator: range | tqdm = range(reps)
    if show_progress and reps > 0:
        iterator = tqdm(
            iterator,
            desc=f"Wild bootstrap [{target_param}]",
            unit="rep",
            leave=False,
        )
    for _ in iterator:
        weights = {cluster: rng.choice([-1.0, 1.0]) for cluster in unique_clusters}
        w = clusters.map(weights).to_numpy()
        y_star = restricted.fittedvalues + restricted.resid * w
        res_star = sm.OLS(y_star, X_u).fit(
            cov_type="cluster",
            cov_kwds={"groups": clusters},
        )
        t_star = float(res_star.tvalues[target_param])
        boot_hits += abs(t_star) >= abs(obs_t)

    return boot_hits / reps


def summarise_key_terms(
    result: WiodModelResult,
    *,
    key_terms: list[str],
    restricted_formulas: dict[str, str] | None = None,
    bootstrap_reps: int = 99,
    bootstrap_seed: int = 123,
    bootstrap_show_progress: bool = True,
) -> pd.DataFrame:
    """Tabulate coefficients and p-values; run wild bootstrap where `restricted_formulas` supplies a key.

    Wild bootstrap uses ``seed=bootstrap_seed + idx`` for ``idx`` = position in ``key_terms`` (see
    ``write_model_bundle`` / ``effective_bootstrap_seed_by_term`` in run metadata).
    """
    rows: list[dict[str, object]] = []
    restricted_formulas = restricted_formulas or {}

    for idx, term in enumerate(key_terms):
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
            "p_wild_cluster": np.nan,
        }
        if result.driscoll_kraay is not None and term in result.driscoll_kraay.params.index:
            row["coef_driscoll_kraay"] = float(result.driscoll_kraay.params.get(term, np.nan))
            row["se_driscoll_kraay"] = float(result.driscoll_kraay.std_errors.get(term, np.nan))
            row["p_driscoll_kraay"] = float(result.driscoll_kraay.pvalues.get(term, np.nan))

        restricted = restricted_formulas.get(term)
        if restricted:
            row["p_wild_cluster"] = wild_cluster_bootstrap_pvalue(
                result.formula,
                restricted,
                result.sample,
                target_param=term,
                reps=bootstrap_reps,
                seed=bootstrap_seed + idx,
                show_progress=bootstrap_show_progress,
            )
        rows.append(row)

    return pd.DataFrame(rows)


def write_sample_manifest(
    df: pd.DataFrame,
    tag: str,
    *,
    sample_mode: str = "full",
    out_dir: Path | None = None,
) -> Path:
    ensure_output_dir()
    target_dir = out_dir or RESULTS_CORE_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"sample_manifest_{tag}.txt"
    countries = sorted(df["country_code"].dropna().unique().tolist())
    lines = [
        f"Sample manifest: {tag}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Sample mode: {sample_mode}",
        "=" * 56,
        f"Observations: {len(df)}",
        f"Entities: {df['entity'].nunique()}",
        f"Countries ({len(countries)}): {', '.join(countries)}",
        f"Years: {int(df['year_int'].min())}-{int(df['year_int'].max())}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_run_metadata(
    script_name: str,
    flags: dict[str, object],
    *,
    n_obs: int,
    n_entities: int,
    out_dir: Path | None = None,
) -> Path:
    ensure_output_dir()
    target_dir = out_dir or RESULTS_CORE_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"run_metadata_{Path(script_name).stem}.json"
    try:
        git_hash = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
    except Exception:
        git_hash = "unknown"
    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_hash or "unknown",
        "script": script_name,
        "flags": flags,
        "n_obs": n_obs,
        "n_entities": n_entities,
    }
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return path


def sample_header(df: pd.DataFrame) -> str:
    countries = sorted(df["country_code"].dropna().unique().tolist())
    return (
        f"Sample: {len(df)} obs, {df['entity'].nunique()} entities\n"
        f"Countries ({len(countries)}): {', '.join(countries)}\n"
        f"{'─' * 56}\n"
    )


def control_comparability_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "component": "Outcome",
                "klems_variable": "LAB_QI",
                "wiod_variable": "H_EMPE",
                "comparability": "Same labour-input family, different measure",
                "notes": "KLEMS LAB_QI is quality-adjusted labour services; WIOD H_EMPE is raw employee hours worked.",
            },
            {
                "component": "Output control",
                "klems_variable": "VA_PYP",
                "wiod_variable": "VA_QI",
                "comparability": "Closest analogue / reasonably comparable",
                "notes": "Both are real gross value-added volume measures; base-year/index construction differs across databases.",
            },
            {
                "component": "Capital control",
                "klems_variable": "CAP_QI",
                "wiod_variable": "K",
                "comparability": "Not directly comparable",
                "notes": "KLEMS CAP_QI is capital services volume; WIOD K is nominal capital stock.",
            },
            {
                "component": "Capital control sensitivity",
                "klems_variable": "CAP_QI",
                "wiod_variable": "CAP",
                "comparability": "Not directly comparable",
                "notes": "WIOD CAP is capital compensation, not capital services or capital stock.",
            },
        ]
    )


def _safe_mean(series: pd.Series) -> float | np.nan:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return np.nan
    return float(numeric.mean())
