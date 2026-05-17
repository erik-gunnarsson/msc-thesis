"""
CI smoke test: bytecode compile + import critical modules + core script load + panel funnel.

Does not require `data/` — safe for GitHub Actions where data are gitignored.
Run from repository root: `uv run python code/secondary/smoke_test.py`
"""

from __future__ import annotations

import compileall
import importlib.util
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

CODE = Path(__file__).resolve().parent.parent

CORE_ENTRY_SCRIPTS = (
    "09_build_wiod_panel.py",
    "10_wiod_baseline.py",
    "11_wiod_institution_moderation.py",
    "14_wiod_first_results.py",
    "18_wiod_academic_tables.py",
)

SKIP_SUBDIRS = frozenset({"archived", "legacy_klems", "__pycache__"})


def _compile_dir(subpath: str) -> bool:
    base = CODE / subpath
    if not base.is_dir():
        logger.warning("skip missing dir: {}", base)
        return True
    ok = True
    for py in base.rglob("*.py"):
        if any(p in SKIP_SUBDIRS for p in py.parts):
            continue
        if not compileall.compile_file(py, quiet=1):
            ok = False
    return ok


def _load_core_script(py_path: Path) -> None:
    """Execute top-level imports of a numbered ``code/core/*.py`` script."""
    stem = py_path.stem
    safe_name = f"_wiod_ci_smoke_{stem}"
    spec = importlib.util.spec_from_file_location(safe_name, py_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load spec for {py_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[safe_name] = module
    spec.loader.exec_module(module)


def _synthetic_prepare_wiod_panel_funnel() -> None:
    from _wiod_panel_utils import (
        build_fe_formula,
        get_wiod_controls,
        prepare_wiod_panel,
    )

    rows = []
    for y in range(2002, 2006):
        rows.append(
            {
                "country_code": "AT",
                "nace_r2_code": "C10-C12",
                "year": y,
                "year_int": y,
                "entity": "AT_C10-C12",
                "ln_h_empe": 1.0 + 0.01 * y,
                "ln_robots_lag1": 2.0,
                "ln_va_wiod_qi": 3.0,
                "ln_k_wiod": 4.0,
            }
        )
    df = pd.DataFrame(rows)
    controls = get_wiod_controls(capital_proxy="k", include_gdp=False)
    require = ["ln_h_empe", "ln_robots_lag1"] + controls
    prepared = prepare_wiod_panel(df, require=require, sample="full")
    if prepared.empty:
        raise RuntimeError("synthetic prepare_wiod_panel yielded empty frame")
    rhs = ["ln_robots_lag1"] + controls
    formula = build_fe_formula("ln_h_empe", rhs)
    if "ln_robots_lag1" not in formula or "~" not in formula:
        raise RuntimeError(f"unexpected FE formula: {formula}")
    logger.info("[smoke] synthetic panel funnel OK ({} rows)", len(prepared))


def main() -> None:
    if not _compile_dir("core"):
        raise SystemExit(1)
    if not _compile_dir("exploration/wiod_feasibility"):
        raise SystemExit(1)
    if not _compile_dir("secondary"):
        raise SystemExit(1)

    sys.path.insert(0, str(CODE))
    import _paths  # noqa: F401
    import _wiod_model_utils  # noqa: F401
    import _wiod_panel_utils  # noqa: F401

    core_dir = CODE / "core"
    for name in CORE_ENTRY_SCRIPTS:
        py_path = core_dir / name
        if not py_path.is_file():
            logger.error("missing core entry script: {}", py_path)
            raise SystemExit(1)
        logger.info("[smoke] import-loading {}", py_path.name)
        _load_core_script(py_path)

    _synthetic_prepare_wiod_panel_funnel()

    logger.info("[smoke] compile + imports + core loaders + funnel OK")


if __name__ == "__main__":
    main()
