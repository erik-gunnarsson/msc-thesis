# Results interpretation memo (thesis single source of truth)

Generated for writing the empirical chapter. Numeric claims trace to `results/core/` and `results/secondary/` unless noted. Last aligned with `wiod_first_results_summary.csv` after full pipeline regen.

---

## Eq. 1 — Baseline (`wiod_eq1_baseline_k_*`)

**Claim.** On the full manufacturing panel (26 countries, 2571 obs, 2001–2014), the within country-industry association between one-year-lagged log robot intensity and log employee hours is **small and statistically indistinguishable from zero** under both country-clustered inference and the wild-cluster bootstrap on the robot term.

**Evidence.** Coef. ≈ **0.0096**, p_cluster ≈ **0.119**, p_wild ≈ **0.126** (`wiod_first_results_summary.csv`).

**Do not overclaim.** A null average slope is **consistent with** heterogeneity that Eq. 2 is meant to explain; it does **not** prove “robots have no effect without institutions.”

**Cite in thesis:** §6.1.2; manifest `sample_manifest_wiod_eq1_baseline_k.txt`.

---

## Eq. 2 coord — Primary institutional result (`primary_contribution_eq2_wiod_coord_full_k_continuous_*`)

**Claim.** Adding the interaction of lagged robot intensity with **baseline bargaining coordination** (ICTWSS, pre-sample mean 1990–1995, country-level, centred) yields a **positive** interaction: higher coordination is associated with a **less negative / more positive** slope of employment on robots at the mean of other controls. The coefficient is **stable across auxiliary bootstrap seeds** (see `bootstrap_audit_eq2_coord.md`).

**Evidence.** Interaction coef. ≈ **0.01245**; p_cluster ≈ **0.020**; p_wild ≈ **0.11** (999 reps; seed base 123 → effective **124** for the second key term). Country count **25**; observations **2500**.

**Caveat — few clusters.** With ~25 country clusters, cluster-based p-values can be **too optimistic** relative to wild-cluster bootstrap (see audit note). The **conservative** headline for inference is the **wild-bootstrap** p; the cluster p is **supporting**.

**Do not overclaim.** TWFE with country-industry and year FE does not deliver a causal effect of institutions on the robot–employment gradient without further design; frame as **robust association** consistent with coordinated-bargaining adjustment.

**Cite in thesis:** §6.1.3; overview `wiod_first_results_overview.md`.

---

## Eq. 2 adjcov — Secondary focal, restricted sample (`secondary_focal_eq2_wiod_adjcov_common_*`)

**Claim.** On the **common / adjcov-feasible** subsample (15 countries, 1685 obs), the interaction of robots with **adjusted bargaining coverage** is **essentially zero** and insignificant under both inference methods.

**Evidence.** Coef. ≈ **0.00026**, p_cluster ≈ **0.52**, p_wild ≈ **0.51**.

**Do not overclaim.** Smaller cluster count limits power; keep as **secondary** institutional check, not a headline causal comparison to coordination.

**Thesis decision (AdjCov).** **Keep** as restricted-sample robustness / secondary focal; thesis narrative should **not** bury it entirely — one short paragraph or table note is enough.

**Cite in thesis:** §6.1.4.

---

## Eq. 2 ud — Reference benchmark (`reference_benchmark_eq2_wiod_ud_full_k_continuous_*`)

**Claim.** **Union density** does **not** materially moderate the robot–hours slope in this specification ( coef. ≈ **0**, p_wild ≈ **0.95**).

**Use in thesis.** Supports the **theory emphasis on coordination** rather than raw density (aligned with Hawk–Dove framing); avoid treating ud as a failed “main” hypothesis — it is the **benchmark**.

**Cite in thesis:** §6.1.4.

---

## Eq. 2b — Exploratory joint coord × ud (`exploratory_wiod_eq2b_coord_ud_*`, common sample)

**Claim.** On the **23-country** coord ∩ ud intersection (2356 obs), the **three-way** robot × coordination × union-density term is **not** significant at conventional levels (p_wild ≈ **0.59** in common-sample table). The stand-alone coordination slope in the joint model is **noisier** than in Eq. 2 coord-only on the full sample.

**Supporting artifacts.** `wiod_common_sample_robustness.md`, `wiod_eq2_coord_sample_decomposition.md` (mixed sample vs. specification effect), gate bundle `wiod_eq2b_coord_ud_gate.md` (under `results/archive/exploration/wiod_feasibility/` if `results/exploration/` is empty until rerun — see [`results/README.md`](README.md)) (gate **GO** on support / collinearity).

**Do not overclaim.** Eq. 2b is **exploratory**; do **not** present the three-way term as a core hypothesis test.

---

## Table policy (GH #9) — **locked decision**

- **Primary thesis table:** use **wild-cluster bootstrap stars** on robot-related terms (`results/tables/wiod_regression_table_combined.{md,tex}`). Table notes match this inference standard.

- **Country-cluster inference (comparison only):** do **not** present cluster-*p*-based stars alongside the headline table under `results/tables/`. For readers who want the asymptotic alternative, keep a single **inference-robustness** variant with stars from country-clustered *p*-values under `results/secondary/inference_robustness/wiod_regression_table_combined_clusterstars.{md,tex}` — captions/notes explicitly point back to wild bootstrap as the thesis inference standard; appendix / §6.2 pointers only.

- **Prose:** lead main-text coefficient discussion with **wild-bootstrap *p*** (stars on the headline table agree). Mention **country-cluster *p*** only where you explain fewer clusters / asymptotic-vs-bootstrap comparison (same numbers as tabulated in optional cluster-stars table or `*_key_terms.csv`).

**Reasoning.** The bootstrap audit (`results/secondary/bootstrap_audit_eq2_coord.md`) shows p_cluster ≈ **0.020** vs p_wild ≈ **0.11** for the focal interaction with ~25 clusters. Leading with wild-bootstrap stars matches the **conservative** inference standard appropriate for this cluster count.

---

## Eq. 2b placement (GH #11) — **locked decision**

**Appendix + one short §6.1.5 paragraph.**

- **Appendix:** full Eq. 2b table / estimates and the gate + decomposition references.
- **Main text:** 2–4 sentences: joint model is exploratory; three-way term not significant; decomposition shows attenuation is partly **specification** (adding ud interactions), not only sample change; common-sample table supports **null** on ud moderation.

**Do not** give Eq. 2b equal billing to Eq. 2 coord in the **abstract** or **introduction** claims.

---

## §6.2.4 specification placement — capital `K` vs `CAP`, crisis years (GH #30) — **locked**

**Defaults.** **Headline:** WIOD **`K`** + full **2001–2014**. **`CAP`** swap and **exclude 2008–2009** live **only in the appendix**, not as extra columns on the main combined table.

**Drafting stubs (copy-ready):**

1. **Crisis exclusion:** “The focal coordination interaction is stable when **2008–2009** are excluded (**β** ≈ **0.012**, wild-bootstrap **p** ≈ **0.10**; full estimates in **Table A.X**).” *(Replace **Table A.X** with the final appendix label.)*

2. **`CAP` sensitivity:** “Using **capital compensation (`CAP`)** instead of **capital stock (`K`)** materially **weakens** the coordination interaction (**β** falls from ≈ **0.0124** to ≈ **0.0062**, wild-bootstrap **p** rises to ≈ **0.28** on the same sample), consistent with **`CAP`** absorbing overlapping variation with **value added**; **`K`** remains the headline production-function-style control.” *(Numbers from `results/secondary/robustness/robust_capcomp_eq2_coord_key_terms.csv` vs headline `primary_contribution_eq2_wiod_coord_full_k_continuous_key_terms.csv`.)*

**Artifacts.** `results/secondary/robustness/robust_excl0809_*`, `robust_capcomp_*`; narrative scoreboard `results/secondary/robustness_overview_20260515.md`.

---

## Robot intensity headline + CH-inclusive stock appendix (GH #29) — **locked**

**Headline regressor:** **`ln_robots_lag1`** (IFR per-worker intensity, lagged) — aligned with **Leibrecht et al. (2023)** as the moderation comparator. Do **not** reframe the headline around Graetz & Michaels (2018) robot scaling; their contribution motivates **macro controls**, not replacing the Leibrecht intensity definition.

**Single appendix deliverable** (referenced from **§6.2.2** *and* **§6.2.3** so the appendix does not sprawl):

- `results/tables/wiod_regression_table_appendix_robot_stock_ch_inclusive.{md,tex,csv}` (wild-bootstrap stars on robot rows; cluster-stars sibling under `results/secondary/inference_robustness/`).
- Underlying estimates: `results/secondary/robustness/robust_robotstock_eq1_baseline_*`, `robust_robotstock_eq2_coord_*`.

**Numbers (current committed run):** Eq. 1 stock: **2712** obs / **27** countries (`ln_robot_stock_lag1` coef ≈ **0.013**, wild *p* ≈ **0.068**). Eq. 2 coord stock: **2641** obs / **26** countries (interaction ≈ **0.0149**, wild *p* ≈ **0.050**) — coordination pattern **strengthens** vs headline intensity sample on wild-bootstrap inference.

**§8.1 Switzerland (short):** Two–three sentences: intensity denominator undefined at CH sub-industries because IFR employment is zero; headline excludes CH under the Leibrecht-style intensity definition; CH-inclusive **`ln_robot_stock_lag1`** estimates appear in **Appendix Table `\ref{tab:wiod_appendix_robot_stock_ch_inclusive}`** (adjust numbering in prose). Treat as **measurement constraint** from secondary data (Bryman & Bell Ch. 14 analogue); convergent operationalisation via stock supports construct validity (Ch. 7 analogue) without replacing the headline.

**Footnote stub (§4.2.1 / §5.2.2 when defining intensity):** “IFR employment is recorded as zero for all Swiss manufacturing sub-industries in our extract, so the per-worker intensity used elsewhere is undefined for CH; see appendix Table~\ref{tab:wiod_appendix_robot_stock_ch_inclusive} for CH-inclusive log robot stocks.”

---

## §6.x — File pointer table

| Thesis subsection | Primary artifact |
|-------------------|------------------|
| 6.1.1 Descriptives | Build from panel + ICTWSS; country matrix `results/archive/exploration/wiod_feasibility/europe_country_availability_matrix.csv` (or rerun exploration → `results/exploration/wiod_feasibility/`) |
| 6.1.2 Eq. 1 | `results/core/wiod_eq1_baseline_k_key_terms.csv` |
| 6.1.3 Eq. 2 coord | `results/core/primary_contribution_eq2_wiod_coord_full_k_continuous_key_terms.csv` |
| 6.1.4 Eq. 2 ud / adjcov | `reference_benchmark_*`, `secondary_focal_*` key_terms |
| 6.1.5 Eq. 2b | `results/secondary/exploratory_wiod_eq2b_coord_ud_*`, `wiod_common_sample_robustness.md` |
| 6.2 Inference | `results/secondary/bootstrap_audit_eq2_coord.md` (GH #4 audit: algorithm, seeds, reporting) |
| 6.2 Sample | `wiod_common_sample_robustness.md`, `wiod_eq2_coord_sample_decomposition.md`, `wiod_jackknife_eq2_coord.*` |
| 6.2 CH / intensity | `results/tables/wiod_regression_table_appendix_robot_stock_ch_inclusive.tex` (GH #29 unified appendix); `results/secondary/wiod_ch_alt_normalisation.md`; `results/secondary/robustness/robust_robotstock_*` |
| 6.2 Specification | `results/secondary/robustness/robust_capcomp_*`, `robust_binarycoord_*`, `robust_excl0809_*` |
| 6.2 Multicollinearity | `results/secondary/wiod_vif_audit.md` (plus Eq. 2b gate `wiod_eq2b_coord_ud_vif.csv` in `results/archive/exploration/wiod_feasibility/` or `results/exploration/wiod_feasibility/` after rerun) |
| Combined thesis table | `results/tables/wiod_regression_table_combined.tex` |
| Appendix CH-inclusive robot stock (Eq. 1 + Eq. 2 coord) | `results/tables/wiod_regression_table_appendix_robot_stock_ch_inclusive.tex` |
| Inference-robustness table (country-cluster stars) | `results/secondary/inference_robustness/wiod_regression_table_combined_clusterstars.tex` |

---

## Downstream

**Chapter draft (GH #12):** start from this memo; every coefficient in prose should match `wiod_first_results_summary.csv` or the listed robustness paths.
