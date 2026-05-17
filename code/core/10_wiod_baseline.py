'''
WIOD Eq. 1 baseline labour-input model.

This is part of the mainline WIOD thesis workflow.

ln(H_EMPE)_ijt = beta1 ln(Robots)_{ijt-1} + X_ijt + alpha_ij + delta_t + eps_ijt

Headline inference:
  - Country-clustered standard errors
  - Wild cluster bootstrap p-value for ln_robots_lag1

Secondary comparisons:
  - Entity-clustered SEs
  - Driscoll-Kraay SEs
'''

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from loguru import logger

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from _paths import RESULTS_CORE_DIR
from _wiod_model_utils import load_or_build_wiod_panel, write_model_bundle
from _wiod_panel_utils import fit_all_inference, get_wiod_controls, prepare_wiod_panel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    # Thesis headline: default K, full 2001–2014. Appendix robustness only: capcomp, exclude-years 2008 2009 (GH #30).
    parser.add_argument(
        "--capital-proxy",
        choices=["k", "capcomp"],
        default="k",
        help="WIOD capital control: K (default) or CAP compensation sensitivity.",
    )
    parser.add_argument(
        "--robot-regressor",
        choices=["intensity", "stock"],
        default="intensity",
        help="Robot regressor: per-worker intensity headline (ln_robots_lag1); stock (ln_robot_stock_lag1) for CH-inclusive appendix pair (GH #29).",
    )
    parser.add_argument(
        "--exclude-years",
        type=int,
        nargs="*",
        default=None,
        help="Optional years to drop from estimation window (e.g. 2008 2009).",
    )
    parser.add_argument(
        "--no-gdp",
        action="store_true",
        help="Omit GDP growth from the control set.",
    )
    parser.add_argument(
        "--bootstrap-reps",
        type=int,
        default=999,
        help="Wild cluster bootstrap repetitions for the key robot coefficient.",
    )
    parser.add_argument(
        "--bootstrap-seed",
        type=int,
        default=123,
        help="Base seed forwarded to wild cluster bootstrap.",
    )
    parser.add_argument(
        "--no-bootstrap-progress",
        action="store_true",
        help="Disable tqdm progress bars during wild cluster bootstrap.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Write results here (default: results/core).",
    )
    parser.add_argument(
        "--prefix-override",
        type=str,
        default=None,
        help="Override output file prefix stem (default: wiod_eq1_baseline_{capital}).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_or_build_wiod_panel()

    robot_col = "ln_robots_lag1" if args.robot_regressor == "intensity" else "ln_robot_stock_lag1"
    out_dir = args.output_dir or RESULTS_CORE_DIR
    prefix_base = args.prefix_override or f"wiod_eq1_baseline_{args.capital_proxy}"
    if args.robot_regressor == "stock" and args.prefix_override is None:
        prefix_base = f"{prefix_base}_robot_stock"

    controls = get_wiod_controls(
        capital_proxy=args.capital_proxy,
        include_gdp=not args.no_gdp,
    )
    require = ["ln_h_empe", robot_col] + controls
    sample = prepare_wiod_panel(
        df,
        require=require,
        sample="full",
        exclude_years=args.exclude_years,
    )
    rhs_terms = [robot_col] + controls

    logger.info(
        "WIOD Eq. 1 baseline sample: "
        f"{len(sample)} obs, {sample['entity'].nunique()} entities, "
        f"{sample['country_code'].nunique()} countries"
    )
    result = fit_all_inference(sample, outcome="ln_h_empe", rhs_terms=rhs_terms)

    write_model_bundle(
        prefix=prefix_base,
        title="WIOD Eq. 1 baseline labour-input model (mainline)",
        result=result,
        rhs_terms=rhs_terms,
        key_terms=[robot_col],
        flags={
            "capital_proxy": args.capital_proxy,
            "robot_regressor": args.robot_regressor,
            "robot_col": robot_col,
            "exclude_years": args.exclude_years,
            "include_gdp": not args.no_gdp,
            "headline_se": "country_cluster",
            "secondary_se": ["entity_cluster", "driscoll_kraay"],
            "wild_cluster_bootstrap_reps": args.bootstrap_reps,
            "bootstrap_seed": args.bootstrap_seed,
        },
        sample_mode="full",
        bootstrap_reps=args.bootstrap_reps,
        bootstrap_seed=args.bootstrap_seed,
        bootstrap_show_progress=not args.no_bootstrap_progress,
        out_dir=out_dir,
        extra_lines=[
            "Outcome: ln_h_empe (WIOD H_EMPE labour-hours proxy)",
            f"Controls: {', '.join(controls)}",
            "Inference: country cluster headline; entity cluster + Driscoll-Kraay comparison",
        ],
    )


if __name__ == "__main__":
    main()
