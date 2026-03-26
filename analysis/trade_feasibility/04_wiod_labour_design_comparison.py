from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CODE_DIR = ROOT_DIR / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from _wiod_model_utils import load_or_build_wiod_panel, sample_stats
from _wiod_panel_utils import (
    BUCKET_NAMES,
    add_bucket_interactions,
    add_exposure_interactions,
    build_fe_formula,
    control_comparability_rows,
    fit_country_clustered,
    get_wiod_controls,
    moderator_to_columns,
    prepare_wiod_panel,
)


OUTPUT_DIR = Path(__file__).resolve().parent / "output"
SUPPORT_PATH = OUTPUT_DIR / "wiod_labour_model_support.csv"
BUCKET_PATH = OUTPUT_DIR / "wiod_bucket_coverage.csv"
EXPOSURE_PATH = OUTPUT_DIR / "wiod_exposure_balance.csv"
COMPARABILITY_PATH = OUTPUT_DIR / "wiod_control_comparability.csv"
SKELETON_PATH = OUTPUT_DIR / "wiod_model_comparison_skeleton.csv"
COEFFICIENT_PATH = OUTPUT_DIR / "wiod_heterogeneity_coefficients.csv"
NOTE_PATH = OUTPUT_DIR / "wiod_vs_kelms_note.md"


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def countries_string(df: pd.DataFrame) -> str:
    return ", ".join(sorted(df["country_code"].dropna().unique().tolist()))


def sample_row(
    model: str,
    description: str,
    df: pd.DataFrame,
    *,
    threshold: int | None = None,
) -> dict[str, object]:
    stats = sample_stats(df)
    row = {
        "model": model,
        "description": description,
        "n_countries": stats["n_countries"],
        "n_entities": stats["n_entities"],
        "n_observations": stats["n_obs"],
        "years": (
            f"{stats['year_min']}-{stats['year_max']}"
            if stats["year_min"] is not None and stats["year_max"] is not None
            else ""
        ),
        "countries_list": ", ".join(stats["countries"]),
        "pass_threshold": "",
    }
    if threshold is not None:
        row["pass_threshold"] = "PASS" if stats["n_countries"] >= threshold else "FAIL"
    return row


def model_sample(
    panel: pd.DataFrame,
    *,
    controls: list[str],
    sample_mode: str = "full",
    moderator: str | None = None,
    coord_mode: str = "continuous",
    require_exposure: bool = False,
) -> tuple[pd.DataFrame, str | None]:
    require = ["ln_h_empe", "ln_robots_lag1"] + controls
    has_var = None
    mod_var = None
    if moderator is not None:
        mod_var, has_var, _ = moderator_to_columns(moderator, coord_mode)
        require.append(mod_var)
    if require_exposure:
        require.append("exposed_binary")

    sample = prepare_wiod_panel(panel, require=require, sample=sample_mode)
    if has_var and has_var in sample.columns:
        sample = sample[sample[has_var]].copy()
    return sample, mod_var


def summarise_bucket_coverage(df: pd.DataFrame) -> pd.DataFrame:
    reference_countries = sorted(df["country_code"].dropna().unique().tolist())
    rows: list[dict[str, object]] = []
    for bucket in sorted(BUCKET_NAMES):
        bucket_df = df[df["bucket"] == bucket].copy()
        present = sorted(bucket_df["country_code"].dropna().unique().tolist())
        missing = sorted(set(reference_countries) - set(present))
        rows.append(
            {
                "bucket": bucket,
                "bucket_name": BUCKET_NAMES[bucket],
                "n_countries": len(present),
                "countries_present": ", ".join(present),
                "countries_missing": ", ".join(missing),
                "n_entities": int(bucket_df["entity"].nunique()),
                "n_observations": int(len(bucket_df)),
                "pass_20_country_threshold": "PASS" if len(present) >= 20 else "FAIL",
            }
        )
    return pd.DataFrame(rows)


def summarise_exposure_balance(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for exposure_group, sub in df.groupby("exposure_group", dropna=False):
        label = exposure_group if pd.notna(exposure_group) else "missing"
        rows.append(
            {
                "exposure_group": label,
                "n_countries": int(sub["country_code"].nunique()),
                "n_entities": int(sub["entity"].nunique()),
                "n_observations": int(len(sub)),
                "countries_list": countries_string(sub),
            }
        )
    return pd.DataFrame(rows)


def build_model_skeleton() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "model_id": "EQ3_BUCKET",
                "family": "bucket",
                "description": "Robots x bucket heterogeneity on WIOD labour panel",
                "outcome": "ln_h_empe",
                "key_terms": "lr_bucket_1, lr_bucket_2, lr_bucket_3, lr_bucket_4",
                "default_controls": "ln_va_wiod_qi, ln_k_wiod, gdp_growth",
                "headline_inference": "Country cluster + wild cluster bootstrap on key heterogeneity terms",
            },
            {
                "model_id": "EQ4_COORD_BUCKET",
                "family": "bucket",
                "description": "Robots x bucket x coord (primary focal)",
                "outcome": "ln_h_empe",
                "key_terms": "ln_robots_lag1:coord_pre_c, lr_mod_bucket_1..4",
                "default_controls": "ln_va_wiod_qi, ln_k_wiod, gdp_growth",
                "headline_inference": "Country cluster + wild cluster bootstrap on key interaction terms",
            },
            {
                "model_id": "EQ4_ADJCOV_BUCKET",
                "family": "bucket",
                "description": "Robots x bucket x adjcov (secondary focal, restricted)",
                "outcome": "ln_h_empe",
                "key_terms": "ln_robots_lag1:adjcov_pre_c, lr_mod_bucket_1..4",
                "default_controls": "ln_va_wiod_qi, ln_k_wiod, gdp_growth",
                "headline_inference": "Country cluster + wild cluster bootstrap on key interaction terms",
            },
            {
                "model_id": "EQ4_UD_BUCKET",
                "family": "bucket",
                "description": "Robots x bucket x ud (reference benchmark)",
                "outcome": "ln_h_empe",
                "key_terms": "ln_robots_lag1:ud_pre_c, lr_mod_bucket_1..4",
                "default_controls": "ln_va_wiod_qi, ln_k_wiod, gdp_growth",
                "headline_inference": "Country cluster + wild cluster bootstrap on key interaction terms",
            },
            {
                "model_id": "EQ5A_EXPOSURE",
                "family": "exposure",
                "description": "Robots x exposed/sheltered heterogeneity",
                "outcome": "ln_h_empe",
                "key_terms": "lr_exposed",
                "default_controls": "ln_va_wiod_qi, ln_k_wiod, gdp_growth",
                "headline_inference": "Country cluster + wild cluster bootstrap on lr_exposed",
            },
            {
                "model_id": "EQ5B_COORD_EXPOSURE",
                "family": "exposure",
                "description": "Robots x exposed/sheltered x coord",
                "outcome": "ln_h_empe",
                "key_terms": "ln_robots_lag1:coord_pre_c, lr_mod_exposure",
                "default_controls": "ln_va_wiod_qi, ln_k_wiod, gdp_growth",
                "headline_inference": "Country cluster + wild cluster bootstrap on key interaction terms",
            },
            {
                "model_id": "EQ5B_ADJCOV_EXPOSURE",
                "family": "exposure",
                "description": "Robots x exposed/sheltered x adjcov",
                "outcome": "ln_h_empe",
                "key_terms": "ln_robots_lag1:adjcov_pre_c, lr_mod_exposure",
                "default_controls": "ln_va_wiod_qi, ln_k_wiod, gdp_growth",
                "headline_inference": "Country cluster + wild cluster bootstrap on key interaction terms",
            },
            {
                "model_id": "EQ5B_UD_EXPOSURE",
                "family": "exposure",
                "description": "Robots x exposed/sheltered x ud (reference benchmark)",
                "outcome": "ln_h_empe",
                "key_terms": "ln_robots_lag1:ud_pre_c, lr_mod_exposure",
                "default_controls": "ln_va_wiod_qi, ln_k_wiod, gdp_growth",
                "headline_inference": "Country cluster + wild cluster bootstrap on key interaction terms",
            },
        ]
    )


def fit_and_collect(
    model_id: str,
    family: str,
    df: pd.DataFrame,
    rhs_terms: list[str],
    key_terms: list[str],
) -> pd.DataFrame:
    formula = build_fe_formula("ln_h_empe", rhs_terms)
    result = fit_country_clustered(formula, df)
    rows: list[dict[str, object]] = []
    for term in key_terms:
        coef = float(result.params.get(term, np.nan))
        se = float(result.bse.get(term, np.nan))
        rows.append(
            {
                "model_id": model_id,
                "family": family,
                "term": term,
                "coef_country_cluster": coef,
                "se_country_cluster": se,
                "ci95_low": coef - 1.96 * se if np.isfinite(se) else np.nan,
                "ci95_high": coef + 1.96 * se if np.isfinite(se) else np.nan,
                "p_country_cluster": float(result.pvalues.get(term, np.nan)),
                "n_countries": int(df["country_code"].nunique()),
                "n_entities": int(df["entity"].nunique()),
                "n_observations": int(len(df)),
            }
        )
    return pd.DataFrame(rows)


def write_note(
    *,
    base_row: dict[str, object],
    eq4_ud: dict[str, object],
    eq4_coord: dict[str, object],
    eq5a: dict[str, object],
    eq5b_ud: dict[str, object],
    eq5b_coord: dict[str, object],
    bucket_detail: pd.DataFrame,
    exposure_balance: pd.DataFrame,
) -> None:
    bucket_counts = ", ".join(
        f"B{int(row.bucket)}={int(row.n_countries)}"
        for row in bucket_detail.itertuples(index=False)
    )
    exposure_lines = exposure_balance.to_string(index=False)
    text = f"""# WIOD Labour Extension Note

The outcome remains labour input, not exports. The WIOD extension uses `H_EMPE`
as a broader-coverage labour-hours measure, while WIOD trade is used only to
classify exposed versus sheltered industries.

Current WIOD labour support with default controls (`ln_va_wiod_qi`, `ln_k_wiod`,
`gdp_growth`) is:

- Base panel: {base_row['n_countries']} countries, {base_row['n_entities']} entities, {base_row['n_observations']} observations ({base_row['years']})
- Eq. 4 bucket x coord: {eq4_coord['n_countries']} countries, {eq4_coord['n_observations']} observations
- Eq. 4 bucket x ud: {eq4_ud['n_countries']} countries, {eq4_ud['n_observations']} observations
- Eq. 5a exposure: {eq5a['n_countries']} countries, {eq5a['n_observations']} observations
- Eq. 5b exposure x coord: {eq5b_coord['n_countries']} countries, {eq5b_coord['n_observations']} observations
- Eq. 5b exposure x ud: {eq5b_ud['n_countries']} countries, {eq5b_ud['n_observations']} observations

Bucket models remain estimable in pooled form, but the thin-bucket concern is
real at the country-support level. In the shared `coord + ud` availability sample,
bucket country counts are: {bucket_counts}. That means the issue is more about
precision than identification.

Exposure comparison support on the same labour panel is:

```
{exposure_lines}
```

Control comparability is not one-to-one. `LAB_QI` and `H_EMPE` belong to the
same labour-input family but are measured differently. `VA_PYP` and `VA_QI` are
reasonably comparable real-output controls, while `CAP_QI` is not directly
comparable to either WIOD `K` or `CAP`. Any KLEMS-WIOD comparison should
therefore be presented as a joint measure-and-controls robustness check.

Recommended framing:

- Main WIOD extension: bucket heterogeneity with labour input outcome
- Parsimonious comparison: exposed/sheltered on the same WIOD labour panel
- Headline inference for institution models: country clustering with wild
  cluster bootstrap p-values on the key interaction terms; entity-clustered and
  Driscoll-Kraay results are secondary robustness checks
"""
    NOTE_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    ensure_output_dir()
    panel = load_or_build_wiod_panel()
    controls = get_wiod_controls(capital_proxy="k", include_gdp=True)

    base, _ = model_sample(panel, controls=controls)
    ud, ud_var = model_sample(panel, controls=controls, moderator="ud")
    coord, coord_var = model_sample(panel, controls=controls, moderator="coord")
    adjcov, adjcov_var = model_sample(panel, controls=controls, moderator="adjcov", sample_mode="common")
    exposure_base, _ = model_sample(panel, controls=controls, require_exposure=True)
    exposure_ud, ud_var_exp = model_sample(panel, controls=controls, moderator="ud", require_exposure=True)
    exposure_coord, coord_var_exp = model_sample(panel, controls=controls, moderator="coord", require_exposure=True)
    exposure_adjcov, adjcov_var_exp = model_sample(
        panel,
        controls=controls,
        moderator="adjcov",
        sample_mode="common",
        require_exposure=True,
    )

    support_rows = [
        sample_row("BASE_H_EMPE", "WIOD labour panel with default controls", base, threshold=20),
        sample_row("EQ2_COORD", "Robots x coord (primary focal)", coord, threshold=20),
        sample_row("EQ2_ADJCOV", "Robots x adjcov (secondary focal)", adjcov, threshold=14),
        sample_row("EQ2_UD", "Robots x ud (reference benchmark)", ud, threshold=20),
        sample_row("EQ3_BUCKET", "Bucket heterogeneity", base, threshold=20),
        sample_row("EQ4_COORD_BUCKET", "Bucket x coord (primary focal)", coord, threshold=20),
        sample_row("EQ4_ADJCOV_BUCKET", "Bucket x adjcov (secondary focal)", adjcov, threshold=14),
        sample_row("EQ4_UD_BUCKET", "Bucket x ud (reference benchmark)", ud, threshold=20),
        sample_row("EQ5A_EXPOSURE", "Exposed vs sheltered", exposure_base, threshold=20),
        sample_row("EQ5B_COORD_EXPOSURE", "Exposed x coord", exposure_coord, threshold=20),
        sample_row("EQ5B_ADJCOV_EXPOSURE", "Exposed x adjcov", exposure_adjcov, threshold=14),
        sample_row("EQ5B_UD_EXPOSURE", "Exposed x ud", exposure_ud, threshold=20),
    ]
    support_df = pd.DataFrame(support_rows)
    support_df.to_csv(SUPPORT_PATH, index=False)

    reference = base.copy()
    reference = reference[reference["country_code"].isin(sorted(set(ud["country_code"]) & set(coord["country_code"])))].copy()
    bucket_detail = summarise_bucket_coverage(reference)
    bucket_detail.to_csv(BUCKET_PATH, index=False)

    exposure_reference = exposure_base[
        exposure_base["country_code"].isin(sorted(set(exposure_ud["country_code"]) & set(exposure_coord["country_code"])))
    ].copy()
    exposure_balance = summarise_exposure_balance(exposure_reference)
    exposure_balance.to_csv(EXPOSURE_PATH, index=False)

    comparability_df = control_comparability_rows()
    comparability_df.to_csv(COMPARABILITY_PATH, index=False)

    skeleton_df = build_model_skeleton()
    skeleton_df.to_csv(SKELETON_PATH, index=False)

    coefficient_frames: list[pd.DataFrame] = []

    eq3_sample = base.copy()
    eq3_terms = add_bucket_interactions(eq3_sample)
    coefficient_frames.append(
        fit_and_collect(
            "EQ3_BUCKET",
            "bucket",
            eq3_sample,
            ["ln_robots_lag1"] + eq3_terms + controls,
            eq3_terms,
        )
    )

    eq4_coord_sample = coord.copy()
    eq4_coord_terms = add_bucket_interactions(eq4_coord_sample, mod_var=coord_var)
    eq4_coord_bucket_terms = [term for term in eq4_coord_terms if term.startswith("lr_bucket_")]
    eq4_coord_triples = [term for term in eq4_coord_terms if term.startswith("lr_mod_bucket_")]
    coefficient_frames.append(
        fit_and_collect(
            "EQ4_COORD_BUCKET",
            "bucket",
            eq4_coord_sample,
            ["ln_robots_lag1"] + eq4_coord_bucket_terms + [f"ln_robots_lag1:{coord_var}"] + eq4_coord_triples + controls,
            [f"ln_robots_lag1:{coord_var}"] + eq4_coord_triples,
        )
    )

    eq4_ud_sample = ud.copy()
    eq4_ud_terms = add_bucket_interactions(eq4_ud_sample, mod_var=ud_var)
    eq4_ud_bucket_terms = [term for term in eq4_ud_terms if term.startswith("lr_bucket_")]
    eq4_ud_triples = [term for term in eq4_ud_terms if term.startswith("lr_mod_bucket_")]
    coefficient_frames.append(
        fit_and_collect(
            "EQ4_UD_BUCKET",
            "bucket",
            eq4_ud_sample,
            ["ln_robots_lag1"] + eq4_ud_bucket_terms + [f"ln_robots_lag1:{ud_var}"] + eq4_ud_triples + controls,
            [f"ln_robots_lag1:{ud_var}"] + eq4_ud_triples,
        )
    )

    eq5a_sample = exposure_base.copy()
    eq5a_terms = add_exposure_interactions(eq5a_sample)
    coefficient_frames.append(
        fit_and_collect(
            "EQ5A_EXPOSURE",
            "exposure",
            eq5a_sample,
            ["ln_robots_lag1"] + eq5a_terms + controls,
            eq5a_terms,
        )
    )

    eq5b_coord_sample = exposure_coord.copy()
    eq5b_coord_terms = add_exposure_interactions(eq5b_coord_sample, mod_var=coord_var_exp)
    coefficient_frames.append(
        fit_and_collect(
            "EQ5B_COORD_EXPOSURE",
            "exposure",
            eq5b_coord_sample,
            ["ln_robots_lag1", "lr_exposed", f"ln_robots_lag1:{coord_var_exp}", "lr_mod_exposure"] + controls,
            [f"ln_robots_lag1:{coord_var_exp}", "lr_mod_exposure"],
        )
    )

    eq5b_ud_sample = exposure_ud.copy()
    eq5b_ud_terms = add_exposure_interactions(eq5b_ud_sample, mod_var=ud_var_exp)
    coefficient_frames.append(
        fit_and_collect(
            "EQ5B_UD_EXPOSURE",
            "exposure",
            eq5b_ud_sample,
            ["ln_robots_lag1", "lr_exposed", f"ln_robots_lag1:{ud_var_exp}", "lr_mod_exposure"] + controls,
            [f"ln_robots_lag1:{ud_var_exp}", "lr_mod_exposure"],
        )
    )

    coefficients_df = pd.concat(coefficient_frames, ignore_index=True)
    coefficients_df.to_csv(COEFFICIENT_PATH, index=False)

    support_lookup = {row["model"]: row for row in support_rows}
    write_note(
        base_row=support_lookup["BASE_H_EMPE"],
        eq4_ud=support_lookup["EQ4_UD_BUCKET"],
        eq4_coord=support_lookup["EQ4_COORD_BUCKET"],
        eq5a=support_lookup["EQ5A_EXPOSURE"],
        eq5b_ud=support_lookup["EQ5B_UD_EXPOSURE"],
        eq5b_coord=support_lookup["EQ5B_COORD_EXPOSURE"],
        bucket_detail=bucket_detail,
        exposure_balance=exposure_balance,
    )

    print("=" * 60)
    print("WIOD LABOUR DESIGN COMPARISON")
    print("=" * 60)
    print(support_df.to_string(index=False))
    print()
    print("Bucket coverage on shared coord+ud availability sample")
    print(bucket_detail.to_string(index=False))
    print()
    print("Exposure balance on shared coord+ud availability sample")
    print(exposure_balance.to_string(index=False))
    print()
    print(f"Saved support table to {SUPPORT_PATH}")
    print(f"Saved coefficient comparison to {COEFFICIENT_PATH}")
    print(f"Saved comparability note to {NOTE_PATH}")


if __name__ == "__main__":
    main()
