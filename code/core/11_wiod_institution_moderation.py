'''
WIOD institutional moderation on labour input.

This script runs the active institutional specifications on the WIOD panel:
coord as the focal channel, adjcov as the secondary focal restricted-sample
channel, and ud as a reference benchmark.

ln(H_EMPE)_ijt = beta1 ln(Robots)_{ijt-1}
               + beta2 [ln(Robots)_{ijt-1} x M_c]
               + X_ijt + alpha_ij + delta_t + eps_ijt

Headline inference:
  - Country-clustered standard errors
  - Wild cluster bootstrap p-values for the robot and interaction terms

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
from _shared_utils import get_moderator, moderator_role_summary
from _wiod_model_utils import load_or_build_wiod_panel, write_model_bundle
from _wiod_panel_utils import (
    fit_all_inference,
    get_wiod_controls,
    moderator_to_columns,
    prepare_wiod_panel,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    # Thesis headline: default K, full 2001–2014. Appendix robustness only: capcomp, exclude-years 2008 2009 (GH #30).
    parser.add_argument(
        "--moderator",
        choices=["coord", "adjcov", "ud"],
        default="coord",
        help="Institutional moderator.",
    )
    parser.add_argument(
        "--sample",
        choices=["full", "common"],
        default="full",
        help="Use full sample or adjcov-common sample.",
    )
    parser.add_argument(
        "--coord-mode",
        choices=["continuous", "binary"],
        default="continuous",
        help="Binary coord is a robustness recode (Coord >= 4).",
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
        "--capital-proxy",
        choices=["k", "capcomp"],
        default="k",
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
        help="Wild cluster bootstrap repetitions for the key terms.",
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
        help="Override output file prefix stem.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.moderator == "adjcov" and args.sample != "common":
        logger.info("Forcing common sample for adjcov models")
        args.sample = "common"

    df = load_or_build_wiod_panel()
    mod_info = get_moderator(args.moderator)
    mod_var, has_var, is_binary = moderator_to_columns(args.moderator, args.coord_mode)
    controls = get_wiod_controls(
        capital_proxy=args.capital_proxy,
        include_gdp=not args.no_gdp,
    )
    robot_col = "ln_robots_lag1" if args.robot_regressor == "intensity" else "ln_robot_stock_lag1"
    require = ["ln_h_empe", robot_col, mod_var] + controls
    sample = prepare_wiod_panel(
        df,
        require=require,
        sample=args.sample,
        exclude_years=args.exclude_years,
    )
    if has_var in sample.columns:
        sample = sample[sample[has_var]].copy()

    interaction_term = f"{robot_col}:{mod_var}"
    rhs_terms = [robot_col, interaction_term] + controls
    prefix_root = {
        "primary": "primary_contribution_eq2_wiod",
        "secondary": "secondary_focal_eq2_wiod",
        "reference": "reference_benchmark_eq2_wiod",
    }.get(mod_info.get("workflow_tier"), "institutional_eq2_wiod")

    default_prefix = f"{prefix_root}_{args.moderator}_{args.sample}_{args.capital_proxy}_{args.coord_mode}"
    if args.robot_regressor == "stock":
        default_prefix = f"{default_prefix}_robot_stock"
    prefix_out = args.prefix_override or default_prefix
    out_dir = args.output_dir or RESULTS_CORE_DIR

    logger.info(
        "WIOD Eq. 2 institutional sample: "
        f"{len(sample)} obs, {sample['entity'].nunique()} entities, "
        f"{sample['country_code'].nunique()} countries"
    )
    logger.info(f"Moderator role: {moderator_role_summary(args.moderator)}")
    result = fit_all_inference(sample, outcome="ln_h_empe", rhs_terms=rhs_terms)

    write_model_bundle(
        prefix=prefix_out,
        title=f"WIOD Eq. 2 institutional moderation: {mod_info['label']} ({mod_info['role_label']})",
        result=result,
        rhs_terms=rhs_terms,
        key_terms=[robot_col, interaction_term],
        flags={
            "moderator": args.moderator,
            "sample": args.sample,
            "coord_mode": args.coord_mode,
            "capital_proxy": args.capital_proxy,
            "robot_regressor": args.robot_regressor,
            "robot_col": robot_col,
            "exclude_years": args.exclude_years,
            "include_gdp": not args.no_gdp,
            "moderator_is_binary": is_binary,
            "headline_se": "country_cluster",
            "secondary_se": ["entity_cluster", "driscoll_kraay"],
            "wild_cluster_bootstrap_reps": args.bootstrap_reps,
            "bootstrap_seed": args.bootstrap_seed,
        },
        sample_mode=args.sample,
        bootstrap_reps=args.bootstrap_reps,
        bootstrap_seed=args.bootstrap_seed,
        bootstrap_show_progress=not args.no_bootstrap_progress,
        out_dir=out_dir,
        extra_lines=[
            "Outcome: ln_h_empe (WIOD H_EMPE labour-hours proxy)",
            f"Moderator column: {mod_var}",
            f"Controls: {', '.join(controls)}",
            f"Role: {mod_info['role_label']}",
            f"Theory note: {mod_info['theory_note']}",
            f"Sample note: {mod_info['sample_caveat']}",
            "Inference: country cluster headline; entity cluster + Driscoll-Kraay comparison",
        ],
    )


if __name__ == "__main__":
    main()
