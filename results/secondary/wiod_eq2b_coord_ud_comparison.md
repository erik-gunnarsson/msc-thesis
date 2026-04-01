# WIOD Eq. 2b Comparison

This table compares the current first-results package to the exploratory joint coord x ud extension.

| model_id | title | term_label | n_countries | n_entities | n_observations | coef_country_cluster | se_country_cluster | p_country_cluster | p_wild_cluster |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EQ1 | WIOD Eq. 1 baseline | ln_robots_lag1 | 26 | 257 | 2571 | 0.009645 | 0.006182 | 0.118699 | 0.145729 |
| EQ2_COORD | WIOD Eq. 2 coordination moderation | ln_robots_lag1:coord_pre_c | 25 | 247 | 2500 | 0.012445 | 0.005346 | 0.019907 | 0.155779 |
| EQ2B_COORD_UD | WIOD Eq. 2b joint coord x ud moderation | Eq. 2b coord slope term | 23 | 227 | 2356 | 0.011660 | 0.007992 | 0.144570 | 0.467337 |
| EQ2_UD | WIOD Eq. 2 union-density reference | ln_robots_lag1:ud_pre_c | 23 | 227 | 2356 | -0.000032 | 0.000411 | 0.938738 | 0.949749 |
| EQ2B_COORD_UD | WIOD Eq. 2b joint coord x ud moderation | Eq. 2b ud slope term | 23 | 227 | 2356 | -0.000006 | 0.000363 | 0.986850 | 0.979899 |
| EQ2B_COORD_UD | WIOD Eq. 2b joint coord x ud moderation | Eq. 2b Hawk-Dove three-way term | 23 | 227 | 2356 | -0.000411 | 0.000492 | 0.403424 | 0.532663 |
