# WIOD Labour Extension Note

The outcome remains labour input, not exports. The WIOD extension uses `H_EMPE`
as a broader-coverage labour-hours measure, while WIOD trade is used only to
classify exposed versus sheltered industries.

Current WIOD labour support with default controls (`ln_va_wiod_qi`, `ln_k_wiod`,
`gdp_growth`) is:

- Base panel: 24 countries, 236 entities, 2283 observations (2001-2014)
- Eq. 4 bucket x ud: 21 countries, 2068 observations
- Eq. 4 bucket x coord: 23 countries, 2212 observations
- Eq. 5a exposure: 24 countries, 2283 observations
- Eq. 5b exposure x ud: 21 countries, 2068 observations
- Eq. 5b exposure x coord: 23 countries, 2212 observations

Bucket models remain estimable in pooled form, but the thin-bucket concern is
real at the country-support level. In the shared `ud + coord` reference sample,
bucket country counts are: B1=20, B2=19, B3=19, B4=20, B5=21. That means the issue is more about
precision than identification.

Exposure comparison support on the same labour panel is:

```
exposure_group  n_countries  n_entities  n_observations                                                                     countries_list
       exposed           20         110            1138     AT, BE, CZ, DE, DK, EE, EL, ES, FI, FR, HU, IE, IT, LT, LV, NL, PL, PT, SE, SK
     sheltered           21          96             930 AT, BE, CZ, DE, DK, EE, EL, ES, FI, FR, HU, IE, IT, LT, LV, MT, NL, PL, PT, SE, SK
```

Control comparability is not one-to-one. `LAB_QI` and `H_EMPE` belong to the
same labour-input family but are measured differently. `VA_PYP` and `VA_QI` are
reasonably comparable real-output controls, while `CAP_QI` is not directly
comparable to either WIOD `K` or `CAP`. Any KLEMS-WIOD comparison should
therefore be presented as a joint measure-and-controls robustness check.

Recommended framing:

- Main WIOD extension: bucket heterogeneity with labour input outcome
- Parsimonious comparison: exposed/sheltered on the same WIOD labour panel
- Headline inference for institution models: country clustering with wild
  cluster bootstrap p-values on the key interaction terms; entity-clustered and
  Driscoll-Kraay results are secondary robustness checks
