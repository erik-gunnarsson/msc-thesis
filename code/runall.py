'''
Script that runs the full analysis pipeline (three-channel moderation).

Moderator channels: UD (mainline), Coord (continuous default), AdjCov (restricted).
UD has strongest measurement leverage; AdjCov requires common-sample restriction;
Coord binary (high_coord_pre) is robustness only.

Build:
  1-datacheck.py
  2-build_panel.py
  8-ictwss-triage.py          (diagnostic only)

Baseline:
  3-equation1-baseline.py

Eq2 – Institutional moderation (ud + coord full & common; adjcov common):
  4-equation2-… --moderator ud    --sample full
  4-equation2-… --moderator ud    --sample common
  4-equation2-… --moderator coord --sample full
  4-equation2-… --moderator coord --sample common
  5-equation3-… --moderator adjcov --sample common   (restricted)

Eq4 – Bucket heterogeneity (ud + coord full & common; adjcov common):
  6-equation4-… --moderator ud    --sample full
  6-equation4-… --moderator ud    --sample common
  6-equation4-… --moderator coord --sample full
  6-equation4-… --moderator coord --sample common
  6-equation4-… --moderator adjcov --sample common
  7-equation5-… --moderator adjcov --sample common   (continuous variant)

Usage:
  python code/runall.py              # full pipeline
  python code/runall.py --smoke      # smoke test (data-check + panel build only)
'''

import argparse
import subprocess
from pathlib import Path
from loguru import logger
from tqdm import tqdm

CODE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CODE_DIR.parent

FULL_SCRIPTS = [
    # Build
    "1-datacheck.py",
    "2-build_panel.py",
    "8-ictwss-triage.py",
    # Baseline
    "3-equation1-baseline.py",
    # Eq2: institutional moderation (ud + coord, full & common)
    "4-equation2-institutional-moderation-coordination.py 2 --moderator ud --sample full",
    "4-equation2-institutional-moderation-coordination.py 2 --moderator ud --sample common",
    "4-equation2-institutional-moderation-coordination.py 2 --moderator coord --sample full",
    "4-equation2-institutional-moderation-coordination.py 2 --moderator coord --sample common",
    # Eq3: coverage moderation (adjcov, restricted/common only)
    "5-equation3-institutional-moderation-coverage.py 2 --moderator adjcov --sample common",
    # Eq4: bucket heterogeneity (ud + coord, full & common; adjcov common)
    "6-equation4-bucket-heterogeneity-coordination.py 2 --moderator ud --sample full",
    "6-equation4-bucket-heterogeneity-coordination.py 2 --moderator ud --sample common",
    "6-equation4-bucket-heterogeneity-coordination.py 2 --moderator coord --sample full",
    "6-equation4-bucket-heterogeneity-coordination.py 2 --moderator coord --sample common",
    "6-equation4-bucket-heterogeneity-coordination.py 2 --moderator adjcov --sample common",
    # Eq5: bucket heterogeneity continuous variant (adjcov, common only)
    "7-equation5-bucket-heterogeneity-coverage.py 2 --moderator adjcov --sample common",
]

SMOKE_SCRIPTS = [
    "1-datacheck.py",
    "2-build_panel.py",
    "3-equation1-baseline.py",
]


def main():
    parser = argparse.ArgumentParser(description="Run full thesis pipeline")
    parser.add_argument("--smoke", action="store_true", help="Smoke test mode (data check + build only)")
    args = parser.parse_args()

    scripts = SMOKE_SCRIPTS if args.smoke else FULL_SCRIPTS

    for entry in tqdm(scripts, desc="Running scripts"):
        parts = entry.split()
        script_path = str(CODE_DIR / parts[0])
        cmd = ["python", script_path] + parts[1:]
        logger.info(f"Running {parts[0]}...")
        subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))
        logger.info(f"Completed {parts[0]}")

    logger.info("All scripts completed successfully.")


if __name__ == "__main__":
    main()
