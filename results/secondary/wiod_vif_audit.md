# WIOD VIF audit (GH #22)

VIFs are computed on two-way demeaned (entity + year) regressors so that the reported numbers reflect within-FE collinearity, not the well-known FE-induced inflation of raw VIFs. Across all three active specifications the maximum FE-style VIF is 2.02. Eq. 1 and Eq. 2 coord stay well below conventional cutoffs (max FE-style VIF 1.74). The Eq. 2b coord×ud specification includes the full robot interaction block; within-FE VIFs remain modest (max 2.02).

Definition: each regressor is two-way demeaned by entity and year before computing the variance inflation factor, mirroring the two-way FE absorption in the active OLS specifications.

## EQ1_BASELINE

n_obs_used = 2571

| term | VIF |
| --- | ---: |
| ln_k_wiod | 1.702 |
| ln_robots_lag1 | 1.670 |
| ln_va_wiod_qi | 1.035 |
| gdp_growth | 1.010 |

## EQ2_COORD

n_obs_used = 2500

| term | VIF |
| --- | ---: |
| ln_robots_lag1 | 1.741 |
| ln_k_wiod | 1.657 |
| ln_robots_lag1_x_coord_pre_c | 1.107 |
| ln_va_wiod_qi | 1.030 |
| gdp_growth | 1.015 |

## EQ2B_COORD_UD

n_obs_used = 2356

| term | VIF |
| --- | ---: |
| ln_robots_lag1 | 2.023 |
| ln_robots_lag1_x_coord_pre_c_x_ud_pre_c | 1.904 |
| ln_robots_lag1_x_coord_pre_c | 1.627 |
| ln_k_wiod | 1.584 |
| ln_robots_lag1_x_ud_pre_c | 1.584 |
| ln_va_wiod_qi | 1.047 |
| gdp_growth | 1.011 |

