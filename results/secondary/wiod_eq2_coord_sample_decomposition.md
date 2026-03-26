# WIOD Eq. 2 Coordination Sample Decomposition

This diagnostic isolates whether the coordination attenuation in Eq. 2b is mainly due to losing two countries or due to adding union density and the three-way term on the same rows.

Interpretation: **mixed effect**

| comparison_id | title | n_countries | n_entities | n_observations | coef_country_cluster | se_country_cluster | p_country_cluster | p_wild_cluster | delta_vs_eq2_full_coef | delta_vs_eq2_full_p_wild | delta_vs_eq2b_coord_term_coef | delta_vs_eq2b_coord_term_p_wild |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EQ2_COORD_FULL | WIOD Eq. 2 coordination moderation (23-country full sample) | 23 | 226 | 2212 | 0.010767 | 0.004605 | 0.019383 | 0.120603 | 0.000000 | 0.000000 | 0.001975 | -0.447236 |
| EQ2_COORD_EQ2B_SAMPLE | WIOD Eq. 2 coordination moderation (exact Eq. 2b sample) | 21 | 206 | 2068 | 0.012753 | 0.004426 | 0.003958 | 0.095477 | 0.001986 | -0.025126 | 0.003960 | -0.472362 |
| EQ2B_COORD_TERM | WIOD Eq. 2b joint coord x ud moderation (coord term only) | 21 | 206 | 2068 | 0.008792 | 0.007008 | 0.209616 | 0.567839 | -0.001975 | 0.447236 | 0.000000 | 0.000000 |
