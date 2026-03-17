"""Convert WIOD .xlsb files to CSV."""

from pathlib import Path

import pandas as pd
from loguru import logger

INPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "WIOTS_in_EXCEL"
OUTPUT_DIR = INPUT_DIR  # same dir; change to INPUT_DIR / "csv" if preferred


def convert_xlsb_to_csv(input_path: Path, output_path: Path) -> None:
    """Convert a single .xlsb file to CSV."""
    df = pd.read_excel(input_path, engine="pyxlsb")
    df.to_csv(output_path, index=False)
    logger.info(f"Converted {input_path.name} -> {output_path.name}")


def main() -> None:
    xlsb_files = sorted(INPUT_DIR.glob("*.xlsb"))
    if not xlsb_files:
        logger.warning(f"No .xlsb files found in {INPUT_DIR}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for path in xlsb_files:
        out_path = OUTPUT_DIR / path.with_suffix(".csv").name
        convert_xlsb_to_csv(path, out_path)

    logger.success(f"Converted {len(xlsb_files)} files to CSV in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
