"""
Build thesis-facing academic regression tables for WIOD Eq. 1, Eq. 2, and Eq. 2b.

Primary output:
  - results/tables/wiod_regression_table_combined.tex

Companion outputs:
  - results/tables/wiod_regression_table_combined.md
  - results/tables/wiod_regression_table_combined.csv
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from loguru import logger

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from _paths import RESULTS_CORE_DIR, RESULTS_SECONDARY_DIR, RESULTS_TABLES_DIR, ensure_results_dirs


@dataclass(frozen=True)
class ModelTableSpec:
    model_id: str
    column_number: int
    column_label: str
    prefix_template: str
    source_dir: Path
    source_script: str

    def prefix(self, capital_proxy: str) -> str:
        return self.prefix_template.format(capital_proxy=capital_proxy)


@dataclass(frozen=True)
class DisplayRowSpec:
    row_key: str
    label: str
    candidate_terms: tuple[str, ...]
    use_wild_stars: bool = False


MODEL_SPECS = [
    ModelTableSpec(
        model_id="EQ1",
        column_number=1,
        column_label="Eq. 1",
        prefix_template="wiod_eq1_baseline_{capital_proxy}",
        source_dir=RESULTS_CORE_DIR,
        source_script="code/core/14_wiod_first_results.py",
    ),
    ModelTableSpec(
        model_id="EQ2_COORD",
        column_number=2,
        column_label="Eq. 2 coord",
        prefix_template="primary_contribution_eq2_wiod_coord_full_{capital_proxy}_continuous",
        source_dir=RESULTS_CORE_DIR,
        source_script="code/core/14_wiod_first_results.py",
    ),
    ModelTableSpec(
        model_id="EQ2_ADJCOV",
        column_number=3,
        column_label="Eq. 2 adjcov",
        prefix_template="secondary_focal_eq2_wiod_adjcov_common_{capital_proxy}_continuous",
        source_dir=RESULTS_CORE_DIR,
        source_script="code/core/14_wiod_first_results.py",
    ),
    ModelTableSpec(
        model_id="EQ2_UD",
        column_number=4,
        column_label="Eq. 2 ud",
        prefix_template="reference_benchmark_eq2_wiod_ud_full_{capital_proxy}_continuous",
        source_dir=RESULTS_CORE_DIR,
        source_script="code/core/14_wiod_first_results.py",
    ),
    ModelTableSpec(
        model_id="EQ2B",
        column_number=5,
        column_label="Eq. 2b",
        prefix_template="exploratory_wiod_eq2b_coord_ud_full_{capital_proxy}_continuous",
        source_dir=RESULTS_SECONDARY_DIR,
        source_script="code/secondary/15_wiod_eq2b_hawk_dove.py",
    ),
]


DISPLAY_ROWS = [
    DisplayRowSpec(
        row_key="ln_robots_lag1",
        label="Log robot intensity (lagged)",
        candidate_terms=("ln_robots_lag1",),
        use_wild_stars=True,
    ),
    DisplayRowSpec(
        row_key="ln_robots_lag1_coord",
        label="Log robots x bargaining coordination",
        candidate_terms=("ln_robots_lag1:coord_pre_c",),
        use_wild_stars=True,
    ),
    DisplayRowSpec(
        row_key="ln_robots_lag1_adjcov",
        label="Log robots x adjusted bargaining coverage",
        candidate_terms=("ln_robots_lag1:adjcov_pre_c",),
        use_wild_stars=True,
    ),
    DisplayRowSpec(
        row_key="ln_robots_lag1_ud",
        label="Log robots x union density",
        candidate_terms=("ln_robots_lag1:ud_pre_c",),
        use_wild_stars=True,
    ),
    DisplayRowSpec(
        row_key="ln_robots_lag1_coord_ud",
        label="Log robots x coordination x union density",
        candidate_terms=("ln_robots_lag1:coord_pre_c:ud_pre_c",),
        use_wild_stars=True,
    ),
    DisplayRowSpec(
        row_key="ln_va",
        label="Log value added",
        candidate_terms=("ln_va_wiod_qi",),
    ),
    DisplayRowSpec(
        row_key="capital",
        label="Log capital",
        candidate_terms=("ln_k_wiod", "ln_capcomp_wiod"),
    ),
    DisplayRowSpec(
        row_key="gdp_growth",
        label="GDP growth",
        candidate_terms=("gdp_growth",),
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build thesis-facing academic regression tables.")
    parser.add_argument(
        "--capital-proxy",
        choices=["k", "capcomp"],
        default="k",
        help="Capital proxy for the structured model artifacts. The frozen thesis-facing default is k.",
    )
    parser.add_argument(
        "--star-source",
        choices=["wild", "cluster"],
        default="wild",
        help="Use wild-cluster bootstrap p-values or country-clustered p-values for robot-term stars.",
    )
    parser.add_argument(
        "--output-suffix",
        default=None,
        help="Optional filename suffix. Defaults to _clusterstars for clustered-star tables and empty for wild-star tables.",
    )
    return parser.parse_args()


def resolve_output_paths(*, star_source: str, output_suffix: str | None) -> tuple[Path, Path, Path]:
    suffix = output_suffix
    if suffix is None:
        suffix = "_clusterstars" if star_source == "cluster" else ""
    stem = f"wiod_regression_table_combined{suffix}"
    return (
        RESULTS_TABLES_DIR / f"{stem}.tex",
        RESULTS_TABLES_DIR / f"{stem}.md",
        RESULTS_TABLES_DIR / f"{stem}.csv",
    )


def load_model_bundle(spec: ModelTableSpec, *, capital_proxy: str) -> dict[str, object]:
    prefix = spec.prefix(capital_proxy)
    terms_path = spec.source_dir / f"{prefix}_table_terms.csv"
    meta_path = spec.source_dir / f"{prefix}_table_meta.json"
    missing = [path for path in [terms_path, meta_path] if not path.exists()]
    if missing:
        missing_str = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(
            f"Missing structured table artifacts for {spec.model_id}: {missing_str}. "
            f"Run {spec.source_script} to regenerate them."
        )

    terms = pd.read_csv(terms_path)
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    return {
        "spec": spec,
        "prefix": prefix,
        "terms": terms,
        "metadata": metadata,
    }


def select_term_row(terms: pd.DataFrame, candidates: tuple[str, ...]) -> pd.Series | None:
    matched = terms.loc[terms["term"].isin(candidates)]
    if matched.empty:
        return None
    return matched.iloc[0]


def significance_stars(p_value: float | None) -> str:
    if p_value is None or pd.isna(p_value):
        return ""
    if p_value < 0.01:
        return "***"
    if p_value < 0.05:
        return "**"
    if p_value < 0.10:
        return "*"
    return ""


def format_coef(value: float | None, *, p_value: float | None = None, use_stars: bool = False) -> str:
    if value is None or pd.isna(value):
        return ""
    stars = significance_stars(p_value) if use_stars else ""
    formatted = f"{float(value):.4f}"
    if formatted == "-0.0000":
        formatted = "0.0000"
    return f"{formatted}{stars}"


def format_se(value: float | None) -> str:
    if value is None or pd.isna(value):
        return ""
    return f"({float(value):.4f})"


def format_int(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return f"{int(value)}"


def format_float(value: object, decimals: int = 3) -> str:
    if value is None or pd.isna(value):
        return ""
    return f"{float(value):.{decimals}f}"


def escape_latex(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def build_display_rows(model_bundles: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    coefficient_rows: list[dict[str, object]] = []
    stat_rows: list[dict[str, object]] = []
    column_labels = [bundle["spec"].column_label for bundle in model_bundles]

    display_order = 1
    for row_spec in DISPLAY_ROWS:
        coef_row = {
            "display_order": display_order,
            "row_group": "coefficients",
            "row_type": "coef",
            "row_key": row_spec.row_key,
            "row_label": row_spec.label,
        }
        display_order += 1
        se_row = {
            "display_order": display_order,
            "row_group": "coefficients",
            "row_type": "se",
            "row_key": f"{row_spec.row_key}_se",
            "row_label": "",
        }
        display_order += 1

        row_has_data = False
        for bundle in model_bundles:
            label = bundle["spec"].column_label
            matched = select_term_row(bundle["terms"], row_spec.candidate_terms)
            if matched is None:
                coef_row[label] = ""
                se_row[label] = ""
                continue

            row_has_data = True
            coef_row[label] = format_coef(matched["coef_country_cluster"])
            se_row[label] = format_se(matched["se_country_cluster"])

        if row_has_data:
            coefficient_rows.extend([coef_row, se_row])

    stat_specs = [
        ("Country-industry FE", lambda meta: "Yes"),
        ("Year FE", lambda meta: "Yes"),
        ("Observations", lambda meta: format_int(meta.get("n_observations"))),
        ("Entities", lambda meta: format_int(meta.get("n_entities"))),
        ("Countries", lambda meta: format_int(meta.get("n_countries"))),
        ("R-squared", lambda meta: format_float(meta.get("r_squared"), decimals=3)),
    ]

    for row_label, value_fn in stat_specs:
        row = {
            "display_order": display_order,
            "row_group": "stats",
            "row_type": "stat",
            "row_key": row_label.lower().replace(" ", "_").replace("-", "_"),
            "row_label": row_label,
        }
        display_order += 1
        for bundle, label in zip(model_bundles, column_labels):
            row[label] = value_fn(bundle["metadata"])
        stat_rows.append(row)

    return coefficient_rows, stat_rows


def apply_star_source(
    coefficient_rows: list[dict[str, object]],
    model_bundles: list[dict[str, object]],
    *,
    star_source: str,
) -> None:
    p_value_field = "p_wild_cluster" if star_source == "wild" else "p_country_cluster"

    row_map = {row_spec.row_key: row_spec for row_spec in DISPLAY_ROWS}
    for row in coefficient_rows:
        if row["row_type"] != "coef":
            continue
        row_spec = row_map.get(row["row_key"])
        if row_spec is None or not row_spec.use_wild_stars:
            continue

        for bundle in model_bundles:
            label = bundle["spec"].column_label
            matched = select_term_row(bundle["terms"], row_spec.candidate_terms)
            if matched is None:
                row[label] = ""
                continue
            row[label] = format_coef(
                matched["coef_country_cluster"],
                p_value=matched.get(p_value_field),
                use_stars=True,
            )


def build_notes(model_bundles: list[dict[str, object]], *, star_source: str) -> str:
    years = sorted({bundle["metadata"].get("years") for bundle in model_bundles if bundle["metadata"].get("years")})
    capital_proxy = model_bundles[0]["metadata"].get("flags", {}).get("capital_proxy", "k")
    capital_label = "WIOD K" if capital_proxy == "k" else "WIOD CAP"
    period_note = years[0] if len(years) == 1 else ", ".join(years)
    if star_source == "wild":
        star_note = (
            "Stars on robot-related terms are based on wild-cluster bootstrap p-values "
            "(* p<0.10, ** p<0.05, *** p<0.01). "
        )
    else:
        star_note = (
            "Stars on robot-related terms are based on country-clustered p-values "
            "(* p<0.10, ** p<0.05, *** p<0.01). "
        )
    return (
        "Notes: Country-clustered standard errors in parentheses. "
        + star_note
        + "Controls are reported with country-clustered standard errors and no star notation. "
        + "All models include country-industry and year fixed effects. "
        + "Eq. 2 adjcov uses the restricted/common sample. "
        + "Eq. 2b is exploratory. "
        + f"Sample period: {period_note}. Capital control: {capital_label}."
    )


def rows_to_dataframe(rows: list[dict[str, object]], model_bundles: list[dict[str, object]]) -> pd.DataFrame:
    columns = ["display_order", "row_group", "row_type", "row_key", "row_label"]
    columns.extend(bundle["spec"].column_label for bundle in model_bundles)
    return pd.DataFrame(rows)[columns]


def write_markdown_table(
    coefficient_rows: list[dict[str, object]],
    stat_rows: list[dict[str, object]],
    model_bundles: list[dict[str, object]],
    note_text: str,
    output_path: Path,
) -> None:
    column_labels = [bundle["spec"].column_label for bundle in model_bundles]
    lines = [
        "# WIOD Combined Regression Table",
        "",
        "| Row | " + " | ".join(column_labels) + " |",
        "| --- | " + " | ".join(["---:"] * len(column_labels)) + " |",
    ]
    for row in coefficient_rows + stat_rows:
        values = [row["row_label"]] + [str(row.get(label, "")) for label in column_labels]
        lines.append("| " + " | ".join(values) + " |")
    lines.extend(["", note_text, ""])
    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_latex_table(
    coefficient_rows: list[dict[str, object]],
    stat_rows: list[dict[str, object]],
    model_bundles: list[dict[str, object]],
    note_text: str,
    output_path: Path,
) -> None:
    column_labels = [bundle["spec"].column_label for bundle in model_bundles]
    model_numbers = [f"({bundle['spec'].column_number})" for bundle in model_bundles]

    lines = [
        r"\begin{table}[!htbp]",
        r"\centering",
        r"\begin{threeparttable}",
        r"\caption{WIOD Regression Results for Eq. 1, Eq. 2, and Eq. 2b}",
        r"\label{tab:wiod_regression_table_combined}",
        r"\small",
        rf"\begin{{tabular}}{{l{'c' * len(model_bundles)}}}",
        r"\toprule",
        " & " + " & ".join(model_numbers) + r" \\",
        " & " + " & ".join(escape_latex(label) for label in column_labels) + r" \\",
        r"\midrule",
    ]

    for idx, row in enumerate(coefficient_rows):
        cell_values = [escape_latex(str(row.get(label, ""))) for label in column_labels]
        lines.append(escape_latex(str(row["row_label"])) + " & " + " & ".join(cell_values) + r" \\")
        if row["row_type"] == "se" and idx < len(coefficient_rows) - 1:
            lines.append(r"\addlinespace[0.2em]")

    lines.append(r"\midrule")
    for row in stat_rows:
        cell_values = [escape_latex(str(row.get(label, ""))) for label in column_labels]
        lines.append(escape_latex(str(row["row_label"])) + " & " + " & ".join(cell_values) + r" \\")

    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\begin{tablenotes}[flushleft]",
            r"\footnotesize",
            r"\item " + escape_latex(note_text),
            r"\end{tablenotes}",
            r"\end{threeparttable}",
            r"\end{table}",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    ensure_results_dirs()
    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    latex_path, markdown_path, csv_path = resolve_output_paths(
        star_source=args.star_source,
        output_suffix=args.output_suffix,
    )

    model_bundles = [load_model_bundle(spec, capital_proxy=args.capital_proxy) for spec in MODEL_SPECS]
    coefficient_rows, stat_rows = build_display_rows(model_bundles)
    apply_star_source(coefficient_rows, model_bundles, star_source=args.star_source)
    note_text = build_notes(model_bundles, star_source=args.star_source)

    combined_rows = coefficient_rows + stat_rows
    rows_df = rows_to_dataframe(combined_rows, model_bundles)
    rows_df.to_csv(csv_path, index=False)
    write_markdown_table(coefficient_rows, stat_rows, model_bundles, note_text, markdown_path)
    write_latex_table(coefficient_rows, stat_rows, model_bundles, note_text, latex_path)

    logger.info(f"Combined table CSV -> {csv_path}")
    logger.info(f"Combined table Markdown -> {markdown_path}")
    logger.info(f"Combined table LaTeX -> {latex_path}")


if __name__ == "__main__":
    main()
