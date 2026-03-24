'''
Run the main KLEMS thesis pipeline in execution order.

Workflow:
  01_data_check.py
  02_build_klems_panel.py
  03_ictwss_moderator_triage.py          (diagnostic only)
  04_klems_baseline.py
  05_klems_institution_moderation.py     (ud + coord)
  06_klems_adjcov_moderation.py          (restricted-sample AdjCov)
  07_klems_bucket_moderation.py          (main bucket runner)
  08_klems_bucket_adjcov_continuous.py   (continuous AdjCov bucket variant)

Usage:
  python code/00_run_pipeline.py
  python code/00_run_pipeline.py --smoke
'''

import argparse
import subprocess
import sys
from pathlib import Path
from loguru import logger
from tqdm import tqdm

CODE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CODE_DIR.parent

FULL_SCRIPTS = [
    # Build
    "01_data_check.py",
    "02_build_klems_panel.py",
    "03_ictwss_moderator_triage.py",
    # Baseline
    "04_klems_baseline.py",
    # Eq2: institutional moderation (ud + coord, full & common)
    "05_klems_institution_moderation.py 2 --moderator ud --sample full",
    "05_klems_institution_moderation.py 2 --moderator ud --sample common",
    "05_klems_institution_moderation.py 2 --moderator coord --sample full",
    "05_klems_institution_moderation.py 2 --moderator coord --sample common",
    # Eq3: coverage moderation (adjcov, restricted/common only)
    "06_klems_adjcov_moderation.py 2 --moderator adjcov --sample common",
    # Eq4: bucket heterogeneity (ud + coord, full & common; adjcov common)
    "07_klems_bucket_moderation.py 2 --moderator ud --sample full",
    "07_klems_bucket_moderation.py 2 --moderator ud --sample common",
    "07_klems_bucket_moderation.py 2 --moderator coord --sample full",
    "07_klems_bucket_moderation.py 2 --moderator coord --sample common",
    "07_klems_bucket_moderation.py 2 --moderator adjcov --sample common",
    # Eq5: bucket heterogeneity continuous variant (adjcov, common only)
    "08_klems_bucket_adjcov_continuous.py 2 --moderator adjcov --sample common",
]

SMOKE_SCRIPTS = [
    "01_data_check.py",
    "02_build_klems_panel.py",
    "04_klems_baseline.py",
]


def main():
    parser = argparse.ArgumentParser(description="Run full thesis pipeline")
    parser.add_argument("--smoke", action="store_true", help="Smoke test mode (data check + build only)")
    args = parser.parse_args()

    scripts = SMOKE_SCRIPTS if args.smoke else FULL_SCRIPTS

    for entry in tqdm(scripts, desc="Running scripts"):
        parts = entry.split()
        script_path = str(CODE_DIR / parts[0])
        cmd = [sys.executable, script_path] + parts[1:]
        logger.info(f"Running {parts[0]}...")
        subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))
        logger.info(f"Completed {parts[0]}")

    logger.info("All scripts completed successfully.")


if __name__ == "__main__":
    main()
