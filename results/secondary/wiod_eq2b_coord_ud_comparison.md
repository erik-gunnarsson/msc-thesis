# WIOD Eq. 2b Comparison

This table compares the current first-results package to the exploratory joint coord x ud extension.

| model_id | title | term_label | n_countries | n_entities | n_observations | coef_country_cluster | se_country_cluster | p_country_cluster | p_wild_cluster |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EQ1 | WIOD Eq. 1 baseline | ln_robots_lag1 | 24 | 236 | 2283 | 0.009068 | 0.006763 | 0.179990 | 0.236181 |
| EQ2_COORD | WIOD Eq. 2 coordination moderation | ln_robots_lag1:coord_pre_c | 23 | 226 | 2212 | 0.010767 | 0.004605 | 0.019383 | 0.120603 |
| EQ2B_COORD_UD | WIOD Eq. 2b joint coord x ud moderation | Eq. 2b coord slope term | 21 | 206 | 2068 | 0.008792 | 0.007008 | 0.209616 | 0.567839 |
| EQ2_UD | WIOD Eq. 2 union-density reference | ln_robots_lag1:ud_pre_c | 21 | 206 | 2068 | -0.000106 | 0.000407 | 0.794266 | 0.839196 |
| EQ2B_COORD_UD | WIOD Eq. 2b joint coord x ud moderation | Eq. 2b ud slope term | 21 | 206 | 2068 | 0.000048 | 0.000386 | 0.901457 | 0.889447 |
| EQ2B_COORD_UD | WIOD Eq. 2b joint coord x ud moderation | Eq. 2b Hawk-Dove three-way term | 21 | 206 | 2068 | -0.000554 | 0.000461 | 0.229392 | 0.402010 |
