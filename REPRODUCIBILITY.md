# Reproducibility checklist (thesis WIOD workflow)

Use this after time away from the project. All commands assume repository root and **[uv](https://docs.astral.sh/uv/)** with Python **3.11+**.

## 1. Environment

```bash
uv sync
```

## 2. Data inputs (`data/`)

Expected files are listed in [README.md](README.md) (IFR, ICTWSS, Eurostat GDP/unemployment, WIOD SEA, WIOT workbooks, etc.). The panel builder fails fast if anything required is missing.

## 3. Command sequence (canonical thesis outputs)

1. **Panel** — `uv run python code/core/09_build_wiod_panel.py`  
   Writes `data/cleaned_data_wiod.csv`.

2. **First-results bundle (Eq. 1, Eq. 2 × 4)** — `uv run python code/core/14_wiod_first_results.py`  
   Default: **999** wild-cluster bootstrap reps. Use `--no-bootstrap-progress` in CI logs.  
   Writes under `results/core/` (`wiod_first_results_summary.csv`, `wiod_first_results_overview.md`, per-model `*_key_terms.csv`, etc.).

3. **Eq. 2b gate (exploratory)** — `uv run python code/exploration/wiod_feasibility/05_wiod_eq2b_hawk_dove_gate.py`

4. **Eq. 2b estimation** — `uv run python code/secondary/15_wiod_eq2b_hawk_dove.py`

5. **Coord-on-Eq.2b-sample diagnostic** — `uv run python code/secondary/16_wiod_eq2_coord_on_eq2b_sample.py`

6. **Common-sample robustness** — `uv run python code/secondary/17_wiod_common_sample_robustness.py`

7. **Academic tables** —  
   Canonical (wild-bootstrap stars): `uv run python code/core/18_wiod_academic_tables.py` → `results/tables/wiod_regression_table_combined.{md,tex,csv}`.

   Optional inference robustness (country-clustered stars, appendix-only):  
   `uv run python code/core/18_wiod_academic_tables.py --star-source cluster` → `results/secondary/inference_robustness/wiod_regression_table_combined_clusterstars.{md,tex,csv}`.

   **Appendix — CH-inclusive log robot stock (GH #29)** — `uv run python code/core/18_wiod_academic_tables.py --appendix-robot-stock-ch-inclusive-only` (and the same with `--star-source cluster`) → `results/tables/wiod_regression_table_appendix_robot_stock_ch_inclusive.{md,tex,csv}` plus cluster-stars sibling under `results/secondary/inference_robustness/`. Underlying models: `10_wiod_baseline.py` / `11_wiod_institution_moderation.py` with `--robot-regressor stock`, `--output-dir results/secondary/robustness`, `--prefix-override robust_robotstock_eq1_baseline` / `robust_robotstock_eq2_coord`.

8. **Validate artifacts** — `uv run python code/secondary/_validate_artifacts.py`  
   Checks internal consistency among `results/core/` (`wiod_first_results_run_manifest.json`, `wiod_first_results_summary.csv`, per-model `*_table_meta.json`, `*_table_terms.csv`, `*_key_terms.csv`, `run_metadata_*.json`, `sample_manifest_*.txt`), selected `results/secondary/` robustness CSVs (including jackknife + sample decomposition), and `results/tables/` + `results/secondary/inference_robustness/` combined Markdown, TeX, and CSV regression tables (`wiod_first_results_*` mismatches emit a rerun hint). Optional diff against a saved manifest:  
   `uv run python code/secondary/_validate_artifacts.py --compare-snapshot results/_snapshot_YYYYMMDD/run_manifest.json`

9. **CI smoke (no data required)** — `uv run python code/secondary/smoke_test.py`

## 4. Expected sample counts (sanity check)

After step 2, `wiod_first_results_summary.csv` should report approximately:

| Model        | Observations |
|-------------|--------------|
| Eq. 1       | 2571         |
| Eq. 2 coord | 2500         |
| Eq. 2 adjcov| 1685         |
| Eq. 2 ud    | 2356         |

(Eq. 2b and common-sample specs use the **23-country** coord × ud intersection: **2356** obs — see secondary outputs.)

## 5. Script taxonomy

| Location | Role |
|----------|------|
| `code/core/` | Active WIOD mainline: panel build, Eq. 1–2, first-results runner, tables |
| `code/secondary/` | Diagnostics, robustness, jackknife, bootstrap audit, artifact validator, smoke test |
| `code/exploration/wiod_feasibility/` | Feasibility / Eq. 2b gate (not part of minimal Eq. 1–2-only path) |
| `code/secondary/legacy_klems/` | Legacy KLEMS robustness only |
| `results/core/` | Headline regression artifacts |
| `results/secondary/` | Eq. 2b, decomposition, common-sample, bootstrap audit, robustness subfolder |
| `results/secondary/inference_robustness/` | Country-cluster-stars regression table variant (comparison to headline wild-bootstrap table) |
| `results/tables/` | Canonical combined Markdown/TeX tables + appendix CH-inclusive robot-stock table (`wiod_regression_table_appendix_robot_stock_ch_inclusive.*`, GH #29) |

## 6. Wild-cluster bootstrap — methods and code

**Implementation:** `wild_cluster_bootstrap_pvalue` in [`code/_wiod_panel_utils.py`](code/_wiod_panel_utils.py). **Restricted model per tested coefficient:** `build_restricted_formulas` in [`code/_wiod_model_utils.py`](code/_wiod_model_utils.py) (drops only the focal RHS term under H₀, same country-industry and year FE as the full model).

**Algorithm (Rademacher wild cluster, restricted residuals).**

1. Fit homoskedastic OLS for the unrestricted and restricted specifications.
2. Let `ŷ_r` and `û_r` be restricted fitted values and residuals. For each replication, draw `v_g ∈ {-1, +1}` for each **country** cluster `g`, map to observations `w`, and form `y* = ŷ_r + û_r ∘ w`.
3. Refit the **unrestricted** design on `y*` with **country-clustered** covariance; collect the bootstrap t-stat for the focal parameter.
4. **Two-sided p-value:** fraction of draws with `|t*| ≥ |t|`, where `t` is the cluster-robust t-stat from the real sample.

Defaults: **999** repetitions, cluster id **`country_code`**, PRNG **`numpy.random.default_rng(seed)`**. This follows Cameron, Gelbach & Miller (2008) and is the usual conservative reference when the number of clusters is modest (see also MacKinnon & Webb on few-cluster bias of cluster sandwiches).

**Seed convention.** Scripts take `--bootstrap-seed` (default **123**). [`summarise_key_terms`](code/_wiod_panel_utils.py) passes `seed = bootstrap_seed + idx` for the `idx`-th entry of `key_terms`. For Eq. 2 ([`11_wiod_institution_moderation.py`](code/core/11_wiod_institution_moderation.py)), `key_terms = [ln_robots_lag1, interaction]`, so the **coordination interaction uses effective seed 124**. Eq. 2b lists four focal terms, so effective seeds **123–126** for those rows. Regenerated `run_metadata_*.json` files include `effective_bootstrap_seed_by_term` for traceability.

**Audit (GH #4):** multi-seed stability and cluster-vs-wild narrative — [`results/secondary/bootstrap_audit_eq2_coord.md`](results/secondary/bootstrap_audit_eq2_coord.md); `uv run python code/secondary/_audit_bootstrap_eq2_coord.py`.

### Thesis inference standard (results chapter)

- **Report** country-clustered standard errors in parentheses and **wild-bootstrap *p*-values / stars** on robot-related coefficients (999 Rademacher reps; canonical table from [`18_wiod_academic_tables.py`](code/core/18_wiod_academic_tables.py), default `--star-source wild`).
- **Eq. 2 coordination:** treat **wild *p* ≈ 0.11** as the headline (*suggestive*, not sharp null rejection at 5%). Cite **country-cluster *p* ≈ 0.02** only as a **few-clusters sensitivity** contrast (asymptotic cluster inference can be liberal with ~25 groups).
- Do **not** use cluster-*p* alone as the sole basis for claiming sharp significance on the focal interaction.

Details and drafting language: [`results/RESULTS_BRIEF.md`](results/RESULTS_BRIEF.md), [`results/interpretation_memo.md`](results/interpretation_memo.md).

## 7. Bootstrap / seeds (quick reference)

Wild-cluster bootstrap defaults: **999** reps, base `--bootstrap-seed 123` (e.g. [`14_wiod_first_results.py`](code/core/14_wiod_first_results.py)). The second `key_terms` row in Eq. 2 uses effective seed **124** for the robot × coordination interaction; see §6 and [`results/secondary/bootstrap_audit_eq2_coord.md`](results/secondary/bootstrap_audit_eq2_coord.md).
