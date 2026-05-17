# WIOD First Results Overview

Generated: 2026-05-17T14:44:50.616289+00:00

Frozen specification:
- Capital proxy: `k`
- Outcome: `ln_h_empe`
- Robot regressor: `ln_robots_lag1`
- Controls: `ln_va_wiod_qi`, selected capital proxy, `gdp_growth`
- Years: `2001-2014`
- Headline inference: country-clustered SEs + wild cluster bootstrap
- Wild cluster bootstrap reps: `999`

Review order:
## 1. EQ1 — WIOD Eq. 1 baseline
- Role: headline baseline
- Sample: 2571 obs, 257 entities, 26 countries, 2001-2014
- Focal term: `ln_robots_lag1`
- Coef / SE / p(cluster) / p(wild): 0.0096 / 0.0062 / 0.1187 / 0.1261
- Key terms CSV: `wiod_eq1_baseline_k_key_terms.csv`
- Results text: `wiod_eq1_baseline_k_results.txt`

## 2. EQ2_COORD — WIOD Eq. 2 coordination moderation
- Role: primary focal institutional result
- Sample: 2500 obs, 247 entities, 25 countries, 2001-2014
- Focal term: `ln_robots_lag1:coord_pre_c`
- Coef / SE / p(cluster) / p(wild): 0.0124 / 0.0053 / 0.0199 / 0.1081
- Key terms CSV: `primary_contribution_eq2_wiod_coord_full_k_continuous_key_terms.csv`
- Results text: `primary_contribution_eq2_wiod_coord_full_k_continuous_results.txt`

## 3. EQ2_ADJCOV — WIOD Eq. 2 adjusted coverage moderation
- Role: secondary focal restricted-sample result
- Sample: 1685 obs, 153 entities, 15 countries, 2001-2014
- Focal term: `ln_robots_lag1:adjcov_pre_c`
- Coef / SE / p(cluster) / p(wild): 0.0003 / 0.0004 / 0.5208 / 0.5085
- Key terms CSV: `secondary_focal_eq2_wiod_adjcov_common_k_continuous_key_terms.csv`
- Results text: `secondary_focal_eq2_wiod_adjcov_common_k_continuous_results.txt`

## 4. EQ2_UD — WIOD Eq. 2 union-density reference
- Role: reference benchmark institutional result
- Sample: 2356 obs, 227 entities, 23 countries, 2001-2014
- Focal term: `ln_robots_lag1:ud_pre_c`
- Coef / SE / p(cluster) / p(wild): -0.0000 / 0.0004 / 0.9387 / 0.9550
- Key terms CSV: `reference_benchmark_eq2_wiod_ud_full_k_continuous_key_terms.csv`
- Results text: `reference_benchmark_eq2_wiod_ud_full_k_continuous_results.txt`
