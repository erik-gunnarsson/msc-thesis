'''
Formal gate diagnostics for the WIOD Eq. 2b Hawk-Dove extension.

This script evaluates whether the joint coord x ud moderator distribution is
spread out enough on the exact WIOD estimation sample to support an
exploratory three-way interaction:

ln_h_empe ~ ln_robots_lag1
         + ln_robots_lag1:coord_pre_c
         + ln_robots_lag1:ud_pre_c
         + ln_robots_lag1:coord_pre_c:ud_pre_c
         + controls + FE
'''

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger
from statsmodels.stats.outliers_influence import variance_inflation_factor


ROOT_DIR = Path(__file__).resolve().parents[3]
CODE_DIR = ROOT_DIR / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from _paths import RESULTS_CORE_DIR, RESULTS_EXPLORATION_TRADE_DIR, ensure_results_dirs  # type: ignore
from _wiod_model_utils import load_or_build_wiod_panel  # type: ignore
from _wiod_panel_utils import prepare_wiod_joint_coord_ud_sample  # type: ignore


COUNTRY_TABLE_PATH = RESULTS_EXPLORATION_TRADE_DIR / "wiod_eq2b_coord_ud_country_table.csv"
CELL_COUNTS_PATH = RESULTS_EXPLORATION_TRADE_DIR / "wiod_eq2b_coord_ud_cell_counts.csv"
VIF_PATH = RESULTS_EXPLORATION_TRADE_DIR / "wiod_eq2b_coord_ud_vif.csv"
SCATTER_PATH = RESULTS_EXPLORATION_TRADE_DIR / "wiod_eq2b_coord_ud_scatter.png"
GATE_MD_PATH = RESULTS_EXPLORATION_TRADE_DIR / "wiod_eq2b_coord_ud_gate.md"


def build_country_table(sample: pd.DataFrame) -> pd.DataFrame:
    table = (
        sample.groupby("country_code", as_index=False)
        .agg(
            coord_pre=("coord_pre", "first"),
            ud_pre=("ud_pre", "first"),
            coord_pre_c=("coord_pre_c", "first"),
            ud_pre_c=("ud_pre_c", "first"),
        )
        .sort_values("country_code")
        .reset_index(drop=True)
    )
    return table


def build_cell_counts(country_table: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    ud_median = float(country_table["ud_pre"].median())
    cell = country_table.copy()
    cell["coord_high"] = (cell["coord_pre"] >= 4).astype(int)
    cell["ud_high"] = (cell["ud_pre"] >= ud_median).astype(int)
    cell["cell_label"] = cell.apply(
        lambda row: f"coord_{'high' if row['coord_high'] else 'low'}__ud_{'high' if row['ud_high'] else 'low'}",
        axis=1,
    )
    counts = (
        cell.groupby(["coord_high", "ud_high", "cell_label"], as_index=False)
        .agg(
            n_countries=("country_code", "size"),
            countries=("country_code", lambda s: ", ".join(sorted(s.tolist()))),
        )
        .sort_values(["coord_high", "ud_high"])
        .reset_index(drop=True)
    )
    return counts, ud_median


def write_scatterplot(country_table: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.scatter(country_table["coord_pre"], country_table["ud_pre"], color="#1f4e79", s=55)
    for _, row in country_table.iterrows():
        ax.annotate(
            row["country_code"],
            (row["coord_pre"], row["ud_pre"]),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=9,
        )
    ax.set_title("WIOD Eq. 2b gate: coord vs union density")
    ax.set_xlabel("coord_pre")
    ax.set_ylabel("ud_pre")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(SCATTER_PATH, dpi=200)
    plt.close(fig)


def build_vif_table(sample: pd.DataFrame) -> pd.DataFrame:
    work = sample.copy()
    work["robots_x_coord"] = work["ln_robots_lag1"] * work["coord_pre_c"]
    work["robots_x_ud"] = work["ln_robots_lag1"] * work["ud_pre_c"]
    work["robots_x_coord_ud"] = (
        work["ln_robots_lag1"] * work["coord_pre_c"] * work["ud_pre_c"]
    )

    demeaned_cols: list[str] = []
    for col in ["robots_x_coord", "robots_x_ud", "robots_x_coord_ud"]:
        entity_mean = work.groupby("entity")[col].transform("mean")
        year_mean = work.groupby("year_int")[col].transform("mean")
        overall_mean = work[col].mean()
        dm_col = f"{col}_dm"
        work[dm_col] = work[col] - entity_mean - year_mean + overall_mean
        demeaned_cols.append(dm_col)

    X = work[demeaned_cols].replace([np.inf, -np.inf], np.nan).dropna()
    rows = []
    for idx, col in enumerate(demeaned_cols):
        vif = float(variance_inflation_factor(X.values, idx))
        rows.append(
            {
                "term": col.replace("_dm", ""),
                "demeaned_term": col,
                "vif": vif,
                "n_obs_used": int(len(X)),
            }
        )
    return pd.DataFrame(rows)


def sample_match_note(sample: pd.DataFrame) -> str:
    summary_path = RESULTS_CORE_DIR / "wiod_first_results_summary.csv"
    if not summary_path.exists():
        return "Could not compare against the current Eq. 2 ud support because results/core/wiod_first_results_summary.csv is missing."
    summary = pd.read_csv(summary_path)
    ud_row = summary.loc[summary["model_id"] == "EQ2_UD"]
    if ud_row.empty:
        return "Could not compare against the current Eq. 2 ud support because EQ2_UD is missing from results/core/wiod_first_results_summary.csv."
    ud = ud_row.iloc[0]
    match = (
        int(ud["n_countries"]) == sample["country_code"].nunique()
        and int(ud["n_entities"]) == sample["entity"].nunique()
        and int(ud["n_observations"]) == len(sample)
    )
    status = "matches" if match else "does not match"
    return (
        "Eq. 2b sample benchmark against current Eq. 2 ud support: "
        f"{status} (Eq. 2b = {sample['country_code'].nunique()} countries / "
        f"{sample['entity'].nunique()} entities / {len(sample)} obs; "
        f"Eq. 2 ud = {int(ud['n_countries'])} countries / "
        f"{int(ud['n_entities'])} entities / {int(ud['n_observations'])} obs)."
    )


def gate_status(corr: float, counts: pd.DataFrame, vif_table: pd.DataFrame) -> tuple[str, list[str]]:
    min_cell = int(counts["n_countries"].min())
    max_vif = float(vif_table["vif"].max())
    notes: list[str] = []
    if corr > 0.7 or min_cell <= 1 or max_vif > 30:
        notes.append(
            "Kill signal triggered: severe moderator collinearity, empty/singleton Hawk-Dove cells, or near-collinear three-way term."
        )
        return "STOP", notes
    if corr >= 0.5 or min_cell == 2 or max_vif >= 10:
        notes.append(
            "Proceed with caution: the three-way specification is estimable, but moderator spread or regressor separability is weaker than ideal."
        )
        return "PROCEED WITH CAUTION", notes
    notes.append(
        "Gate passed cleanly: moderator spread is workable, all Hawk-Dove cells are populated, and FE-style VIFs are low."
    )
    return "GO", notes


def main() -> None:
    ensure_results_dirs()
    RESULTS_EXPLORATION_TRADE_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_or_build_wiod_panel()
    sample, controls = prepare_wiod_joint_coord_ud_sample(panel, capital_proxy="k", include_gdp=True)

    country_table = build_country_table(sample)
    country_table.to_csv(COUNTRY_TABLE_PATH, index=False)

    corr = float(country_table[["coord_pre", "ud_pre"]].corr(method="pearson").iloc[0, 1])
    cell_counts, ud_median = build_cell_counts(country_table)
    cell_counts.to_csv(CELL_COUNTS_PATH, index=False)

    write_scatterplot(country_table)

    vif_table = build_vif_table(sample)
    vif_table.to_csv(VIF_PATH, index=False)

    status, notes = gate_status(corr, cell_counts, vif_table)
    gate_lines = [
        "# WIOD Eq. 2b Hawk-Dove Gate",
        "",
        f"Status: **{status}**",
        "",
        "Exact estimation support:",
        f"- Sample: {len(sample)} obs, {sample['entity'].nunique()} entities, {sample['country_code'].nunique()} countries",
        f"- Years: {int(sample['year_int'].min())}-{int(sample['year_int'].max())}",
        f"- Controls: {', '.join(controls)}",
        "",
        "Joint-distribution diagnostics:",
        f"- Pearson corr(coord_pre, ud_pre): `{corr:.3f}`",
        f"- UD median used for binary cell split: `{ud_median:.3f}`",
        f"- Minimum Hawk-Dove cell size: `{int(cell_counts['n_countries'].min())}` countries",
        f"- Max FE-style VIF: `{float(vif_table['vif'].max()):.3f}`",
        "",
        "Decision notes:",
    ]
    gate_lines.extend([f"- {note}" for note in notes])
    gate_lines.extend(
        [
            "",
            "Benchmark check:",
            f"- {sample_match_note(sample)}",
            "",
            "Saved artifacts:",
            f"- `{COUNTRY_TABLE_PATH.name}`",
            f"- `{CELL_COUNTS_PATH.name}`",
            f"- `{VIF_PATH.name}`",
            f"- `{SCATTER_PATH.name}`",
        ]
    )
    GATE_MD_PATH.write_text("\n".join(gate_lines) + "\n", encoding="utf-8")

    logger.info(
        "WIOD Eq. 2b gate complete: "
        f"{len(sample)} obs, {sample['entity'].nunique()} entities, "
        f"{sample['country_code'].nunique()} countries, corr={corr:.3f}, "
        f"min_cell={int(cell_counts['n_countries'].min())}, max_vif={float(vif_table['vif'].max()):.3f}"
    )
    logger.info(f"Country table -> {COUNTRY_TABLE_PATH}")
    logger.info(f"Cell counts -> {CELL_COUNTS_PATH}")
    logger.info(f"VIF table -> {VIF_PATH}")
    logger.info(f"Scatterplot -> {SCATTER_PATH}")
    logger.info(f"Gate summary -> {GATE_MD_PATH}")


if __name__ == "__main__":
    main()
