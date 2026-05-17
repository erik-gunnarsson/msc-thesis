# Results brief (1–2 pages) - May 15th 

**Numbers** trace to `[wiod_first_results_summary.csv](core/wiod_first_results_summary.csv)`.   
**Claims and caveats** are expanded in `[interpretation_memo.md](interpretation_memo.md)`.

## Design (headline)

- WIOD manufacturing panel, **2001–2014**.
- Two-way fixed effects: **country-industry** and **year** 
- **Country-clustered** standard errors (asymptotic cluster inference).
- **Wild-cluster Rademacher bootstrap**, **999** replications, country clusters — **headline inference** on robot-related coefficients and interactions (**wild-bootstrap stars** on the canonical table under `results/tables/`). **`--bootstrap-seed`** (default **123**) is advanced by `+idx` per `key_terms` row; Eq. 2 coordination interaction uses **effective seed 124** (see `REPRODUCIBILITY.md` §6–7, `results/secondary/bootstrap_audit_eq2_coord.md`, GH #4). Report **country-cluster *p*** in prose **only** for comparison / few-clusters framing, or alongside the inference-robustness table (`results/secondary/inference_robustness/wiod_regression_table_combined_clusterstars.*`).
- Institutional moderators use **pre-sample** country means (ICTWSS coordination; adjusted coverage where feasible; union density benchmark), centred in estimation.

## Core estimates 


| Spec                | Focal term                                  | Countries | *N*  | Coef.      | *p* cluster | *p* wild (999) |
| ------------------- | ------------------------------------------- | --------- | ---- | ---------- | ----------- | -------------- |
| Eq. 1               | ln robots (lag 1)                           | 26        | 2571 | 0.0096     | 0.119       | 0.126          |
| Eq. 2 coordination  | ln robots × coordination                    | 25        | 2500 | **0.0124** | **0.020**   | **0.108**      |
| Eq. 2 adj. coverage | ln robots × adj. coverage *(common-sample)* | 15        | 1685 | 0.00026    | 0.521       | 0.509          |
| Eq. 2 union density | ln robots × union density                   | 23        | 2356 | ≈ −0.00003 | 0.939       | 0.955          |


## What to say (plain)

- **Eq. 1:** Average within country-industry gradient of employment on lagged robot intensity is **small** and **not distinguishable from zero** under both cluster inference and wild bootstrap — consistent with modelling **heterogeneity** in Eq. 2, not proof of “no robot effect.”
- **Eq. 2 coordination:** The robot × coordination interaction is **positive**: higher bargaining coordination aligns with a **less negative / more positive** robot–employment slope (conditional on TWFE controls). **Lead sentence:** **wild-bootstrap *p*** ≈ **0.11** (~25 clusters): **suggestive, not sharp null rejection.** (Country-cluster *p* ≈ **0.02** — asymptotic inference on the smaller cluster count *only* if you cite it as sensitivity; see appendix inference-robustness table.)
- **Eq. 2 adjusted coverage:** On the adjcov-feasible subsample the interaction is **essentially zero** and insignificant (**secondary** institutional check; smaller *N*, fewer clusters).
- **Eq. 2 union density:** Interaction **near zero** and insignificant — use as a **reference benchmark** for “density vs coordination,” not as a competing headline hypothesis.
- **Eq. 2b (exploratory):** Joint coord × UD specification on the **coord ∩ UD intersection** (**23** countries, **2356** obs): three-way **Hawk–Dove** term **not significant** (*p* wild ≈ **0.59** on that common-sample table — see `[secondary/wiod_common_sample_robustness.md](secondary/wiod_common_sample_robustness.md)`). **Do not** equal prominence with Eq. 2 coordination-only; appendix + short main-text caveat is enough.

## Robustness / diagnostics (pointers only)

- **Few clusters + focal interaction:** Bootstrap seed audit — stable wild *p* across seeds; cluster vs wild gap documented — `[secondary/bootstrap_audit_eq2_coord.md](secondary/bootstrap_audit_eq2_coord.md)`.
- **Leave-one-country jackknife (Eq. 2 coordination):** `[secondary/wiod_jackknife_eq2_coord.md](secondary/wiod_jackknife_eq2_coord.md)`.
- **Common sample + specification comparison:** `[secondary/wiod_common_sample_robustness.md](secondary/wiod_common_sample_robustness.md)`; decomposition — `[secondary/wiod_eq2_coord_sample_decomposition.md](secondary/wiod_eq2_coord_sample_decomposition.md)`.
- **Eq. 2b feasibility gate:** `[exploration/wiod_feasibility/wiod_eq2b_coord_ud_gate.md](exploration/wiod_feasibility/wiod_eq2b_coord_ud_gate.md)`.
- **Crisis years (appendix only; GH #30):** exclude **2008–2009** — Eq. 2 coordination interaction stays ~**0.012** (e.g. **0.01218**, SE ~**0.00538**, wild *p* ~**0.104** vs headline **0.0124** / **0.108**) on [`robust_excl0809_eq2_coord_key_terms.csv`](secondary/robustness/robust_excl0809_eq2_coord_key_terms.csv). Not a main-table column; §6.2.4 should forward-reference the appendix table (**Table A.X** placeholder).
- **Capital proxy (appendix only; GH #30):** headline control remains **`K`**. **`CAP`** (`--capital-proxy capcomp`) is appendix sensitivity: interaction falls to ~**0.00618** (wild *p* ~**0.28**) — [`robust_capcomp_eq2_coord_key_terms.csv`](secondary/robustness/robust_capcomp_eq2_coord_key_terms.csv). Describe as **attenuation under an alternate capital measure**, not “unchanged results.”
- **Robot exposure — headline vs appendix (GH #29):** Main tables stay on **Leibrecht-style per-worker intensity** (`ln_robots_lag1`). **One appendix table** combines **CH-inclusive log robot stock** for **Eq. 1** and **Eq. 2 coord** — cite **§6.2.2** (sample) **and** **§6.2.3** (operationalisation) to the same artefact: [`wiod_regression_table_appendix_robot_stock_ch_inclusive.{md,tex}`](tables/wiod_regression_table_appendix_robot_stock_ch_inclusive.md). Current run: interaction ≈ **0.0149**, wild *p* ≈ **0.05** (`robust_robotstock_eq2_coord_key_terms.csv`).
- **Other appendix specs** (binary coordination, etc.): [`secondary/robustness/`](secondary/robustness/).
- **Multicollinearity audit:** `[secondary/wiod_vif_audit.md](secondary/wiod_vif_audit.md)`.

## Bottom line for drafting

TWFE yields **conditional associations**, not causal effects of institutions on the robot gradient without further design — frame coordination results as **consistent with adjustment under coordinated bargaining**. For the focal coordination interaction, **wild-cluster bootstrap** is the **single headline inference standard** (stars on `wiod_regression_table_combined`); cite **country-cluster *p*** only for transparency / appendix comparison (`inference_robustness/wiod_regression_table_combined_clusterstars`).

---

