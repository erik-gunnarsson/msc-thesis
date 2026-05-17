"""
VIF audit for the active WIOD specifications (GH #22).

Computes FE-style variance inflation factors for each non-FE regressor that
enters the headline Eq. 1, Eq. 2 coord, and Eq. 2b coord x ud models. Eq. 2b
includes the full robot block (main effect, both two-way interactions, and
the three-way coord×ud×robot product). To mimic the actual estimated panel,
we two-way demean each regressor by entity and year (consistent with the FE
absorption inside `statsmodels` OLS with `C(entity) + C(year_int)`) before
computing the VIF on the demeaned design.

Outputs
-------
results/secondary/wiod_vif_audit.csv
    columns: equation, term, demeaned_term, vif, n_obs_used
results/secondary/wiod_vif_audit.md
    one-paragraph interpretation + per-equation table.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from statsmodels.stats.outliers_influence import variance_inflation_factor

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from _paths import RESULTS_SECONDARY_DIR
from _wiod_model_utils import load_or_build_wiod_panel
from _wiod_panel_utils import (
    get_wiod_controls,
    moderator_to_columns,
    prepare_wiod_joint_coord_ud_sample,
    prepare_wiod_panel,
)


CSV_PATH = RESULTS_SECONDARY_DIR / "wiod_vif_audit.csv"
MD_PATH = RESULTS_SECONDARY_DIR / "wiod_vif_audit.md"


def two_way_demean(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    new_cols: list[str] = []
    for col in cols:
        entity_mean = out.groupby("entity")[col].transform("mean")
        year_mean = out.groupby("year_int")[col].transform("mean")
        overall_mean = out[col].mean()
        new_col = f"{col}__dm"
        out[new_col] = out[col] - entity_mean - year_mean + overall_mean
        new_cols.append(new_col)
    return out[new_cols].copy()


def compute_vif(sample: pd.DataFrame, terms: list[str], *, equation: str) -> pd.DataFrame:
    work = sample.copy()
    interaction_terms = [t for t in terms if ":" in t or "*" in t]
    interactions_resolved: list[str] = []
    for term in interaction_terms:
        parts = [p.strip() for p in term.replace("*", ":").split(":")]
        if len(parts) == 2:
            left, right = parts
            new_name = f"{left}_x_{right}"
            work[new_name] = work[left] * work[right]
        elif len(parts) == 3:
            a, b, c = parts
            new_name = f"{a}_x_{b}_x_{c}"
            work[new_name] = work[a] * work[b] * work[c]
        else:
            raise ValueError(
                f"Interaction term must have 2 or 3 components separated by ':' or '*'; "
                f"got {len(parts)} in {term!r}"
            )
        interactions_resolved.append(new_name)
    base_terms = [t for t in terms if ":" not in t and "*" not in t]
    all_terms = base_terms + interactions_resolved

    dm = two_way_demean(work, all_terms)
    X = dm.replace([np.inf, -np.inf], np.nan).dropna()
    rows: list[dict[str, object]] = []
    for idx, col in enumerate(X.columns):
        vif = float(variance_inflation_factor(X.values, idx))
        rows.append(
            {
                "equation": equation,
                "term": col.replace("__dm", ""),
                "demeaned_term": col,
                "vif": vif,
                "n_obs_used": int(len(X)),
            }
        )
    return pd.DataFrame(rows)


def build_eq1_sample(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    controls = get_wiod_controls(capital_proxy="k", include_gdp=True)
    require = ["ln_h_empe", "ln_robots_lag1"] + controls
    sample = prepare_wiod_panel(df, require=require, sample="full")
    return sample, ["ln_robots_lag1"] + controls


def build_eq2_coord_sample(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    controls = get_wiod_controls(capital_proxy="k", include_gdp=True)
    mod_var, has_var, _ = moderator_to_columns("coord", "continuous")
    require = ["ln_h_empe", "ln_robots_lag1", mod_var] + controls
    sample = prepare_wiod_panel(df, require=require, sample="full")
    if has_var in sample.columns:
        sample = sample[sample[has_var]].copy()
    terms = [
        "ln_robots_lag1",
        f"ln_robots_lag1:{mod_var}",
    ] + controls
    return sample, terms


def build_eq2b_sample(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    sample, controls = prepare_wiod_joint_coord_ud_sample(
        df, capital_proxy="k", include_gdp=True
    )
    terms = [
        "ln_robots_lag1",
        "ln_robots_lag1:coord_pre_c",
        "ln_robots_lag1:ud_pre_c",
        "ln_robots_lag1:coord_pre_c:ud_pre_c",
    ] + controls
    return sample, terms


def write_markdown(vif_df: pd.DataFrame) -> None:
    max_overall = float(vif_df["vif"].max())
    over_10 = vif_df[vif_df["vif"] > 10]

    interpretive = (
        f"VIFs are computed on two-way demeaned (entity + year) regressors so that the "
        f"reported numbers reflect within-FE collinearity, not the well-known FE-induced "
        f"inflation of raw VIFs. Across all three active specifications the maximum FE-style "
        f"VIF is {max_overall:.2f}."
    )
    if not over_10.empty:
        flagged = ", ".join(
            f"{row.equation}:{row.term} (VIF={row.vif:.2f})"
            for row in over_10.sort_values("vif", ascending=False).itertuples()
        )
        interpretive += f" Rule-of-thumb flag (VIF > 10): {flagged}."

    eq12 = vif_df[vif_df["equation"].isin(["EQ1_BASELINE", "EQ2_COORD"])]
    eq2b = vif_df[vif_df["equation"] == "EQ2B_COORD_UD"]

    if not eq12.empty:
        max_eq12 = float(eq12["vif"].max())
        over10_eq12 = eq12[eq12["vif"] > 10]
        watch_eq12 = eq12[(eq12["vif"] > 5) & (eq12["vif"] <= 10)]
        if over10_eq12.empty and watch_eq12.empty:
            interpretive += (
                f" Eq. 1 and Eq. 2 coord stay well below conventional cutoffs "
                f"(max FE-style VIF {max_eq12:.2f})."
            )
        elif over10_eq12.empty:
            w12 = ", ".join(
                f"{row.term} (VIF={row.vif:.2f})"
                for row in watch_eq12.sort_values("vif", ascending=False).itertuples()
            )
            interpretive += (
                f" Eq. 1 and Eq. 2 coord do not exceed VIF=10; mid-range terms: {w12}."
            )
        else:
            interpretive += (
                " Eq. 1 and/or Eq. 2 coord include terms flagged above the VIF=10 rule of thumb "
                "(see the consolidated list in the previous sentence)."
            )

    if not eq2b.empty:
        max_2b = float(eq2b["vif"].max())
        over10_2b = eq2b[eq2b["vif"] > 10]
        watch_2b = eq2b[(eq2b["vif"] > 5) & (eq2b["vif"] <= 10)]
        if over10_2b.empty and watch_2b.empty:
            interpretive += (
                f" The Eq. 2b coord×ud specification includes the full robot interaction "
                f"block; within-FE VIFs remain modest (max {max_2b:.2f})."
            )
        else:
            interpretive += (
                " The Eq. 2b specification stacks correlated coord×robot, ud×robot, and "
                "three-way terms with the same controls as the headline regressions; FE-style "
                f"VIFs rise in that interaction set (max {max_2b:.2f}), consistent with "
                "substantive overlap among the moderated robot slopes on the joint sample."
            )
            if over10_2b.empty and not watch_2b.empty:
                w2b = ", ".join(
                    f"{row.term} (VIF={row.vif:.2f})"
                    for row in watch_2b.sort_values("vif", ascending=False).itertuples()
                )
                interpretive += f" Eq. 2b mid-range (5 < VIF ≤ 10): {w2b}."

    lines = [
        "# WIOD VIF audit (GH #22)",
        "",
        interpretive,
        "",
        "Definition: each regressor is two-way demeaned by entity and year before "
        "computing the variance inflation factor, mirroring the two-way FE absorption in "
        "the active OLS specifications.",
        "",
    ]
    for equation in vif_df["equation"].unique():
        sub = vif_df[vif_df["equation"] == equation].sort_values("vif", ascending=False)
        lines.extend(
            [
                f"## {equation}",
                "",
                f"n_obs_used = {int(sub['n_obs_used'].iloc[0])}",
                "",
                "| term | VIF |",
                "| --- | ---: |",
            ]
        )
        for _, row in sub.iterrows():
            lines.append(f"| {row['term']} | {float(row['vif']):.3f} |")
        lines.append("")
    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    df = load_or_build_wiod_panel()

    eq1_sample, eq1_terms = build_eq1_sample(df)
    logger.info(
        f"Eq. 1 sample: {len(eq1_sample)} obs, "
        f"{eq1_sample['country_code'].nunique()} countries"
    )
    eq1_vif = compute_vif(eq1_sample, eq1_terms, equation="EQ1_BASELINE")

    eq2_sample, eq2_terms = build_eq2_coord_sample(df)
    logger.info(
        f"Eq. 2 coord sample: {len(eq2_sample)} obs, "
        f"{eq2_sample['country_code'].nunique()} countries"
    )
    eq2_vif = compute_vif(eq2_sample, eq2_terms, equation="EQ2_COORD")

    eq2b_sample, eq2b_terms = build_eq2b_sample(df)
    logger.info(
        f"Eq. 2b coord x ud sample: {len(eq2b_sample)} obs, "
        f"{eq2b_sample['country_code'].nunique()} countries"
    )
    eq2b_vif = compute_vif(eq2b_sample, eq2b_terms, equation="EQ2B_COORD_UD")

    vif_df = pd.concat([eq1_vif, eq2_vif, eq2b_vif], ignore_index=True)
    vif_df.to_csv(CSV_PATH, index=False)
    logger.info(f"Wrote {CSV_PATH}")
    write_markdown(vif_df)
    logger.info(f"Wrote {MD_PATH}")
    logger.info(f"Max FE-style VIF across all equations: {vif_df['vif'].max():.3f}")


if __name__ == "__main__":
    main()
