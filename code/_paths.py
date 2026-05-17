from __future__ import annotations

from pathlib import Path


CODE_DIR = Path(__file__).resolve().parent
ROOT_DIR = CODE_DIR.parent
DATA_DIR = ROOT_DIR / "data"
RESULTS_DIR = ROOT_DIR / "results"
RESULTS_CORE_DIR = RESULTS_DIR / "core"
RESULTS_SECONDARY_DIR = RESULTS_DIR / "secondary"
RESULTS_INFERENCE_ROBUSTNESS_DIR = RESULTS_SECONDARY_DIR / "inference_robustness"
RESULTS_TABLES_DIR = RESULTS_DIR / "tables"
RESULTS_LEGACY_KLEMS_DIR = RESULTS_SECONDARY_DIR / "legacy_klems"
RESULTS_EXPLORATION_DIR = RESULTS_DIR / "exploration"
RESULTS_EXPLORATION_TRADE_DIR = RESULTS_EXPLORATION_DIR / "wiod_feasibility"
RESULTS_ARCHIVE_DIR = RESULTS_DIR / "archive"
RESULTS_FIGURES_DIR = RESULTS_DIR / "figures"


def ensure_results_dirs() -> None:
    RESULTS_CORE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_SECONDARY_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_INFERENCE_ROBUSTNESS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_LEGACY_KLEMS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_EXPLORATION_TRADE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
