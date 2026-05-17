"""Thesis-ready WIOD tables/figures → results/figures/. Run: uv run python code/core/21_wiod_thesis_figures_tables.py"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import shutil
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from loguru import logger

CODE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_ROOT))

from _paths import (  # noqa: E402
    RESULTS_ARCHIVE_DIR,
    RESULTS_CORE_DIR,
    RESULTS_EXPLORATION_TRADE_DIR,
    RESULTS_FIGURES_DIR,
    RESULTS_SECONDARY_DIR,
    RESULTS_TABLES_DIR,
    ensure_results_dirs,
)
from _wiod_panel_utils import (  # noqa: E402
    WIOD_PANEL_PATH,
    build_fe_formula,
    get_wiod_controls,
    moderator_to_columns,
    prepare_wiod_panel,
    wild_cluster_unrestricted_coef_draws,
)


def load_academic_tables_module():
    p = Path(__file__).resolve().parent / "18_wiod_academic_tables.py"
    name = "wiod_academic_tables_dyn"
    spec = importlib.util.spec_from_file_location(name, p)
    if spec is None or spec.loader is None:
        raise RuntimeError(p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


AC = load_academic_tables_module()
THESIS_COL_ORDER = ("EQ1", "EQ2_COORD", "EQ2_UD", "EQ2_ADJCOV", "EQ2B")

ROBOT_ROW_KEYS = frozenset(
    {
        "ln_robots_lag1",
        "ln_robots_lag1_coord",
        "ln_robots_lag1_ud",
        "ln_robots_lag1_adjcov",
        "ln_robots_lag1_coord_ud",
    }
)


def mpl_thesis() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "axes.unicode_minus": False,
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
        }
    )


def thesis_specs():
    mp = {s.model_id: s for s in AC.MODEL_SPECS}
    return [replace(mp[i], column_number=j) for j, i in enumerate(THESIS_COL_ORDER, start=1)]


def save_fig(fig, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".pdf"))
    fig.savefig(stem.with_suffix(".png"))
    plt.close(fig)


def png_table(df: pd.DataFrame, stem: Path, title: str | None = None) -> None:
    mpl_thesis()
    fh = max(2.9, 0.38 * (df.shape[0] + (3 if title else 1)))
    fw = max(8.5, min(28.0, 0.85 * df.shape[1] + 5.0))
    fig, ax = plt.subplots(figsize=(fw, fh))
    ax.axis("off")
    t = ax.table(
        cellText=df.astype(str).values,
        colLabels=list(df.columns),
        cellLoc="center",
        loc="center",
    )
    t.auto_set_font_size(False)
    t.set_fontsize(7.9)
    t.scale(1.0, 1.42)
    if title:
        ax.set_title(title, fontsize=10, pad=14)
    stem.with_suffix(".png").parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".png"))
    plt.close(fig)


def eq2_coord_sample() -> pd.DataFrame:
    if not WIOD_PANEL_PATH.exists():
        raise FileNotFoundError(
            f"{WIOD_PANEL_PATH} missing. Run uv run python code/core/09_build_wiod_panel.py"
        )
    raw = pd.read_csv(WIOD_PANEL_PATH)
    mod, has_flag, _ = moderator_to_columns("coord")
    ctl = get_wiod_controls("k", include_gdp=True)
    rq = ["ln_h_empe", "ln_robots_lag1", mod] + ctl
    s = prepare_wiod_panel(raw, require=rq, sample="full")
    if has_flag in s.columns:
        s = s.loc[s[has_flag]]
    return s.reset_index(drop=True)


def tbl1(fig_dir: Path) -> None:
    # Headline Eq. 2 coordination panel (coord + robot + FE controls); ICTWSS
    # centred moderators can be pairwise missing → per-variable counts.
    s = eq2_coord_sample()
    cols = [
        "ln_h_empe",
        "ln_robots",
        "ln_robots_lag1",
        "ln_va_wiod_qi",
        "ln_k_wiod",
        "gdp_growth",
        "coord_pre_c",
        "ud_pre_c",
        "adjcov_pre_c",
    ]
    nr = []
    for var in cols:
        vals_series = pd.to_numeric(s[var], errors="coerce").dropna()
        n_v = len(vals_series)
        indexed = s.loc[vals_series.index]
        wg: list[float] = []
        for _, g in indexed.groupby("entity"):
            xv = pd.to_numeric(g[var], errors="coerce").dropna()
            if len(xv) > 1:
                wg.append(float(np.std(xv, ddof=1)))
        wsd = float(np.mean(wg)) if wg else float("nan")
        nr.append(
            {
                "variable": var,
                "mean": float(vals_series.mean()) if n_v else math.nan,
                "sd": float(vals_series.std(ddof=1)) if n_v > 1 else math.nan,
                "within_CI_sd_mean": wsd,
                "min": float(vals_series.min()) if n_v else math.nan,
                "max": float(vals_series.max()) if n_v else math.nan,
                "N": n_v,
            }
        )
    nd = pd.DataFrame(nr)
    nd.to_csv(fig_dir / "table1_sample_descriptives.csv", index=False)

    panel_n = int(len(s))
    nc, ne = int(s["country_code"].nunique()), int(s["entity"].nunique())
    nn = int(s["nace_r2_code"].nunique()) if "nace_r2_code" in s.columns else 0
    L = [
        r"\begin{table}[!htbp]\centering\begin{threeparttable}",
        r"\caption{Sample composition and descriptive statistics (Eq.\ 2 coordination headline sample)}\label{tab:table1}",
        r"\footnotesize\begin{tabular}{lcccccc}",
        r"\toprule Variable & Mean & SD & WI SD & Min & Max & $N$ \\ \midrule",
    ]
    for _, r in nd.iterrows():
        wi = rf"{r['within_CI_sd_mean']:.4f}" if pd.notna(r["within_CI_sd_mean"]) else ""
        L.append(
            rf"{AC.escape_latex(r['variable'])} & {r['mean']:.4f} & {r['sd']:.4f} & {wi} & "
            + f"{r['min']:.4f} & {r['max']:.4f} & {int(r['N'])}".replace(",", r"\,")
            + r" \\ "
        )
    L += [
        r"\bottomrule\end{tabular}",
        r"\begin{tablenotes}\footnotesize",
        rf"\item Regression panel backbone: $N={panel_n}$, {nc} countries, {ne} entities, "
        rf"years 2001--2014, {nn} NACE aggregates (IFR). ",
        rf"\item Columns use pairwise-complete counts when ICTWSS moderators omit rows; WI SD averages "
        r"within-(country$\times$industry) temporal SD over years.",
        r"\end{tablenotes}\end{threeparttable}\end{table}",
    ]
    (fig_dir / "table1_sample_descriptives.tex").write_text("\n".join(L), encoding="utf-8")
    png_table(nd.rename(columns={"within_CI_sd_mean": "WI SD"}), fig_dir / "renders/table1", "Table 1")


def fig1_coverage(fig_dir: Path) -> None:
    src = RESULTS_ARCHIVE_DIR / "exploration/wiod_feasibility/europe_country_availability_matrix.csv"
    if not src.is_file():
        raise FileNotFoundError(str(src))
    d = pd.read_csv(src).sort_values("country_code")
    mpl_thesis()

    def y_(x):
        return 2 if str(x or "N").upper() == "Y" else 0

    M: list[list[int]] = []
    rows: list[str] = []
    for _, rw in d.iterrows():
        rows.append(str(rw["country_code"]))
        ifr = (
            2
            if str(rw.get("has_ifr_lagged", "N") or "N").upper() == "Y"
            else (1 if str(rw.get("has_ifr_raw", "N") or "N").upper() == "Y" else 0)
        )
        ic = rw.get("has_ictwss_coord"), rw.get("has_ictwss_ud"), rw.get("has_ictwss_adjcov")
        nh = sum(1 for z in ic if str(z or "N").upper() == "Y")
        if nh >= 3:
            iw = 2
        elif nh == 0:
            iw = 0
        else:
            iw = 1
        M.append(
            [
                y_(rw.get("has_wiod_sea")),
                ifr,
                iw,
                y_(rw.get("has_gdp")),
                y_(ic[0]),
                y_(ic[1]),
                y_(ic[2]),
            ]
        )

    arr = np.array(M)
    cmap = mpl.colors.ListedColormap(["#fcfcfc", "#c9c9c9", "#4a4a4a"])
    norm = mpl.colors.BoundaryNorm([-0.5, 0.5, 1.5, 2.5], cmap.N)
    fh, fw = arr.shape[0] * 0.32 + 1.85, 8.9
    fig, ax = plt.subplots(figsize=(fw, fh))
    ax.imshow(arr, cmap=cmap, norm=norm, interpolation="nearest", aspect="auto")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows, fontsize=7.9)
    ax.set_xticks(range(7))
    ax.set_xticklabels(["WIOD", "IFR", "ICTWSS", "GDP", "Coord", "UD", "AdjCov"], fontsize=8.2)
    ax.legend(
        handles=[
            mpatches.Patch(color=cmap(2), label="Avail.", ec="#333333", lw=0.35),
            mpatches.Patch(color=cmap(1), label="Partial", ec="#333333", lw=0.35),
            mpatches.Patch(color=cmap(0), label="Miss.", ec="#333333", lw=0.35),
        ],
        ncol=3,
        fontsize=8.2,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.11),
        frameon=False,
    )
    ax.set_title(
        "Figure 1. European candidate coverage matrix (33 ISO2 codes). "
        r"Greyscale: avail./partial/miss.; IFR partial if extracts exist without lag robots.",
        fontsize=9,
        pad=36,
    )
    fig.subplots_adjust(top=0.83, bottom=0.08, left=0.12, right=0.98)
    save_fig(fig, fig_dir / "figure1_country_coverage_matrix")


def fig2_coord(fig_dir: Path) -> None:
    ct = RESULTS_EXPLORATION_TRADE_DIR / "wiod_eq2b_coord_ud_country_table.csv"
    mj = RESULTS_CORE_DIR / "primary_contribution_eq2_wiod_coord_full_k_continuous_table_meta.json"
    if not ct.exists():
        raise FileNotFoundError(str(ct))
    c = pd.read_csv(ct).sort_values("coord_pre")
    inc = set(json.loads(mj.read_text(encoding="utf-8"))["countries"]) if mj.exists() else set()
    c["included"] = c["country_code"].astype(str).isin(inc)
    mpl_thesis()
    fig, ax = plt.subplots(figsize=(7.2, max(8.0, len(c) * 0.34)))
    cl = np.where(c["included"], "#2f5f8f", "#c4c4c4")
    ax.barh(c["country_code"].astype(str), c["coord_pre"], color=list(cl), ec="#303030", lw=0.35, height=0.71)
    ax.set_xlabel(r"ICTWSS mean coordination baseline (\textit{coord\_pre}), uncensored ICTWSS scale", fontsize=9.5)
    ax.set_title(
        r"Figure 2. Cross-country bargaining coordination heterogeneity." "\n" r"Colour: Eq.\ 2 coord headline sample incl./excl.",
        fontsize=9.9,
    )
    ax.legend(
        handles=[
            mpatches.Patch(facecolor="#2f5f8f", label=r"In Eq.\ 2 coord (25-country headline)"),
            mpatches.Patch(facecolor="#c4c4c4", label="Outside headline sample"),
        ],
        fontsize=8.8,
        loc="lower right",
        framealpha=1.0,
    )
    fig.tight_layout()
    save_fig(fig, fig_dir / "figure2_coord_pre_country_bars")


def row_map_specs():
    mp: dict[str, tuple[str, ...]] = {s.row_key: s.candidate_terms for s in AC.DISPLAY_ROWS if s.use_wild_stars}
    mp["ln_robots_lag1"] = ("ln_robots_lag1",)
    return mp


def tbl2(fig_dir: Path) -> Path:
    sp = thesis_specs()
    cp = "k"
    bds = [AC.load_model_bundle(s, capital_proxy=cp) for s in sp]
    cr, sr = AC.build_display_rows(bds)
    AC.apply_star_source(cr, bds, star_source="wild")
    df = AC.rows_to_dataframe(cr + sr, bds)
    df.to_csv(fig_dir / "table2_main_regression_ordered.csv", index=False)

    labs = [b["spec"].column_label for b in bds]

    rk2cands = row_map_specs()

    def cell_val(m: pd.DataFrame, cands):
        rr = m.loc[m["term"].isin(cands)]
        return rr.iloc[0] if not rr.empty else None

    L = [
        r"\begin{table}[!htbp]\centering\begin{threeparttable}",
        r"\caption{Main WIOD regressions --- thesis ordering}\label{tab:table2}",
        r"\footnotesize\begin{tabular}{l" + "c" * len(bds) + "}",
        r"\toprule ",
        "& " + " & ".join(f"({b['spec'].column_number})" for b in bds) + r" \\ ",
        "& " + " & ".join(AC.escape_latex(z) for z in labs) + r" \\ \midrule",
    ]
    for i, rr in enumerate(cr):
        if rr["row_type"] != "coef":
            continue
        vs = [str(rr.get(ll, "")) for ll in labs]
        L.append(AC.escape_latex(str(rr["row_label"])) + " & " + " & ".join(vs) + r" \\ ")
        sei = cr[i + 1]
        ses = [str(sei.get(ll, "")) for ll in labs]
        L.append(" & " + " & ".join(ses) + r" \\")
        ky = rr["row_key"]
        if ky in ROBOT_ROW_KEYS:
            pc = rk2cands.get(ky, ())
            pcs = []
            for b in bds:
                m = cell_val(b["terms"], pc)
                if m is None:
                    pcs.append("--")
                else:
                    pcs.append(f"{float(m['p_country_cluster']):.4f} / {float(m['p_wild_cluster']):.4f}".replace(",", r"\,"))
            L.append(r"\multicolumn{1}{r}{\scriptsize\itshape $p_{cl}/p_{wb}$}" + " & " + " & ".join(pcs) + r" \\")
            L.append(r"\addlinespace[0.12em]")
    L.append(r"\midrule")
    for ar in sr:
        L.append(AC.escape_latex(str(ar["row_label"])) + " & " + " & ".join(str(ar.get(ll, "")) for ll in labs) + r" \\ ")
    L += [
        r"\bottomrule\end{tabular}",
        r"\begin{tablenotes}\footnotesize\item " + AC.escape_latex(AC.build_notes(bds, star_source="wild")),
        r"\end{tablenotes}\end{threeparttable}\end{table}",
    ]
    px = fig_dir / "table2_main_regression_thesis.tex"
    px.write_text("\n".join(L), encoding="utf-8")
    png_table(df[["row_label"] + labs], fig_dir / "renders/table2", "Table 2 (preview)")
    return px




def term_row_series(df: pd.DataFrame, cand: tuple[str, ...]) -> pd.Series:
    rr = df.loc[df["term"].isin(cand)]
    return rr.iloc[0]


def headline_robot_coefs() -> tuple[float, float]:
    pref = "primary_contribution_eq2_wiod_coord_full_k_continuous"
    t = pd.read_csv(RESULTS_CORE_DIR / f"{pref}_table_terms.csv")
    b1 = term_row_series(t, ("ln_robots_lag1",))
    b2 = term_row_series(t, ("ln_robots_lag1:coord_pre_c",))
    return float(b1["coef_country_cluster"]), float(b2["coef_country_cluster"])


def fig3_marginal(fig_dir: Path, *, boot_reps: int, prog: bool) -> None:
    samp = eq2_coord_sample()
    rhs = ["ln_robots_lag1", "ln_robots_lag1:coord_pre_c"] + get_wiod_controls("k", include_gdp=True)
    formula = build_fe_formula("ln_h_empe", rhs)
    mj = RESULTS_CORE_DIR / "primary_contribution_eq2_wiod_coord_full_k_continuous_table_meta.json"
    seed_co = json.loads(mj.read_text(encoding="utf-8"))["flags"]["effective_bootstrap_seed_by_term"][
        "ln_robots_lag1:coord_pre_c"
    ]

    mpl_thesis()
    draws = wild_cluster_unrestricted_coef_draws(
        formula,
        samp,
        ["ln_robots_lag1", "ln_robots_lag1:coord_pre_c"],
        reps=boot_reps,
        seed=int(seed_co),
        show_progress=prog,
    )

    gx = np.linspace(float(samp["coord_pre_c"].min()), float(samp["coord_pre_c"].max()), 140)
    b1_hat, b2_hat = headline_robot_coefs()
    me_point = b1_hat + b2_hat * gx
    boots = draws[:, 0][:, np.newaxis] + draws[:, 1][:, np.newaxis] * gx[np.newaxis, :]

    fig, ax = plt.subplots(figsize=(7.2, 5.85))
    q02 = np.quantile(boots, 0.025, axis=0)
    q975 = np.quantile(boots, 0.975, axis=0)
    q05 = np.quantile(boots, 0.05, axis=0)
    q95 = np.quantile(boots, 0.95, axis=0)

    ax.fill_between(gx, q02, q975, color="#cdd9eb", alpha=0.55, lw=0, label="Wild boot. 95%")
    ax.fill_between(gx, q05, q95, color="#93b5d8", alpha=0.4, lw=0, label="Wild boot. 90%")
    ax.plot(gx, me_point, color="#173e6f", lw=2.05, label="Point estimate (b1 + b2 * c)")

    ymin = float(me_point.min())
    ymin = min(ymin, float(np.nanmin(q02)))
    ymax = float(me_point.max())
    ymax = max(ymax, float(np.nanmax(q975)))
    yr = ymax - ymin
    ax.set_ylim(ymin - 0.16 * yr, ymax + 0.12 * yr)
    ry_b = ax.get_ylim()[0] + 0.05 * yr
    cc = samp.groupby("country_code")["coord_pre_c"].first().reset_index()
    ax.scatter(
        cc["coord_pre_c"].to_numpy(dtype=float),
        np.full(len(cc), ry_b),
        marker="|",
        s=70,
        color="#2b2b2b",
        linewidths=2.05,
        zorder=14,
        label="Countries (rug)",
        clip_on=False,
    )

    ax.set_xlabel(
        "coord_pre_c (ICTWSS coordination, mean-centred on the Eq. 2 coordination estimation sample)",
        fontsize=9.4,
    )
    ax.set_ylabel(
        "Marginal effect of ln robot intensity on ln employment hours (with fixed effects as estimated)",
        fontsize=9.25,
    )
    ax.axhline(0, color="#6e6e6e", lw=1, ls="-", zorder=0)
    ax.set_title(
        "Figure 3. Robot marginal effects along bargaining coordination;\nbands from unrestricted residual wild-bootstrap draws.",
        fontsize=10.05,
        pad=10,
    )
    lg = ax.legend(loc="upper center", ncol=3, fontsize=8.2, bbox_to_anchor=(0.53, -0.12), frameon=False)
    _ = lg  # lint
    fig.subplots_adjust(bottom=0.26)
    save_fig(fig, fig_dir / "figure3_marginal_effect_robots_by_coord")


def forest_pick(
    label: str, path_terms: Path, term_tuple: tuple[str, ...] = ("ln_robots_lag1:coord_pre_c",)
) -> dict[str, float]:
    tbl = pd.read_csv(path_terms)
    rr = term_row_series(tbl, term_tuple)
    return {
        "label": label,
        "coef": float(rr["coef_country_cluster"]),
        "lo": float(rr["ci95_low_country_cluster"]),
        "hi": float(rr["ci95_high_country_cluster"]),
    }


def csv_row_ci(label: str, row_parsed: pd.Series, *, coef_col="coef_country_cluster", se_col="se_country_cluster"):
    coef = float(row_parsed[coef_col])
    se = float(row_parsed[se_col])
    return {"label": label, "coef": coef, "lo": coef - 1.96 * se, "hi": coef + 1.96 * se}


def fig4_robustness(fig_dir: Path) -> None:
    rob_dir = RESULTS_SECONDARY_DIR / "robustness"
    headline = forest_pick(
        "Eq. 2 coord headline (25 countries)",
        RESULTS_CORE_DIR / "primary_contribution_eq2_wiod_coord_full_k_continuous_table_terms.csv",
        ("ln_robots_lag1:coord_pre_c",),
    )
    hl = headline["coef"]
    rows_list: list[dict[str, float | str]] = [headline]

    cdf = pd.read_csv(RESULTS_SECONDARY_DIR / "wiod_common_sample_robustness.csv")
    cw = cdf.loc[(cdf.model_id.eq("EQ2_COORD_COMMON")) & cdf.term.eq("ln_robots_lag1:coord_pre_c")].iloc[0]
    rows_list.append(
        csv_row_ci("Eq. 2 coord • 23-country common sample • 2356 obs", cw, coef_col="coef_country_cluster")
    )

    rows_list.extend(
        [
            forest_pick("Exclude 2008–2009 (Eq. 2 coord)", rob_dir / "robust_excl0809_eq2_coord_table_terms.csv"),
            forest_pick(
                "Robot stock lag (CH-inclusive) x coordination",
                rob_dir / "robust_robotstock_eq2_coord_table_terms.csv",
                ("ln_robot_stock_lag1:coord_pre_c",),
            ),
            forest_pick(
                "Binary high-coord (>= 4) specification",
                rob_dir / "robust_binarycoord_eq2_coord_table_terms.csv",
                ("ln_robots_lag1:high_coord_pre",),
            ),
            forest_pick(
                "CAP capital proxy substitution (Eq. 2 coord)",
                rob_dir / "robust_capcomp_eq2_coord_table_terms.csv",
            ),
        ]
    )

    mpl_thesis()
    n = len(rows_list)
    fig, ax = plt.subplots(figsize=(7.95, max(7.05, n * 0.68 + 1.55)))
    for i, rr in enumerate(rows_list):
        y = n - i - 1
        ax.plot([rr["lo"], rr["hi"]], [y, y], color="#394d64", lw=7.05, alpha=0.42, solid_capstyle="round")
        ax.scatter([rr["coef"]], [y], marker="D", s=71, color="#17355b", edgecolors="#0c1f37", lw=0.43, zorder=5)
    ax.axvline(0, color="#5c5c5c", lw=1, ls="-", zorder=0)
    ref = hl if abs(hl - 0.012445) <= 5e-3 else 0.0124
    ax.axvline(ref, color="#984444", lw=1.1, ls="--", alpha=0.92, label="Headline ref. (0.0124)")
    ax.set_yticks(np.arange(n))
    ax.set_yticklabels([str(r["label"]) for r in reversed(rows_list)], fontsize=9.18)
    ax.set_xlabel("Coordination interaction coefficient (± country-cluster asymptotic CI)", fontsize=9.55)
    ax.set_title(
        "Figure 4. Coordination interaction coefficient across robustness designs " "(country-cluster 95% CI from reported SEs).",
        fontsize=9.9,
        pad=10,
    )
    ax.legend(loc="lower right", fontsize=8.4)
    fig.tight_layout()
    save_fig(fig, fig_dir / "figure4_robustness_forest_interaction")


def fig5_jackknife(fig_dir: Path) -> None:
    jp = RESULTS_SECONDARY_DIR / "wiod_jackknife_eq2_coord.csv"
    if not jp.exists():
        raise FileNotFoundError(str(jp))
    jdf = pd.read_csv(jp)
    bl = float(jdf.loc[jdf["dropped_country"].eq("BASELINE_NONE_DROPPED"), "beta_interaction"].iloc[0])
    jk = (
        jdf.loc[~jdf["dropped_country"].eq("BASELINE_NONE_DROPPED")]
        .assign(z=lambda d: d["beta_interaction"])
        .sort_values("beta_interaction")
    )

    mpl_thesis()
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(12.9, max(10.8, len(jk) * 0.26 + 3.45)), gridspec_kw={"wspace": 0.18})
    ys = np.arange(len(jk))
    for y, (_, rw) in enumerate(jk.iterrows()):
        coef = float(rw["beta_interaction"])
        se_c = float(rw["se_country_cluster"])
        lo = coef - 1.96 * se_c
        hi = coef + 1.96 * se_c
        ax0.plot([lo, hi], [y, y], lw=10.8, alpha=0.42, solid_capstyle="round", color="#6c8aae")
        ax0.scatter(coef, y, color="#28456e", s=62, zorder=5)
        ax1.scatter(float(rw.get("p_wild", math.nan)), y, color="#842626", s=41, marker="x", lw=2.05)
    ax0.axvline(bl, ls=":", color="#984444", lw=1.2, label=f"Baseline {bl:.5f}")

    codes = jk["dropped_country"].astype(str).tolist()

    ax0.set_yticks(ys)
    ax0.set_yticklabels(codes, fontsize=9.1)
    ax0.axvline(0.0, color="#7b7b7b", lw=1)
    ax0.set_title("Coefficient and cluster 95% intervals", fontsize=10.05)
    ax0.legend(loc="lower right", fontsize=8.88)
    ax0.set_xlabel("Interaction: ln(robots, t-1) × coordination", fontsize=9.58)

    ax1.set_yticks(ys)
    ax1.set_yticklabels([])
    ax1.axvline(0.10, lw=1, ls="--", color="#666666")
    ax1.axvline(0.05, lw=1, ls=":", color="#979797")
    ax1.set_xlabel("Wild-bootstrap p-value (per jackknife refit)", fontsize=9.62)
    ax1.set_title("Wild p-values", fontsize=10.08)
    fig.suptitle(r"Figure 5. Country-wise jackknife (leave-one-country-out, Eq.\ 2 coord).", fontsize=10.92, y=1.019)
    fig.tight_layout()
    save_fig(fig, fig_dir / "figure5_jackknife_eq2_coord")


def tbl3_decomposition(fig_dir: Path) -> None:
    meta_h = json.loads(
        (RESULTS_CORE_DIR / "primary_contribution_eq2_wiod_coord_full_k_continuous_table_meta.json").read_text(
            encoding="utf-8"
        )
    )
    hq = pd.read_csv(RESULTS_CORE_DIR / "primary_contribution_eq2_wiod_coord_full_k_continuous_key_terms.csv")
    hq = hq.loc[hq["term"].eq("ln_robots_lag1:coord_pre_c")].iloc[0]
    h_coef = float(hq["coef_country_cluster"])
    h_se = float(hq["se_country_cluster"])
    h_pc = float(hq["p_country_cluster"])
    h_pw = float(hq["p_wild_cluster"])
    n_h = int(meta_h["n_observations"])

    cdf = pd.read_csv(RESULTS_SECONDARY_DIR / "wiod_common_sample_robustness.csv")
    r_c = cdf.loc[(cdf.model_id.eq("EQ2_COORD_COMMON")) & cdf.term.eq("ln_robots_lag1:coord_pre_c")].iloc[0]
    r_b = cdf.loc[(cdf.model_id.eq("EQ2B_COMMON")) & cdf.term.eq("ln_robots_lag1:coord_pre_c")].iloc[0]

    def pack(row: pd.Series, label: str, n_obs: int) -> dict[str, float | str | int]:
        c = float(row["coef_country_cluster"])
        se = float(row["se_country_cluster"])
        pc = float(row["p_country_cluster"])
        pw = float(row["p_wild_cluster"])
        return {
            "specification": label,
            "N": n_obs,
            "coef": c,
            "SE": se,
            "p_cluster": pc,
            "p_wild": pw,
            "delta_coef": c - h_coef,
            "delta_p_wild": pw - h_pw,
        }

    rows = [
        {
            "specification": "Eq. 2 coord headline (25 countries)",
            "N": n_h,
            "coef": h_coef,
            "SE": h_se,
            "p_cluster": h_pc,
            "p_wild": h_pw,
            "delta_coef": 0.0,
            "delta_p_wild": 0.0,
        },
        pack(r_c, "Eq. 2 coord on coord×UD intersection (23 countries)", int(r_c["n_observations"])),
        pack(r_b, "Eq. 2b joint model — coord term (same 23-country bundle)", int(r_b["n_observations"])),
    ]
    tdf = pd.DataFrame(rows)
    tdf.to_csv(fig_dir / "table3_sample_spec_decomposition.csv", index=False)
    L = [
        r"\begin{table}[!htbp]\centering\begin{threeparttable}",
        r"\caption{Sample versus specification decomposition for the coordination interaction}\label{tab:table3}",
        r"\footnotesize\begin{tabular}{lccccccc}",
        r"\toprule Spec. & $N$ & Coef & SE & $p_{cl}$ & $p_{wb}$ & $\Delta$Coef & $\Delta p_{wb}$ \\ \midrule",
    ]
    for _, z in tdf.iterrows():
        L.append(
            " ".join(
                [
                    AC.escape_latex(str(z["specification"])),
                    "&",
                    str(int(z["N"])),
                    "&",
                    f"{float(z['coef']):.5f}",
                    "&",
                    f"{float(z['SE']):.5f}",
                    "&",
                    f"{float(z['p_cluster']):.4f}",
                    "&",
                    f"{float(z['p_wild']):.4f}",
                    "&",
                    f"{float(z['delta_coef']):+.5f}",
                    "&",
                    f"{float(z['delta_p_wild']):+.4f}",
                    r"\\",
                ]
            )
        )
    L += [r"\bottomrule\end{tabular}", r"\end{threeparttable}\end{table}"]
    (fig_dir / "table3_sample_spec_decomposition.tex").write_text("\n".join(L), encoding="utf-8")
    png_table(
        tdf,
        fig_dir / "renders/table3",
        "Table 3. Sample vs specification decomposition",
    )


def fig6_robot_tiers(fig_dir: Path) -> None:
    samp = eq2_coord_sample()
    if "coord_pre" not in samp.columns or "robot_wrkr_stock_95" not in samp.columns:
        raise KeyError("fig6 needs coord_pre and robot_wrkr_stock_95 in panel")
    cc = samp.groupby("country_code")["coord_pre"].first()
    cut = pd.qcut(cc, q=3, labels=["Low coordination", "Medium coordination", "High coordination"], duplicates="drop")
    tier_map = cut.to_dict()
    work = samp.copy()
    work["tier"] = work["country_code"].map(tier_map)
    work = work.dropna(subset=["tier", "robot_wrkr_stock_95"])
    ser = (
        work.groupby(["year_int", "tier"], as_index=False)["robot_wrkr_stock_95"]
        .mean()
        .sort_values(["tier", "year_int"])
    )

    mpl_thesis()
    fig, ax = plt.subplots(figsize=(8.2, 5.25))
    for tier in ["Low coordination", "Medium coordination", "High coordination"]:
        sub = ser.loc[ser["tier"].eq(tier)].sort_values("year_int")
        if sub.empty:
            continue
        ax.plot(
            sub["year_int"].to_numpy(),
            sub["robot_wrkr_stock_95"].to_numpy(),
            lw=2.15,
            marker="o",
            markersize=3.95,
            label=tier.replace(" coordination", "").replace("Medium", "Med."),
        )
    ax.legend(fontsize=8.92, ncol=3, frameon=False, bbox_to_anchor=(0.53, -0.12), loc="upper center")
    ax.set_xlabel("Year", fontsize=10.05)
    ax.set_ylabel(
        "Mean robots per worker (same level series underlying ln robot intensity regressors)",
        fontsize=9.2,
    )
    ax.set_title(
        r"Figure 6. Adoption paths by coordination tiers (balanced Eq.\ 2 coordination estimation sample)." "\n"
        r"Countries assigned to tertiary bins on \texttt{coord\_pre}.",
        fontsize=9.92,
        pad=10,
    )
    ax.grid(which="major", linestyle=":", lw=0.55, alpha=0.65)
    fig.subplots_adjust(bottom=0.31)
    save_fig(fig, fig_dir / "figure6_robot_intensity_by_coordination_tiers")


def appendix_eq2b_full(fig_dir: Path) -> None:
    pref = RESULTS_SECONDARY_DIR / "exploratory_wiod_eq2b_coord_ud_full_k_continuous"
    tt = pd.read_csv(f"{pref}_table_terms.csv")
    mj = json.loads(Path(f"{pref}_table_meta.json").read_text(encoding="utf-8"))
    labs = []
    ordered = tt["term"].tolist()
    rows_tex = []
    for term in ordered:
        rw = tt.loc[tt["term"].eq(term)].iloc[0]
        pwc = rw["p_wild_cluster"]
        pws_tex = r"---" if pd.isna(pwc) else f"{float(pwc):.4f}"
        rows_tex.append(
            rf"{AC.escape_latex(term)} & {float(rw['coef_country_cluster']):.4f} & ({float(rw['se_country_cluster']):.4f}) & "
            rf"{float(rw['p_country_cluster']):.4f} & {pws_tex} \\"
        )
        labs.append(
            {
                "term": term,
                "coef": float(rw["coef_country_cluster"]),
                "se": float(rw["se_country_cluster"]),
                "p_cluster": float(rw["p_country_cluster"]),
                "p_wild": float(pwc) if pd.notna(pwc) else float("nan"),
            }
        )
    pd.DataFrame(labs).to_csv(fig_dir / "appendix_table_A1_eq2b_full.csv", index=False)
    rest = [
        r"\begin{table}[!htbp]\centering\begin{threeparttable}",
        r"\caption{Appendix Table A1. Full Eq.\ 2b specification (ICTWSS Hawk--Dove extension)}\label{tab:appA1}",
        r"\footnotesize\begin{tabular}{lcccc}",
        r"\toprule Term & Coef & (SE) & $p_{cl}$ & $p_{wb}$ \\ \midrule",
        *rows_tex,
        r"\midrule",
        rf"Observations & \multicolumn{{4}}{{r}}{{{mj['n_observations']}}} \\",
        rf"Countries & \multicolumn{{4}}{{r}}{{{mj['n_countries']}}} \\",
        r"Country-industry FE & \multicolumn{4}{c}{Yes} \\ Year FE & \multicolumn{4}{c}{Yes} \\",
        r"\bottomrule\end{tabular}\end{threeparttable}\end{table}",
    ]
    (fig_dir / "appendix_table_A1_eq2b_full.tex").write_text("\n".join(rest), encoding="utf-8")
    png_table(pd.DataFrame(labs), fig_dir / "renders/appendix_A1", "Appendix A1")


def appendix_common_sample_table(fig_dir: Path) -> None:
    cdf = pd.read_csv(RESULTS_SECONDARY_DIR / "wiod_common_sample_robustness.csv")
    want = [
        ("EQ1_COMMON", "ln_robots_lag1", "Eq. 1"),
        ("EQ2_COORD_COMMON", "ln_robots_lag1:coord_pre_c", "Eq. 2 coord"),
        ("EQ2_UD_COMMON", "ln_robots_lag1:ud_pre_c", "Eq. 2 ud"),
        ("EQ2B_COMMON", "ln_robots_lag1:coord_pre_c", "Eq. 2b joint (coord term)"),
    ]
    recs = []
    L = [
        r"\begin{table}[!htbp]\centering\begin{threeparttable}",
        r"\caption{Appendix Table A2. Common-sample anchor (coord $\times$ UD intersection)}\label{tab:appA2}",
        r"\footnotesize\begin{tabular}{lcccccc}",
        r"\toprule Model & Term & Coef & SE & $p_{cl}$ & $p_{wb}$ & $N$ \\ \midrule",
    ]
    for mid, term, label in want:
        rw = cdf.loc[(cdf.model_id.eq(mid)) & cdf.term.eq(term)].iloc[0]
        recs.append(
            {
                "model": label,
                "term": term,
                "coef": float(rw["coef_country_cluster"]),
                "se": float(rw["se_country_cluster"]),
                "p_cluster": float(rw["p_country_cluster"]),
                "p_wild": float(rw["p_wild_cluster"]),
                "N": int(rw["n_observations"]),
            }
        )
        L.append(
            " ".join(
                [
                    AC.escape_latex(label),
                    "&",
                    AC.escape_latex(term),
                    "&",
                    f"{float(rw['coef_country_cluster']):.5f}",
                    "&",
                    f"{float(rw['se_country_cluster']):.5f}",
                    "&",
                    f"{float(rw['p_country_cluster']):.4f}",
                    "&",
                    f"{float(rw['p_wild_cluster']):.4f}",
                    "&",
                    str(int(rw["n_observations"])),
                    r"\\",
                ]
            )
        )
    L += [r"\bottomrule\end{tabular}\end{threeparttable}\end{table}"]
    pd.DataFrame(recs).to_csv(fig_dir / "appendix_table_A2_common_sample.csv", index=False)
    (fig_dir / "appendix_table_A2_common_sample.tex").write_text("\n".join(L), encoding="utf-8")
    png_table(pd.DataFrame(recs), fig_dir / "renders/appendix_A2", "Appendix A2")


def appendix_robot_stock_copy(fig_dir: Path) -> None:
    src = RESULTS_TABLES_DIR / "wiod_regression_table_appendix_robot_stock_ch_inclusive.tex"
    if not src.exists():
        raise FileNotFoundError(str(src))
    dst = fig_dir / "appendix_table_A3_robot_stock_CH_inclusive.tex"
    shutil.copyfile(src, dst)


def appendix_vif(fig_dir: Path) -> None:
    vif = pd.read_csv(RESULTS_SECONDARY_DIR / "wiod_vif_audit.csv")
    sub = vif.loc[vif["equation"].eq("EQ2B_COORD_UD")].copy()
    sub.to_csv(fig_dir / "appendix_table_A4_vif_eq2b.csv", index=False)
    L = [
        r"\begin{table}[!htbp]\centering",
        r"\caption{Appendix Table A4. FE-style VIF diagnostics (Eq.\ 2b on 23-country intersection)}\label{tab:appA4}",
        r"\footnotesize\begin{tabular}{lccc}\toprule Term & Demeaned regressor & VIF & $N$ \\ \midrule",
    ]
    for _, r in sub.iterrows():
        L.append(
            rf"{AC.escape_latex(str(r['term']))} & {AC.escape_latex(str(r['demeaned_term']))} & {float(r['vif']):.3f} & {int(r['n_obs_used'])} \\"
        )
    L += [r"\bottomrule\end{tabular}\end{table}"]
    (fig_dir / "appendix_table_A4_vif_eq2b.tex").write_text("\n".join(L), encoding="utf-8")
    png_table(sub, fig_dir / "renders/appendix_A4", "Appendix A4 VIF")


def appendix_jackknife_table(fig_dir: Path) -> None:
    jk = pd.read_csv(RESULTS_SECONDARY_DIR / "wiod_jackknife_eq2_coord.csv")
    bl = float(jk.loc[jk["dropped_country"].eq("BASELINE_NONE_DROPPED"), "beta_interaction"].iloc[0])
    out = jk.loc[~jk["dropped_country"].eq("BASELINE_NONE_DROPPED")].copy()
    out["delta_vs_baseline"] = out["beta_interaction"] - bl
    cols = [
        "dropped_country",
        "beta_interaction",
        "se_country_cluster",
        "p_cluster",
        "p_wild",
        "delta_vs_baseline",
    ]
    out[cols].to_csv(fig_dir / "appendix_table_A5_jackknife_full.csv", index=False)
    L = [
        r"\begin{table}[!htbp]\centering\footnotesize",
        r"\caption{Appendix Table A5. Jackknife leave-one-country-out diagnostics}\label{tab:appA5}",
        r"\begin{tabular}{lccccc}",
        r"\toprule Country drop & $\hat\beta_{\times}$ & SE & $p_{cl}$ & $p_{wb}$ & $\Delta \hat\beta$ \\ \midrule",
    ]
    for _, r in out.sort_values("dropped_country").iterrows():
        L.append(
            f"{AC.escape_latex(str(r['dropped_country']))} & "
            f"{float(r['beta_interaction']):.5f} & {float(r['se_country_cluster']):.5f} & "
            f"{float(r['p_cluster']):.4f} & {float(r['p_wild']):.4f} & {float(r['delta_vs_baseline']):+.5f} \\\\",
        )
    L += [
        rf"\bottomrule\end{{tabular}}\par\medskip{{\scriptsize Baseline headline interaction (no drops): {bl:.6f}.}}\end{{table}}",
    ]
    (fig_dir / "appendix_table_A5_jackknife_full.tex").write_text("\n".join(L), encoding="utf-8")
    png_table(out[cols], fig_dir / "renders/appendix_A5", "Appendix A5")


def appendix_seed_audit(fig_dir: Path) -> None:
    b = RESULTS_SECONDARY_DIR / "bootstrap_audit_eq2_coord.csv"
    if not b.exists():
        raise FileNotFoundError(str(b))
    sdf = pd.read_csv(b)
    sdf.to_csv(fig_dir / "appendix_table_A6_bootstrap_seed_audit.csv", index=False)
    L = [
        r"\begin{table}[!htbp]\centering",
        r"\caption{Appendix Table A6. Wild-bootstrap seed audit (Eq.\ 2 coordination interaction)}\label{tab:appA6}",
        r"\footnotesize\begin{tabular}{ccccc}\toprule Base seed & Effective seed & Reps & $p_{wb}$ & CPU s \\ \midrule",
    ]
    for _, r in sdf.iterrows():
        L.append(
            f"{int(r['base_seed'])} & {int(r['effective_seed'])} & {int(r['reps'])} & {float(r['p_wild']):.4f} & {float(r['elapsed_seconds']):.1f} \\\\",
        )
    L += [r"\bottomrule\end{tabular}\end{table}"]
    (fig_dir / "appendix_table_A6_bootstrap_seed_audit.tex").write_text("\n".join(L), encoding="utf-8")
    png_table(sdf, fig_dir / "renders/appendix_A6", "Appendix A6")


def appendix_hawk_dove(fig_dir: Path) -> None:
    mpl_thesis()
    fig, ax = plt.subplots(figsize=(7.4, 6.4))
    ax.axis("off")
    ax.set_xlim(0, 2)
    ax.set_ylim(0, 2)
    r = 0.85
    ax.add_patch(mpatches.Rectangle((0.2, 0.2), r * 2, r * 2, fill=False, lw=1.8, edgecolor="#202020"))
    ax.plot([1.1, 1.1], [0.2, 1.9], color="#202020", lw=1.4)
    ax.plot([0.2, 1.9], [1.1, 1.1], color="#202020", lw=1.4)
    ax.text(0.65, 1.55, r"Coordinated $(C)$", ha="center", fontsize=10.5, fontweight="bold")
    ax.text(1.45, 1.55, r"Uncoordinated $(U)$", ha="center", fontsize=10.5, fontweight="bold")
    ax.text(0.65, 0.65, r"Hawk–Dove A", ha="center", fontsize=9.6)
    ax.text(1.45, 0.65, r"Hawk–Dove B", ha="center", fontsize=9.6)
    ax.text(0.65, 1.18, r"Payoff block: surplus $V$, cost $C$", ha="center", fontsize=9.2)
    ax.text(1.45, 1.18, r"Shift when moving $C \rightarrow U$", ha="center", fontsize=9.2)
    ax.text(0.65, 0.45, r"$(V-C)$ / $(0)$ stylised", ha="center", fontsize=8.9)
    ax.text(1.45, 0.45, r"$(0)$ / $(-C)$ stylised", ha="center", fontsize=8.9)
    ax.set_title("Appendix Figure A1. Stylised Hawk–Dove coordination comparison", fontsize=10.8, pad=18)
    fig.tight_layout()
    save_fig(fig, fig_dir / "appendix_figure_A1_hawk_dove_matrix")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=Path, default=RESULTS_FIGURES_DIR)
    p.add_argument("--bootstrap-reps-marginal", type=int, default=999)
    p.add_argument("--no-bootstrap-progress", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    ensure_results_dirs()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "renders").mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing thesis artefacts to {out}")

    tbl1(out)
    fig1_coverage(out)
    fig2_coord(out)
    tbl2(out)
    fig3_marginal(out, boot_reps=args.bootstrap_reps_marginal, prog=not args.no_bootstrap_progress)
    fig4_robustness(out)
    fig5_jackknife(out)
    tbl3_decomposition(out)
    fig6_robot_tiers(out)

    appendix_eq2b_full(out)
    appendix_common_sample_table(out)
    appendix_robot_stock_copy(out)
    appendix_vif(out)
    appendix_jackknife_table(out)
    appendix_seed_audit(out)
    appendix_hawk_dove(out)

    logger.info("Done.")


if __name__ == "__main__":
    main()

