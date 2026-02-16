'''
Script that runs the output for all code 1-7.

• 1-datacheck.py
• 2-cleaning-data.py
• 3-equation1-baseline.py
• 4-equation2-institutional-moderation-coordination.py
• 5-equation3-institutional-moderation-coverage.py
• 6-equation4-industry-heterogeneity-coordination.py
• 7-equation5-industry-heterogeneity-coverage.py

'''

import subprocess
from pathlib import Path
from loguru import logger
from tqdm import tqdm

CODE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CODE_DIR.parent

scripts = [
    "1-datacheck.py",
    "2-cleaning-data.py",
    "3-equation1-baseline.py 2",
    "4-equation2-institutional-moderation-coordination.py 2",
    "5-equation3-institutional-moderation-coverage.py 2",
    "6-equation4-industry-heterogeneity-coordination.py 2",
    "7-equation5-industry-heterogeneity-coverage.py 2",
]

for entry in tqdm(scripts, desc="Running scripts"):
    parts = entry.split()
    script_path = str(CODE_DIR / parts[0])
    cmd = ["python", script_path] + parts[1:]
    logger.info(f"Running {parts[0]}...")
    subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))
    logger.info(f"Completed {parts[0]}")

logger.info("All scripts completed successfully.")