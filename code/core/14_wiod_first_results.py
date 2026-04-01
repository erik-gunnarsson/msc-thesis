'''
Run the mainline WIOD first-results package in one command.

This coordinated runner rebuilds the WIOD panel, archives stale WIOD-only
artifacts from the results tree, regenerates the headline model
bundle, and writes compact summary files for review.

First-results package:
  - Eq. 1 baseline
  - Eq. 2 coord (primary focal)
  - Eq. 2 adjcov common sample (secondary focal)
  - Eq. 2 ud (reference benchmark)

Excluded from this coordinated run:
  - Bucket models (archived outside this branch workflow)
  - KLEMS legacy workflow
  - Archived exposure models
'''

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from loguru import logger

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from _paths import RESULTS_ARCHIVE_DIR, RESULTS_CORE_DIR, ensure_results_dirs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
SUMMARY_CSV = RESULTS_CORE_DIR / "wiod_first_results_summary.csv"
OVERVIEW_MD = RESULTS_CORE_DIR / "wiod_first_results_overview.md"
RUN_MANIFEST_JSON = RESULTS_CORE_DIR / "wiod_first_results_run_manifest.json"


@dataclass(frozen=True)
class ModelSpec:
    review_order: int
    model_id: str
    title: str
    role: str
    script: str
    cli_args: tuple[str, ...]
    prefix_template: str
    focal_term: str
    sample_mode: str

    def prefix(self, capital_proxy: str) -> str:
        return self.prefix_template.format(capital_proxy=capital_proxy)


MODEL_SPECS = [
    ModelSpec(
        review_order=1,
        model_id="EQ1",
        title="WIOD Eq. 1 baseline",
        role="headline baseline",
        script="10_wiod_baseline.py",
        cli_args=(),
        prefix_template="wiod_eq1_baseline_{capital_proxy}",
        focal_term="ln_robots_lag1",
        sample_mode="full",
    ),
    ModelSpec(
        review_order=2,
        model_id="EQ2_COORD",
        title="WIOD Eq. 2 coordination moderation",
        role="primary focal institutional result",
        script="11_wiod_institution_moderation.py",
        cli_args=("--moderator", "coord", "--sample", "full", "--coord-mode", "continuous"),
        prefix_template="primary_contribution_eq2_wiod_coord_full_{capital_proxy}_continuous",
        focal_term="ln_robots_lag1:coord_pre_c",
        sample_mode="full",
    ),
    ModelSpec(
        review_order=3,
        model_id="EQ2_ADJCOV",
        title="WIOD Eq. 2 adjusted coverage moderation",
        role="secondary focal restricted-sample result",
        script="11_wiod_institution_moderation.py",
        cli_args=("--moderator", "adjcov", "--sample", "common", "--coord-mode", "continuous"),
        prefix_template="secondary_focal_eq2_wiod_adjcov_common_{capital_proxy}_continuous",
        focal_term="ln_robots_lag1:adjcov_pre_c",
        sample_mode="common",
    ),
    ModelSpec(
        review_order=4,
        model_id="EQ2_UD",
        title="WIOD Eq. 2 union-density reference",
        role="reference benchmark institutional result",
        script="11_wiod_institution_moderation.py",
        cli_args=("--moderator", "ud", "--sample", "full", "--coord-mode", "continuous"),
        prefix_template="reference_benchmark_eq2_wiod_ud_full_{capital_proxy}_continuous",
        focal_term="ln_robots_lag1:ud_pre_c",
        sample_mode="full",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the WIOD first-results package")
    parser.add_argument(
        "--capital-proxy",
        choices=["k", "capcomp"],
        default="k",
        help="Frozen first-results capital proxy; K is the default thesis-facing choice.",
    )
    parser.add_argument(
        "--bootstrap-reps",
        type=int,
        default=199,
        help="Shared wild cluster bootstrap repetitions for the first-results package.",
    )
    parser.add_argument(
        "--skip-archive",
        action="store_true",
        help="Do not archive stale WIOD-only outputs before regenerating the first-results bundle.",
    )
    return parser.parse_args()


def artifact_prefix(name: str) -> str | None:
    patterns = [
        (r"^(?P<prefix>.+)_key_terms\.csv$", "prefix"),
        (r"^(?P<prefix>.+)_table_terms\.csv$", "prefix"),
        (r"^(?P<prefix>.+)_results\.txt$", "prefix"),
        (r"^(?P<prefix>.+)_table_meta\.json$", "prefix"),
        (r"^sample_manifest_(?P<prefix>.+)\.txt$", "prefix"),
        (r"^run_metadata_(?P<prefix>.+)\.json$", "prefix"),
    ]
    for pattern, group in patterns:
        match = re.match(pattern, name)
        if match:
            return match.group(group)
    return None


def is_wiod_artifact_prefix(prefix: str) -> bool:
    return (
        "wiod" in prefix
        or prefix.startswith("exploratory_")
        or prefix.startswith("primary_contribution_eq2_wiod")
        or prefix.startswith("secondary_focal_eq2_wiod")
        or prefix.startswith("reference_benchmark_eq2_wiod")
    )


def archive_stale_wiod_outputs(keep_prefixes: set[str]) -> list[str]:
    if not RESULTS_CORE_DIR.exists():
        return []

    keep_names = {
        SUMMARY_CSV.name,
        OVERVIEW_MD.name,
        RUN_MANIFEST_JSON.name,
    }
    stale_files: list[Path] = []
    for path in RESULTS_CORE_DIR.iterdir():
        if not path.is_file() or path.name in keep_names:
            continue
        prefix = artifact_prefix(path.name)
        if prefix is None or not is_wiod_artifact_prefix(prefix):
            continue
        if prefix in keep_prefixes:
            continue
        stale_files.append(path)

    if not stale_files:
        logger.info("No stale WIOD-only output artifacts found to archive.")
        return []

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_dir = RESULTS_ARCHIVE_DIR / f"wiod_first_results_superseded_{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    for path in sorted(stale_files):
        destination = archive_dir / path.name
        shutil.move(str(path), str(destination))
        moved.append(path.name)
    logger.info(
        f"Archived {len(moved)} stale WIOD-only outputs to {archive_dir}"
    )
    return moved


def run_script(script: str, cli_args: tuple[str, ...], *, capital_proxy: str, bootstrap_reps: int) -> None:
    cmd = [sys.executable, str(SCRIPT_DIR / script), *cli_args]
    if script != "09_build_wiod_panel.py":
        cmd.extend(["--capital-proxy", capital_proxy, "--bootstrap-reps", str(bootstrap_reps)])
    logger.info("Running " + " ".join(cmd[1:]))
    subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))


def parse_sample_manifest(prefix: str) -> dict[str, object]:
    path = RESULTS_CORE_DIR / f"sample_manifest_{prefix}.txt"
    text = path.read_text(encoding="utf-8")
    patterns = {
        "n_observations": r"Observations:\s+(\d+)",
        "n_entities": r"Entities:\s+(\d+)",
        "n_countries": r"Countries \((\d+)\):",
        "countries_list": r"Countries \(\d+\):\s+(.+)",
        "years": r"Years:\s+(\d{4}-\d{4})",
    }
    out: dict[str, object] = {"path": str(path)}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        out[key] = match.group(1).strip() if match else None
    for key in ["n_observations", "n_entities", "n_countries"]:
        if out[key] is not None:
            out[key] = int(out[key])
    return out


def collect_model_row(spec: ModelSpec, *, capital_proxy: str) -> dict[str, object]:
    prefix = spec.prefix(capital_proxy)
    key_terms_path = RESULTS_CORE_DIR / f"{prefix}_key_terms.csv"
    results_path = RESULTS_CORE_DIR / f"{prefix}_results.txt"
    key_terms = pd.read_csv(key_terms_path)
    focal = key_terms.loc[key_terms["term"] == spec.focal_term]
    if focal.empty:
        raise RuntimeError(f"Missing focal term {spec.focal_term} in {key_terms_path}")
    focal_row = focal.iloc[0].to_dict()
    sample = parse_sample_manifest(prefix)
    return {
        "review_order": spec.review_order,
        "model_id": spec.model_id,
        "title": spec.title,
        "role": spec.role,
        "output_prefix": prefix,
        "sample_mode": spec.sample_mode,
        "focal_term": spec.focal_term,
        "n_countries": sample["n_countries"],
        "n_entities": sample["n_entities"],
        "n_observations": sample["n_observations"],
        "years": sample["years"],
        "countries_list": sample["countries_list"],
        "coef_country_cluster": focal_row.get("coef_country_cluster"),
        "se_country_cluster": focal_row.get("se_country_cluster"),
        "p_country_cluster": focal_row.get("p_country_cluster"),
        "p_wild_cluster": focal_row.get("p_wild_cluster"),
        "ci95_low_country_cluster": focal_row.get("ci95_low_country_cluster"),
        "ci95_high_country_cluster": focal_row.get("ci95_high_country_cluster"),
        "key_terms_file": str(key_terms_path),
        "results_file": str(results_path),
        "sample_manifest_file": sample["path"],
    }


def write_summary_artifacts(rows: list[dict[str, object]], *, capital_proxy: str, bootstrap_reps: int, archived: list[str]) -> None:
    summary = pd.DataFrame(rows).sort_values("review_order").reset_index(drop=True)
    summary.to_csv(SUMMARY_CSV, index=False)

    lines = [
        "# WIOD First Results Overview",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Frozen specification:",
        f"- Capital proxy: `{capital_proxy}`",
        "- Outcome: `ln_h_empe`",
        "- Robot regressor: `ln_robots_lag1`",
        "- Controls: `ln_va_wiod_qi`, selected capital proxy, `gdp_growth`",
        "- Years: `2001-2014`",
        "- Headline inference: country-clustered SEs + wild cluster bootstrap",
        f"- Wild cluster bootstrap reps: `{bootstrap_reps}`",
        "",
        "Review order:",
    ]
    for row in summary.to_dict(orient="records"):
        lines.extend(
            [
                f"## {int(row['review_order'])}. {row['model_id']} — {row['title']}",
                f"- Role: {row['role']}",
                f"- Sample: {row['n_observations']} obs, {row['n_entities']} entities, {row['n_countries']} countries, {row['years']}",
                f"- Focal term: `{row['focal_term']}`",
                f"- Coef / SE / p(cluster) / p(wild): {row['coef_country_cluster']:.4f} / {row['se_country_cluster']:.4f} / {row['p_country_cluster']:.4f} / {row['p_wild_cluster']:.4f}",
                f"- Key terms CSV: `{Path(str(row['key_terms_file'])).name}`",
                f"- Results text: `{Path(str(row['results_file'])).name}`",
                "",
            ]
        )
    if archived:
        lines.extend(
            [
                "Archived stale WIOD-only outputs before regeneration:",
                f"- {len(archived)} files moved into `results/archive/`",
                "",
            ]
        )
    OVERVIEW_MD.write_text("\n".join(lines), encoding="utf-8")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "capital_proxy": capital_proxy,
        "bootstrap_reps": bootstrap_reps,
        "models": rows,
        "archived_stale_files": archived,
        "summary_csv": str(SUMMARY_CSV),
        "overview_md": str(OVERVIEW_MD),
    }
    RUN_MANIFEST_JSON.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info(f"Wrote summary CSV to {SUMMARY_CSV}")
    logger.info(f"Wrote overview note to {OVERVIEW_MD}")


def main() -> None:
    args = parse_args()
    ensure_results_dirs()
    RESULTS_CORE_DIR.mkdir(parents=True, exist_ok=True)

    keep_prefixes = {spec.prefix(args.capital_proxy) for spec in MODEL_SPECS}
    archived = [] if args.skip_archive else archive_stale_wiod_outputs(keep_prefixes)

    run_script("09_build_wiod_panel.py", (), capital_proxy=args.capital_proxy, bootstrap_reps=args.bootstrap_reps)
    for spec in MODEL_SPECS:
        run_script(
            spec.script,
            spec.cli_args,
            capital_proxy=args.capital_proxy,
            bootstrap_reps=args.bootstrap_reps,
        )

    rows = [collect_model_row(spec, capital_proxy=args.capital_proxy) for spec in MODEL_SPECS]
    write_summary_artifacts(
        rows,
        capital_proxy=args.capital_proxy,
        bootstrap_reps=args.bootstrap_reps,
        archived=archived,
    )
    logger.info("WIOD first-results package completed successfully.")


if __name__ == "__main__":
    main()
