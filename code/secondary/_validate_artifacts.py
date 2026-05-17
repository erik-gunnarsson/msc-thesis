#!/usr/bin/env python3
"""
Validate saved WIOD thesis artifacts for internal consistency (issue #8).

Run from repository root:
  uv run python code/secondary/_validate_artifacts.py

Optional: compare coefficients to a snapshot manifest produced by copying
wiod_first_results_run_manifest.json after a trusted run.

**Pinned regression-test counts:** ``EXPECTED_OBS`` matches the committed
``wiod_first_results_summary.csv`` sample sizes. After a deliberate panel or
sample-rule change, update those integers (and this comment) or validation will
fail until the new baseline is agreed.

**Exploration gate:** ``EXPLORATION_GATE`` points at the Eq. 2b Hawk–Dove gate
Markdown under ``results/exploration/...``. If that file is missing (exploration
not rerun), the checker skips it — use ``results/archive/exploration/...`` for
committed gate text.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import pandas as pd

CODE = Path(__file__).resolve().parent.parent
ROOT = CODE.parent
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

from _paths import (  # noqa: E402
    RESULTS_CORE_DIR,
    RESULTS_EXPLORATION_DIR,
    RESULTS_INFERENCE_ROBUSTNESS_DIR,
    RESULTS_SECONDARY_DIR,
    RESULTS_TABLES_DIR,
)

# Pinned headline N from wiod_first_results_summary — update when sample definition changes intentionally.
EXPECTED_OBS = {
    "EQ1": 2571,
    "EQ2_COORD": 2500,
    "EQ2_ADJCOV": 1685,
    "EQ2_UD": 2356,
}

SECONDARY_ARTIFACTS = [
    RESULTS_SECONDARY_DIR / "exploratory_wiod_eq2b_coord_ud_full_k_continuous_key_terms.csv",
    RESULTS_SECONDARY_DIR / "diagnostic_wiod_eq2_coord_on_eq2b_sample_full_k_continuous_key_terms.csv",
    RESULTS_SECONDARY_DIR / "wiod_common_sample_robustness.csv",
]

SECONDARY_ROBUSTNESS_CSV = [
    RESULTS_SECONDARY_DIR / "wiod_jackknife_eq2_coord.csv",
    RESULTS_SECONDARY_DIR / "wiod_eq2_coord_sample_decomposition.csv",
]

SECONDARY_ROBUSTNESS_MD = [
    RESULTS_SECONDARY_DIR / "wiod_jackknife_eq2_coord.md",
    RESULTS_SECONDARY_DIR / "wiod_eq2_coord_sample_decomposition.md",
]

JACKKNIFE_REQUIRED_COLS = (
    "dropped_country",
    "n_obs",
    "n_entities",
    "n_countries",
    "beta_interaction",
    "se_country_cluster",
    "p_cluster",
    "p_wild",
)

DECOMPOSITION_REQUIRED_COLS = (
    "comparison_id",
    "term",
    "n_countries",
    "n_entities",
    "n_observations",
    "years",
    "coef_country_cluster",
    "p_wild_cluster",
)

TABLE_FILES = [
    RESULTS_TABLES_DIR / "wiod_regression_table_combined.md",
    RESULTS_TABLES_DIR / "wiod_regression_table_combined.tex",
    RESULTS_INFERENCE_ROBUSTNESS_DIR / "wiod_regression_table_combined_clusterstars.md",
    RESULTS_INFERENCE_ROBUSTNESS_DIR / "wiod_regression_table_combined_clusterstars.tex",
]

TABLE_CSV_FILES = [
    RESULTS_TABLES_DIR / "wiod_regression_table_combined.csv",
    RESULTS_INFERENCE_ROBUSTNESS_DIR / "wiod_regression_table_combined_clusterstars.csv",
]

APPENDIX_ROBOT_STOCK_TABLE_FILES = [
    RESULTS_TABLES_DIR / "wiod_regression_table_appendix_robot_stock_ch_inclusive.md",
    RESULTS_TABLES_DIR / "wiod_regression_table_appendix_robot_stock_ch_inclusive.tex",
    RESULTS_INFERENCE_ROBUSTNESS_DIR / "wiod_regression_table_appendix_robot_stock_ch_inclusive_clusterstars.md",
    RESULTS_INFERENCE_ROBUSTNESS_DIR / "wiod_regression_table_appendix_robot_stock_ch_inclusive_clusterstars.tex",
]

APPENDIX_ROBOT_STOCK_TABLE_CSV_FILES = [
    RESULTS_TABLES_DIR / "wiod_regression_table_appendix_robot_stock_ch_inclusive.csv",
    RESULTS_INFERENCE_ROBUSTNESS_DIR / "wiod_regression_table_appendix_robot_stock_ch_inclusive_clusterstars.csv",
]

APPENDIX_ROBOT_STOCK_TABLE_CSV_COLS_MIN = (
    "display_order",
    "row_type",
    "Eq. 1 (log robot stock, incl. CH)",
    "Eq. 2 coord (log robot stock, incl. CH)",
)

COMBINED_TABLE_CSV_COLS_MIN = (
    "display_order",
    "row_type",
    "Eq. 1",
    "Eq. 2 coord",
    "Eq. 2 adjcov",
    "Eq. 2 ud",
)

EXPLORATION_GATE = (
    RESULTS_EXPLORATION_DIR / "wiod_feasibility" / "wiod_eq2b_coord_ud_gate.md"
)

KEY_TERMS_REQUIRED_COLS = (
    "term",
    "coef_country_cluster",
    "se_country_cluster",
    "p_country_cluster",
)

COMMON_SAMPLE_ROBUSTNESS_COLS = (
    "model_id",
    "term",
    "coef_country_cluster",
    "n_observations",
)

FIX_FIRST_RESULTS = (
    "Fix: `uv run python code/core/14_wiod_first_results.py` "
    "(or update committed files if editing output by hand)"
)
FIX_TABLES = "Fix: `uv run python code/core/18_wiod_academic_tables.py` (+ `--star-source cluster` for cluster-stars)"
FIX_SECONDARY = (
    "Fix: rerun exploratory/diagnostic scripts in REPRODUCIBILITY.md steps 5–7, "
    "or `uv run python code/secondary/19_wiod_jackknife.py` for jackknife CSV"
)


def _basename(path_str: str) -> str:
    return Path(path_str.replace("\\", "/")).name


def resolve_core(path_str: str) -> Path:
    """Treat manifest/summary paths as repo-relative filenames under results/core."""
    return RESULTS_CORE_DIR / _basename(path_str)


def _fail(msg: str, *, fix: str | None = None) -> None:
    line = f"[validate] FAIL: {msg}"
    if fix:
        line = f"{line}\n{fix}"
    print(line, file=sys.stderr)


def _ok(msg: str) -> None:
    print(f"[validate] OK: {msg}")


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _float_match(a: float, b: float, *, rtol: float = 1e-9, atol: float = 1e-12) -> bool:
    return math.isclose(float(a), float(b), rel_tol=rtol, abs_tol=atol)


def parse_sample_manifest(text: str) -> dict[str, int | str]:
    obs_m = re.search(r"^\s*Observations:\s*(\d+)\s*$", text, re.MULTILINE | re.IGNORECASE)
    ent_m = re.search(r"^\s*Entities:\s*(\d+)\s*$", text, re.MULTILINE | re.IGNORECASE)
    ctr_m = re.search(
        r"^\s*Countries\s*\(\s*(\d+)\s*\):\s*(.+?)\s*$", text, re.MULTILINE | re.IGNORECASE
    )
    yr_m = re.search(r"^\s*Years:\s*(\d{4}-\d{4})\s*$", text, re.MULTILINE | re.IGNORECASE)
    if not obs_m:
        raise ValueError("missing Observations:")
    if not ent_m:
        raise ValueError("missing Entities:")
    if not ctr_m:
        raise ValueError(r"missing Countries (N):")  # noqa: UP031
    if not yr_m:
        raise ValueError("missing Years:")
    return {
        "n_observations": int(obs_m.group(1)),
        "n_entities": int(ent_m.group(1)),
        "n_countries_declared": int(ctr_m.group(1)),
        "countries_tail": ctr_m.group(2).strip(),
        "years": yr_m.group(1),
    }


def _validate_key_terms_csv(path: Path) -> str | None:
    try:
        df = pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001 — surface parse failures to CI
        return f"{path.name}: pandas read_csv failed: {exc}"
    missing = [c for c in KEY_TERMS_REQUIRED_COLS if c not in df.columns]
    if missing:
        return f"{path.name}: missing columns {missing}"
    if df.empty:
        return f"{path.name}: CSV has no rows"
    return None


def focal_row(df: pd.DataFrame, focal: str) -> pd.Series | None:
    subset = df[df["term"] == focal]
    if subset.empty:
        return None
    return subset.iloc[0]


def _validate_common_sample_csv(path: Path) -> str | None:
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return f"{path.name}: pandas read_csv failed: {exc}"
    missing = [c for c in COMMON_SAMPLE_ROBUSTNESS_COLS if c not in df.columns]
    if missing:
        return f"{path.name}: missing columns {missing}"
    if df.empty:
        return f"{path.name}: CSV has no rows"
    return None


def _validate_jackknife_csv(path: Path) -> str | None:
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return f"{path.name}: pandas read_csv failed: {exc}"
    missing = [c for c in JACKKNIFE_REQUIRED_COLS if c not in df.columns]
    if missing:
        return f"{path.name}: missing columns {missing}"
    if df.empty:
        return f"{path.name}: CSV has no rows"
    return None


def _validate_decomposition_csv(path: Path) -> str | None:
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return f"{path.name}: pandas read_csv failed: {exc}"
    missing = [c for c in DECOMPOSITION_REQUIRED_COLS if c not in df.columns]
    if missing:
        return f"{path.name}: missing columns {missing}"
    if df.empty:
        return f"{path.name}: CSV has no rows"
    return None


def _validate_combined_csv(path: Path) -> str | None:
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return f"{path.name}: pandas read_csv failed: {exc}"
    if df.empty:
        return f"{path.name}: CSV has no data rows"
    missing = [c for c in COMBINED_TABLE_CSV_COLS_MIN if c not in df.columns]
    if missing:
        return f"{path.name}: missing columns {missing}"
    return None



def _validate_appendix_robot_stock_csv(path: Path) -> str | None:
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return f"{path.name}: pandas read_csv failed: {exc}"
    if df.empty:
        return f"{path.name}: CSV has no data rows"
    missing = [c for c in APPENDIX_ROBOT_STOCK_TABLE_CSV_COLS_MIN if c not in df.columns]
    if missing:
        return f"{path.name}: missing columns {missing}"
    return None


def _validate_markdown_nonempty(path: Path) -> str | None:
    body = path.read_text(encoding="utf-8").strip()
    if not body:
        return f"{path.name}: empty markdown"
    return None


def _validate_markdown_table(path: Path) -> str | None:
    body = path.read_text(encoding="utf-8").strip()
    if not body:
        return f"{path.name}: empty file"
    pipe_rows = [ln for ln in body.splitlines() if ln.strip().startswith("|") and ln.count("|") >= 3]
    if len(pipe_rows) < 2:
        return f"{path.name}: expected at least 2 markdown table rows with pipes"
    return None


def _validate_tex_table(path: Path) -> str | None:
    body = path.read_text(encoding="utf-8").strip()
    if not body:
        return f"{path.name}: empty file"
    if "\\begin{tabular" not in body:
        return f"{path.name}: missing tabular environment"
    amp_rows = [ln for ln in body.splitlines() if "&" in ln]
    if not amp_rows:
        return f"{path.name}: no lines containing Tab column separator &"
    if "\\" not in body:
        return f"{path.name}: missing TeX backslash commands"
    return None


def _countries_set_from_manifest_list(s: str) -> set[str]:
    return {c.strip() for c in s.split(",") if c.strip()}


def validate(
    *,
    compare_snapshot: Path | None,
) -> int:
    manifest_path = RESULTS_CORE_DIR / "wiod_first_results_run_manifest.json"
    if not manifest_path.is_file():
        _fail(f"missing {manifest_path}", fix=FIX_FIRST_RESULTS)
        return 1

    manifest = load_manifest(manifest_path)
    br = manifest.get("bootstrap_reps")
    if br != 999:
        _fail(f"bootstrap_reps expected 999, got {br}", fix=FIX_FIRST_RESULTS)
        return 1
    _ok(f"bootstrap_reps={br}")

    if manifest.get("capital_proxy") != "k":
        _fail(
            f"capital_proxy expected k, got {manifest.get('capital_proxy')}",
            fix=FIX_FIRST_RESULTS,
        )
        return 1
    _ok("capital_proxy=k")

    models = manifest.get("models", [])
    by_id = {m["model_id"]: m for m in models}
    for mid, exp_n in EXPECTED_OBS.items():
        if mid not in by_id:
            _fail(f"missing model {mid} in manifest", fix=FIX_FIRST_RESULTS)
            return 1
        n = by_id[mid]["n_observations"]
        if int(n) != exp_n:
            _fail(f"{mid} n_observations expected {exp_n}, got {n}", fix=FIX_FIRST_RESULTS)
            return 1
        years = by_id[mid].get("years")
        if years != "2001-2014":
            _fail(f"{mid} years expected 2001-2014, got {years}", fix=FIX_FIRST_RESULTS)
            return 1
    _ok("core model sample counts and years")

    summary_csv = RESULTS_CORE_DIR / "wiod_first_results_summary.csv"
    if not summary_csv.is_file():
        _fail(f"missing {summary_csv}", fix=FIX_FIRST_RESULTS)
        return 1

    try:
        summary_df = pd.read_csv(summary_csv)
    except Exception as exc:
        _fail(f"wiod_first_results_summary.csv: {exc}", fix=FIX_FIRST_RESULTS)
        return 1

    if "model_id" not in summary_df.columns:
        _fail("wiod_first_results_summary.csv missing model_id column", fix=FIX_FIRST_RESULTS)
        return 1

    summary_by_id = summary_df.drop_duplicates("model_id").set_index("model_id", drop=False)

    for mid in EXPECTED_OBS:
        if mid not in summary_by_id.index:
            _fail(f"summary CSV missing model_id {mid}", fix=FIX_FIRST_RESULTS)
            return 1
        srow = summary_by_id.loc[mid].squeeze()
        if isinstance(srow, pd.DataFrame):
            _fail(f"summary CSV duplicate rows for model_id {mid}", fix=FIX_FIRST_RESULTS)
            return 1

        mm = by_id[mid]
        str_pairs = (
            ("title", mm["title"]),
            ("role", mm["role"]),
            ("output_prefix", mm["output_prefix"]),
            ("sample_mode", mm["sample_mode"]),
            ("focal_term", mm["focal_term"]),
            ("years", mm["years"]),
        )
        for col, mv in str_pairs:
            sv = str(srow[col]).strip() if pd.notna(srow[col]) else ""
            ev = str(mv).strip() if mv is not None else ""
            if sv != ev:
                _fail(f"summary vs manifest mismatch {mid}.{col}: {sv!r} vs {ev!r}", fix=FIX_FIRST_RESULTS)
                return 1

        for col in ("n_countries", "n_entities", "n_observations"):
            if int(srow[col]) != int(mm[col]):
                _fail(f"summary vs manifest mismatch {mid}.{col}", fix=FIX_FIRST_RESULTS)
                return 1

        for col in ("coef_country_cluster", "se_country_cluster", "p_country_cluster"):
            if not _float_match(srow[col], mm[col]):
                _fail(f"summary vs manifest mismatch {mid}.{col}", fix=FIX_FIRST_RESULTS)
                return 1

        for path_key in ("key_terms_file", "results_file", "sample_manifest_file"):
            mpath = mm[path_key]
            exp_name = _basename(str(mpath))
            gpath = resolve_core(str(srow[path_key]))
            if exp_name != gpath.name:
                _fail(f"{mid} manifest/basename mismatch {path_key}", fix=FIX_FIRST_RESULTS)
                return 1
            if not gpath.is_file():
                _fail(f"{mid}: summary points to missing {gpath.name}", fix=FIX_FIRST_RESULTS)
                return 1

    _ok("wiod_first_results_summary.csv consistent with manifest (rows + paths)")

    for mid, exp_n in EXPECTED_OBS.items():
        row = by_id[mid]
        prefix = row["output_prefix"]
        kt = RESULTS_CORE_DIR / f"{prefix}_key_terms.csv"
        tt_csv = RESULTS_CORE_DIR / f"{prefix}_table_terms.csv"
        meta_path = RESULTS_CORE_DIR / f"{prefix}_table_meta.json"
        run_meta_path = RESULTS_CORE_DIR / f"run_metadata_{prefix}.json"
        samp_path = RESULTS_CORE_DIR / f"sample_manifest_{prefix}.txt"

        focal = row["focal_term"]

        if resolve_core(str(row["key_terms_file"])) != kt:
            _fail(f"{mid}: manifest key_terms_file does not resolve to {kt.name}", fix=FIX_FIRST_RESULTS)
            return 1

        rf = resolve_core(str(row["results_file"]))
        if rf.name != f"{prefix}_results.txt":
            _fail(f"{mid}: manifest results_file basename mismatch for {prefix}", fix=FIX_FIRST_RESULTS)
            return 1
        if not rf.is_file():
            _fail(f"missing {rf}", fix=FIX_FIRST_RESULTS)
            return 1

        if resolve_core(str(row["sample_manifest_file"])) != samp_path:
            _fail(f"{mid}: manifest sample_manifest_file does not resolve to {samp_path.name}", fix=FIX_FIRST_RESULTS)
            return 1

        if not kt.is_file():
            _fail(f"missing {kt}", fix=FIX_FIRST_RESULTS)
            return 1
        if not tt_csv.is_file():
            _fail(f"missing {tt_csv}", fix=FIX_FIRST_RESULTS)
            return 1
        if not meta_path.is_file():
            _fail(f"missing {meta_path}", fix=FIX_FIRST_RESULTS)
            return 1

        meta_j = load_manifest(meta_path)
        if meta_j.get("n_observations") != exp_n:
            _fail(f"{prefix} table_meta n_obs mismatch", fix=FIX_FIRST_RESULTS)
            return 1

        mf_countries = _countries_set_from_manifest_list(row["countries_list"])
        meta_cs = meta_j.get("countries")
        if not isinstance(meta_cs, list) or not meta_cs:
            _fail(f"{prefix} table_meta.countries invalid", fix=FIX_FIRST_RESULTS)
            return 1
        if set(meta_cs) != mf_countries:
            _fail(f"{prefix} countries_list vs table_meta.countries mismatch", fix=FIX_FIRST_RESULTS)
            return 1

        fe = meta_j.get("fixed_effects", {})
        if not fe.get("country_industry") or not fe.get("year"):
            _fail(f"{prefix} fixed_effects should include country_industry and year", fix=FIX_FIRST_RESULTS)
            return 1

        if meta_j.get("year_min") != 2001 or meta_j.get("year_max") != 2014:
            _fail(f"{prefix} year range should be 2001-2014 in table_meta", fix=FIX_FIRST_RESULTS)
            return 1

        caps = (((meta_j.get("flags") or {}).get("capital_proxy")) if meta_j else None)
        if caps != "k":
            _fail(f"{prefix} table_meta.flags.capital_proxy expected k, got {caps!r}", fix=FIX_FIRST_RESULTS)
            return 1

        err = _validate_key_terms_csv(kt)
        if err:
            _fail(err, fix=FIX_FIRST_RESULTS)
            return 1

        try:
            kt_df = pd.read_csv(kt)
        except Exception as exc:
            _fail(f"{kt.name}: {exc}", fix=FIX_FIRST_RESULTS)
            return 1
        fk = focal_row(kt_df, focal)
        if fk is None:
            _fail(f"{prefix} key_terms.csv missing focal term row {focal!r}", fix=FIX_FIRST_RESULTS)
            return 1
        if not (
            _float_match(fk["coef_country_cluster"], row["coef_country_cluster"])
            and _float_match(fk["se_country_cluster"], row["se_country_cluster"])
            and _float_match(fk["p_country_cluster"], row["p_country_cluster"])
        ):
            _fail(f"{prefix} manifest focal coef/se/p inconsistent with key_terms row", fix=FIX_FIRST_RESULTS)
            return 1

        err_t = _validate_key_terms_csv(tt_csv)
        if err_t:
            _fail(f"table_terms: {err_t}", fix=FIX_FIRST_RESULTS)
            return 1
        try:
            tt_df = pd.read_csv(tt_csv)
        except Exception as exc:
            _fail(f"{tt_csv.name}: {exc}", fix=FIX_FIRST_RESULTS)
            return 1
        ft = focal_row(tt_df, focal)
        if ft is None:
            _fail(f"{prefix} table_terms.csv missing focal term row {focal!r}", fix=FIX_FIRST_RESULTS)
            return 1
        if not (
            _float_match(ft["coef_country_cluster"], row["coef_country_cluster"])
            and _float_match(ft["se_country_cluster"], row["se_country_cluster"])
            and _float_match(ft["p_country_cluster"], row["p_country_cluster"])
        ):
            _fail(f"{prefix} focal row in table_terms inconsistent with manifest", fix=FIX_FIRST_RESULTS)
            return 1

        if run_meta_path.is_file():
            rj = load_manifest(run_meta_path)
            wf = (((rj.get("flags") or {}).get("wild_cluster_bootstrap_reps")))
            cp = (((rj.get("flags") or {}).get("capital_proxy")))
            obs = rj.get("n_obs")
            if wf != 999:
                _fail(f"{prefix} run_metadata wild_cluster_bootstrap_reps expected 999, got {wf}", fix=FIX_FIRST_RESULTS)
                return 1
            if cp != "k":
                _fail(f"{prefix} run_metadata capital_proxy expected k, got {cp!r}", fix=FIX_FIRST_RESULTS)
                return 1
            if int(obs) != exp_n:
                _fail(f"{prefix} run_metadata n_obs expected {exp_n}, got {obs}", fix=FIX_FIRST_RESULTS)
                return 1
        else:
            _fail(f"missing {run_meta_path}", fix=FIX_FIRST_RESULTS)
            return 1

        if not samp_path.is_file():
            _fail(f"missing {samp_path}", fix=FIX_FIRST_RESULTS)
            return 1
        try:
            sm = parse_sample_manifest(samp_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            _fail(f"{samp_path.name}: {exc}", fix=FIX_FIRST_RESULTS)
            return 1

        if int(sm["n_observations"]) != exp_n or int(sm["n_observations"]) != int(row["n_observations"]):
            _fail(f"{prefix} sample manifest Observations vs manifest", fix=FIX_FIRST_RESULTS)
            return 1
        if int(sm["n_entities"]) != int(row["n_entities"]):
            _fail(f"{prefix} sample manifest Entities vs manifest", fix=FIX_FIRST_RESULTS)
            return 1
        if int(sm["n_countries_declared"]) != int(row["n_countries"]):
            _fail(f"{prefix} sample manifest Countries (N) vs manifest n_countries", fix=FIX_FIRST_RESULTS)
            return 1
        if str(sm["years"]) != "2001-2014":
            _fail(f"{prefix} sample manifest Years mismatch", fix=FIX_FIRST_RESULTS)
            return 1

        sm_countries = _countries_set_from_manifest_list(str(sm["countries_tail"]))
        if sm_countries != mf_countries:
            _fail(f"{prefix} sample manifest country list inconsistent with manifest", fix=FIX_FIRST_RESULTS)
            return 1

    _ok("core model bundles: table_meta, key_terms, table_terms, run_metadata, sample_manifest")

    missing_sec = [p for p in SECONDARY_ARTIFACTS if not p.is_file()]
    if missing_sec:
        for p in missing_sec:
            _fail(f"missing secondary artifact {p}", fix=FIX_SECONDARY)
        return 1
    _ok("secondary diagnostics present")

    for p in SECONDARY_ARTIFACTS:
        if "wiod_common_sample_robustness" in p.name:
            err = _validate_common_sample_csv(p)
        else:
            err = _validate_key_terms_csv(p)
        if err:
            _fail(err, fix=FIX_SECONDARY)
            return 1
    _ok("parsed secondary diagnostics CSV schemas")

    missing_rob = [p for p in SECONDARY_ROBUSTNESS_CSV + SECONDARY_ROBUSTNESS_MD if not p.is_file()]
    if missing_rob:
        for p in missing_rob:
            _fail(f"missing robustness artifact {p}", fix=FIX_SECONDARY)
        return 1
    _ok("robustness jackknife/decomposition artifacts present")

    for p in SECONDARY_ROBUSTNESS_MD:
        err_md = _validate_markdown_nonempty(p)
        if err_md:
            _fail(err_md, fix=FIX_SECONDARY)
            return 1
    err_j = _validate_jackknife_csv(SECONDARY_ROBUSTNESS_CSV[0])
    if err_j:
        _fail(err_j, fix=FIX_SECONDARY)
        return 1
    err_d = _validate_decomposition_csv(SECONDARY_ROBUSTNESS_CSV[1])
    if err_d:
        _fail(err_d, fix=FIX_SECONDARY)
        return 1
    _ok("parsed jackknife + decomposition CSV schemas")

    all_tbl_paths = [*TABLE_FILES, *TABLE_CSV_FILES, *APPENDIX_ROBOT_STOCK_TABLE_FILES, *APPENDIX_ROBOT_STOCK_TABLE_CSV_FILES]
    missing_tbl = [p for p in all_tbl_paths if not p.is_file()]
    if missing_tbl:
        for p in missing_tbl:
            _fail(f"missing table artifact {p}", fix=FIX_TABLES)
        return 1
    _ok("combined + appendix robot-stock table artifacts present (md, tex, csv)")

    for tbl in TABLE_FILES + APPENDIX_ROBOT_STOCK_TABLE_FILES:
        err = (
            _validate_markdown_table(tbl)
            if tbl.suffix.lower() == ".md"
            else _validate_tex_table(tbl)
        )
        if err:
            _fail(err, fix=FIX_TABLES)
            return 1
    for tc in TABLE_CSV_FILES:
        err_csv = _validate_combined_csv(tc)
        if err_csv:
            _fail(err_csv, fix=FIX_TABLES)
            return 1
    for tc in APPENDIX_ROBOT_STOCK_TABLE_CSV_FILES:
        err_csv = _validate_appendix_robot_stock_csv(tc)
        if err_csv:
            _fail(err_csv, fix=FIX_TABLES)
            return 1
    _ok("parsed markdown / TeX structure and combined + appendix CSV columns")

    if EXPLORATION_GATE.is_file():
        _ok(f"Eq. 2b gate note present: {EXPLORATION_GATE.name}")
    else:
        _ok(f"skip exploration gate (not committed): {EXPLORATION_GATE.name}")

    if compare_snapshot and compare_snapshot.is_file():
        snap = load_manifest(compare_snapshot)
        snap_models = {m["model_id"]: m for m in snap.get("models", [])}
        for mid in EXPECTED_OBS:
            a = float(by_id[mid]["coef_country_cluster"])
            b = float(snap_models[mid]["coef_country_cluster"])
            if abs(a - b) > 1e-9:
                _fail(f"{mid} coef drift vs snapshot: {a} vs {b}", fix=FIX_FIRST_RESULTS)
                return 1
            if int(by_id[mid]["n_observations"]) != int(snap_models[mid]["n_observations"]):
                _fail(f"{mid} n_sample drift vs snapshot", fix=FIX_FIRST_RESULTS)
                return 1
        _ok("coefficients and sample counts match snapshot manifest")

    print("[validate] all checks passed.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--compare-snapshot",
        type=Path,
        default=None,
        help="Prior wiod_first_results_run_manifest.json to diff coefs against",
    )
    args = parser.parse_args()
    raise SystemExit(validate(compare_snapshot=args.compare_snapshot))


if __name__ == "__main__":
    main()
