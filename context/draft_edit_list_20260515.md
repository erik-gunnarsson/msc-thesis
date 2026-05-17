# Draft edit checklist — `Master Thesis Draft - May 15.pdf` vs current pipeline

Apply in Google Docs / Word. Do **not** treat the March 26 inline staging notes as authoritative — the repo is.

## Cross-cutting

- Remove visible `XX`, `CLEAN UP`, `UPDATED AS OF MARCH 26`, `create visual?`, and `Remove ADJCOV completely?` markers once each item below is done.

## §4.1 Research design

- Replace “EU manufacturing countries only” with **European candidate universe**: the empirical sample is **not** a hard EU-27 cutoff; **UK** and **NO** appear in headline models (see README + `wiod_first_results_summary.csv`).
- Panel years: analysis window **2001–2014** (not “2000–2014” for regressions; 2000 is consumed by the robot lag). Opening sentence can still mention WIOD **release** coverage 2000–2014 if you clarify first regression year is 2001.

## §4.2.2 Employment / outcome (critical)

- **Delete** the paragraph that treats **gross exports** as the primary outcome. The active outcome is **log employee hours `H_EMPE`** from **WIOD SEA** (`ln_h_empe`), aligned with §5.2.1 and the code.

## §4.2.3 ICTWSS / institutional freeze

- **Every** mention of the institutional baseline must say **1990–1995** (country-level means from ICTWSS, then frozen). **Remove** the example “e.g. 2000–2005” — it contradicts Stage 3 in §4.3.1 and the code (`code/_wiod_panel_utils.py`).
- Table notes and footnotes should say **1990–1995** explicitly (matches `results/tables/*combined*.md` after regen).

## §4.2.4–4.2.6 Macro and control summary table

- Replace GDP **“XXX”** with **Eurostat** national-accounts GDP (file `eurostata_gdp_nama_10_gdp.csv` in repo; indicator `nama_10_gdp` / B1GQ chain as implemented).
- §4.2.6: **delete** the row claiming separate **Country FE**, **Industry FE**, and **Year FE** as standalone FE. The regressions use **country-industry FE** (`entity`) **plus year FE** — two-way FE, not three separate dimensions.
- Rename / redefine `ln_cap`: the default capital control is **WIOD SEA capital stock `K`** (`ln_k_wiod`), not generically “capital compensation.” CAP (`ln_capcomp_wiod`) is a **robustness** control (`results/secondary/robustness/robust_capcomp_*`).
- **AdjCov role:** in the moderator bullets, swap labels to match code/README: **coord** = primary; **ud** = reference benchmark; **adjcov** = secondary focal on restricted common sample — not “benchmark vs secondary” as currently drafted.

## §4.3.1 Merging — Stage 3

- Stage 3 already states 1990–1995; ensure **no** other section repeats a different window.

## §4.3.2–4.3.3 Sample sizes and nesting

Replace the pre-expansion **23-country / 21-country Eq. 2b** narrative with **per-equation** facts from `results/core/wiod_first_results_summary.csv`:

| Specification | Countries | Entities | Observations |
|---------------|-----------|----------|--------------|
| Eq. 1 | 26 | 257 | 2571 |
| Eq. 2 coord | 25 | 247 | 2500 |
| Eq. 2 ud | 23 | 227 | 2356 |
| Eq. 2 adjcov (common) | 15 | 153 | 1685 |
| Eq. 2b / common-sample stack | 23 | 227 | 2356 |

- **Drop** the claim that **RO** and **SK** alone drive Eq. 2b sample size in the current ICTWSS merge — refresh country lists from `sample_manifest_*` files if you need ISO lists in prose.
- **AdjCov decision:** keep as **secondary focal** on the **restricted 15-country** common sample; add one honest sentence on **few clusters**.

## §5.3 / Appendix 2 — Decomposition table

- Replace stale coefficients (**0.0108 / 0.0128 / 0.0088**, 21-country framing) with current decomposition (`results/secondary/wiod_eq2_coord_sample_decomposition.md`): **0.012445 / 0.014210 / 0.011660**; p_wild **0.108 / 0.101 / 0.472**; **23-country** Eq. 2b intersection.

## §6.2 Robustness (prose must match repo)

- **Inference:** reference `results/secondary/bootstrap_audit_eq2_coord.md` and **lead** with **p_wild** for the focal coordination interaction in §6.1.3 (headline prose matches canonical table stars). Use **p_cluster** **only** in §6.2 / appendix when discussing asymptotic-vs-bootstrap comparison; point optionally to `results/secondary/inference_robustness/wiod_regression_table_combined_clusterstars.tex` rather than implying two equal starring conventions in core tables.

- §6.1.3 main-text wording for Eq. 2 coordination: **wild-bootstrap *p*** is the headline number; do not lead sentences with asymptotic cluster *p*.
- **Sample:** jackknife → `wiod_jackknife_eq2_coord.md`; common-sample → `wiod_common_sample_robustness.md`; CH → `wiod_ch_alt_normalisation.md`.
- **Specification:** CAP vs K, binary coordination, exclude 2008–2009, robot **stock** spec → under `results/secondary/robustness/`.
- **VIF:** `wiod_vif_audit.md` (+ gate `wiod_eq2b_coord_ud_vif.csv`).

## References / consistency

- Hypotheses H2–H4 still refer to **unemployment** in places; your estimand is **Hours / `H_EMPE`** in the WIOD chapter. Either relabel hypotheses to **labour input / hours** or add one explicit bridge sentence that the empirical proxy is hours, not U.
