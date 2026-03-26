# WIOD First Results Overview

Generated: 2026-03-26T21:20:15.026979+00:00

Frozen specification:
- Capital proxy: `k`
- Outcome: `ln_h_empe`
- Robot regressor: `ln_robots_lag1`
- Controls: `ln_va_wiod_qi`, selected capital proxy, `gdp_growth`
- Years: `2001-2014`
- Headline inference: country-clustered SEs + wild cluster bootstrap
- Wild cluster bootstrap reps: `199`

Review order:
## 1. EQ1 — WIOD Eq. 1 baseline
- Role: headline baseline
- Sample: 2283 obs, 236 entities, 24 countries, 2001-2014
- Focal term: `ln_robots_lag1`
- Coef / SE / p(cluster) / p(wild): 0.0091 / 0.0068 / 0.1800 / 0.2362
- Key terms CSV: `wiod_eq1_baseline_k_key_terms.csv`
- Results text: `wiod_eq1_baseline_k_results.txt`

## 2. EQ2_COORD — WIOD Eq. 2 coordination moderation
- Role: primary focal institutional result
- Sample: 2212 obs, 226 entities, 23 countries, 2001-2014
- Focal term: `ln_robots_lag1:coord_pre_c`
- Coef / SE / p(cluster) / p(wild): 0.0108 / 0.0046 / 0.0194 / 0.1206
- Key terms CSV: `primary_contribution_eq2_wiod_coord_full_k_continuous_key_terms.csv`
- Results text: `primary_contribution_eq2_wiod_coord_full_k_continuous_results.txt`

## 3. EQ2_ADJCOV — WIOD Eq. 2 adjusted coverage moderation
- Role: secondary focal restricted-sample result
- Sample: 1535 obs, 142 entities, 14 countries, 2001-2014
- Focal term: `ln_robots_lag1:adjcov_pre_c`
- Coef / SE / p(cluster) / p(wild): 0.0006 / 0.0005 / 0.2575 / 0.2563
- Key terms CSV: `secondary_focal_eq2_wiod_adjcov_common_k_continuous_key_terms.csv`
- Results text: `secondary_focal_eq2_wiod_adjcov_common_k_continuous_results.txt`

## 4. EQ2_UD — WIOD Eq. 2 union-density reference
- Role: reference benchmark institutional result
- Sample: 2068 obs, 206 entities, 21 countries, 2001-2014
- Focal term: `ln_robots_lag1:ud_pre_c`
- Coef / SE / p(cluster) / p(wild): -0.0001 / 0.0004 / 0.7943 / 0.8392
- Key terms CSV: `reference_benchmark_eq2_wiod_ud_full_k_continuous_key_terms.csv`
- Results text: `reference_benchmark_eq2_wiod_ud_full_k_continuous_results.txt`
