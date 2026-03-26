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
    parser.add_argument(
        "--capital-proxy",
        choices=["k", "capcomp"],
        default="k",
        help="WIOD capital control: K (default) or CAP compensation sensitivity.",
    )
    parser.add_argument(
        "--no-gdp",
        action="store_true",
        help="Omit GDP growth from the control set.",
    )
    parser.add_argument(
        "--bootstrap-reps",
        type=int,
        default=199,
        help="Wild cluster bootstrap repetitions for the key robot coefficient.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_or_build_wiod_panel()

    controls = get_wiod_controls(
        capital_proxy=args.capital_proxy,
        include_gdp=not args.no_gdp,
    )
    require = ["ln_h_empe", "ln_robots_lag1"] + controls
    sample = prepare_wiod_panel(df, require=require, sample="full")
    rhs_terms = ["ln_robots_lag1"] + controls

    logger.info(
        "WIOD Eq. 1 baseline sample: "
        f"{len(sample)} obs, {sample['entity'].nunique()} entities, "
        f"{sample['country_code'].nunique()} countries"
    )
    result = fit_all_inference(sample, outcome="ln_h_empe", rhs_terms=rhs_terms)

    write_model_bundle(
        prefix=f"wiod_eq1_baseline_{args.capital_proxy}",
        title="WIOD Eq. 1 baseline labour-input model (mainline)",
        result=result,
        rhs_terms=rhs_terms,
        key_terms=["ln_robots_lag1"],
        flags={
            "capital_proxy": args.capital_proxy,
            "include_gdp": not args.no_gdp,
            "headline_se": "country_cluster",
            "secondary_se": ["entity_cluster", "driscoll_kraay"],
            "wild_cluster_bootstrap_reps": args.bootstrap_reps,
        },
        sample_mode="full",
        bootstrap_reps=args.bootstrap_reps,
        out_dir=RESULTS_CORE_DIR,
        extra_lines=[
            "Outcome: ln_h_empe (WIOD H_EMPE labour-hours proxy)",
            f"Controls: {', '.join(controls)}",
            "Inference: country cluster headline; entity cluster + Driscoll-Kraay comparison",
        ],
    )


if __name__ == "__main__":
    main()
