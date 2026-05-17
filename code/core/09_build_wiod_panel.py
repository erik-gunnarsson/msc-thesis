'''
Build WIOD labour panel for regression analysis.

Creates data/cleaned_data_wiod.csv: country x industry x year panel (2000-2014).
Outcome: ln(H_EMPE) [raw labour hours proxy from WIOD SEA]
Treatment: ln(robot_wrkr_stock_95)_{t-1}
Controls: ln(VA_QI), ln(K) [default capital proxy], ln(CAP) [sensitivity], GDP growth
Institutions: 1990-1995 baseline-frozen ICTWSS measures
Trade-derived exposure fields are retained only for archived and exploratory diagnostics.

This is the mainline WIOD panel used for Eq. 1 and Eq. 2.
Industry controls come from WIOD SEA, not KLEMS.
'''

from pathlib import Path
import sys

from loguru import logger

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from _wiod_panel_utils import WIOD_PANEL_PATH, save_wiod_panel


def main() -> None:
    panel = save_wiod_panel(show_progress=True)
    logger.info(f"Saved WIOD panel to {WIOD_PANEL_PATH}")
    logger.info("Controls source check: WIOD SEA supplies VA_QI, K, and CAP for this panel.")
    logger.info(
        f"Countries: {panel['country_code'].nunique()}, "
        f"Entities: {panel['entity'].nunique()}, "
        f"Years: {int(panel['year'].min())}-{int(panel['year'].max())}"
    )
    logger.info(
        "Non-missing key vars: "
        f"ln_h_empe={panel['ln_h_empe'].notna().sum()}, "
        f"ln_robots_lag1={panel['ln_robots_lag1'].notna().sum()}, "
        f"ln_va_wiod_qi={panel['ln_va_wiod_qi'].notna().sum()}, "
        f"ln_k_wiod={panel['ln_k_wiod'].notna().sum()}, "
        f"ln_capcomp_wiod={panel['ln_capcomp_wiod'].notna().sum()}"
    )
    country_rows = panel.groupby("country_code").size().sort_values(ascending=False)
    logger.info("Country row counts after WIOD merge:\n" + country_rows.to_string())


if __name__ == "__main__":
    main()
