# WIOD Eq. 2 coordination — country leave-one-out jackknife (GH #16)

Country jackknife (drop-one over the 25-country Eq. 2 coord sample, baseline beta_interaction = 0.0124, p_cluster = 0.0199). Across the 25 jackknife re-fits the interaction coefficient ranges 0.0079-0.0152 and the cluster p ranges 0.002-0.172; 23/25 jackknife fits are significant at p_cluster < 0.05. No sign flips across drops. Wild-cluster p (999 reps) ranges 0.038-0.190; 14/25 jackknife fits reject at the 10% wild-bootstrap level. Verdict: FRAGILE.

## Baseline (no country dropped)

- beta_interaction = 0.012445
- se_country_cluster = 0.005346
- p_cluster = 0.019907
- n_obs = 2500, n_entities = 247, n_countries = 25

## Per-country drops (sorted by beta_interaction, ascending)

| dropped_country | n_obs | n_countries | beta_interaction | se_cluster | p_cluster | p_wild |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HU | 2417 | 24 | 0.007886 | 0.005767 | 0.1715 | 0.190 |
| NO | 2362 | 24 | 0.010105 | 0.004797 | 0.0352 | 0.165 |
| EL | 2431 | 24 | 0.011270 | 0.005602 | 0.0443 | 0.154 |
| ES | 2350 | 24 | 0.011683 | 0.005200 | 0.0247 | 0.153 |
| NL | 2400 | 24 | 0.011736 | 0.006448 | 0.0688 | 0.183 |
| AT | 2392 | 24 | 0.011776 | 0.005368 | 0.0282 | 0.098 |
| EE | 2454 | 24 | 0.011980 | 0.005536 | 0.0305 | 0.124 |
| LT | 2457 | 24 | 0.012128 | 0.005785 | 0.0360 | 0.145 |
| BE | 2394 | 24 | 0.012253 | 0.005550 | 0.0273 | 0.120 |
| SE | 2352 | 24 | 0.012275 | 0.005406 | 0.0232 | 0.124 |
| FI | 2350 | 24 | 0.012302 | 0.005223 | 0.0185 | 0.095 |
| IT | 2350 | 24 | 0.012320 | 0.005370 | 0.0218 | 0.096 |
| MT | 2492 | 24 | 0.012463 | 0.005346 | 0.0197 | 0.098 |
| SK | 2421 | 24 | 0.012551 | 0.005188 | 0.0156 | 0.085 |
| FR | 2350 | 24 | 0.012594 | 0.005293 | 0.0173 | 0.111 |
| CZ | 2406 | 24 | 0.012598 | 0.005248 | 0.0164 | 0.091 |
| SI | 2409 | 24 | 0.012688 | 0.005446 | 0.0198 | 0.103 |
| DE | 2350 | 24 | 0.012697 | 0.005526 | 0.0216 | 0.093 |
| LV | 2468 | 24 | 0.012803 | 0.005426 | 0.0183 | 0.088 |
| UK | 2350 | 24 | 0.013020 | 0.005131 | 0.0112 | 0.072 |
| IE | 2431 | 24 | 0.013386 | 0.005602 | 0.0169 | 0.082 |
| PT | 2410 | 24 | 0.013443 | 0.005573 | 0.0158 | 0.086 |
| BG | 2447 | 24 | 0.013966 | 0.005233 | 0.0076 | 0.081 |
| PL | 2403 | 24 | 0.014498 | 0.005506 | 0.0085 | 0.076 |
| DK | 2354 | 24 | 0.015214 | 0.004990 | 0.0023 | 0.038 |
