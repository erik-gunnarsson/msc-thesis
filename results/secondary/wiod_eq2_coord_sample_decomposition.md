# WIOD Eq. 2 Coordination Sample Decomposition

This diagnostic isolates whether the coordination attenuation in Eq. 2b is mainly due to moving from the broader coord sample to the exact joint-modulator intersection or due to adding union density and the three-way term on the same rows.

Interpretation: **mixed effect**

| comparison_id | title | n_countries | n_entities | n_observations | coef_country_cluster | se_country_cluster | p_country_cluster | p_wild_cluster | delta_vs_eq2_full_coef | delta_vs_eq2_full_p_wild | delta_vs_eq2b_coord_term_coef | delta_vs_eq2b_coord_term_p_wild |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EQ2_COORD_FULL | WIOD Eq. 2 coordination moderation (25-country full sample) | 25 | 247 | 2500 | 0.012445 | 0.005346 | 0.019907 | 0.108108 | 0.000000 | 0.000000 | 0.000785 | -0.364364 |
| EQ2_COORD_EQ2B_SAMPLE | WIOD Eq. 2 coordination moderation (exact Eq. 2b sample) | 23 | 227 | 2356 | 0.014210 | 0.005337 | 0.007758 | 0.101101 | 0.001764 | -0.007007 | 0.002549 | -0.371371 |
| EQ2B_COORD_TERM | WIOD Eq. 2b joint coord x ud moderation (coord term only) | 23 | 227 | 2356 | 0.011660 | 0.007992 | 0.144570 | 0.472472 | -0.000785 | 0.364364 | 0.000000 | 0.000000 |
