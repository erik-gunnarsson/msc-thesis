# CH alt-normalisation note (GH #21)

**Thesis-facing recovery of CH:** bundled Eq. 1 + Eq. 2 coord estimates using **`ln_robot_stock_lag1`** (CH-inclusive) live in [`results/tables/wiod_regression_table_appendix_robot_stock_ch_inclusive.{md,tex,csv}`](../tables/wiod_regression_table_appendix_robot_stock_ch_inclusive.md) — single appendix cross-reference for §6.2.2 and §6.2.3 (GH #29). This note documents why **per-worker intensity** cannot be built for CH under the IFR extract.

## TL;DR

Switzerland (CH) is structurally excluded from the headline robot-intensity
panel because the IFR data we use does not ship a per-worker normalisation
for Swiss sub-industries. Every alternative denominator we can construct
from the data we have (total manufacturing IFR employment, KLEMS hours,
WIOD H_EMPE) is either degenerate (collapses to a single sector aggregate),
mechanically introduces a different measurement object (no longer
"installed robots per worker in industry i"), or relies on a series CH
does not provide in the relevant years. The conservative robustness
statement is therefore: **CH stays excluded from the headline Eq. 1 and
Eq. 2 intensity specifications**, and the substitute that restores CH consistently is the **GH #29 appendix robot-stock table** (paired Eq. 1 + Eq. 2 coord columns).

## Why the headline panel drops CH

The headline regressor is

    ln_robots_lag1 = log(robot_wrkr_stock_95)_{t-1}

where `robot_wrkr_stock_95` is the per-worker robot stock that Karol's IFR
extract (`data/IFR_karol.csv`) ships at the IFR sub-industry level,
normalised on IFR sub-industry employment in 1995.

Diagnosing the raw panel directly (see the `head_alt_norm` slice in
`code/_wiod_panel_utils.py::load_ifr_panel`):

| metric                        | CH         | typical EU country (e.g. DE) |
| ----------------------------- | ---------- | ---------------------------- |
| rows in panel                 | 165        | 165                          |
| `ln_h_empe` non-NA            | 165 / 165  | full                         |
| `ln_robots_lag1` non-NA       | **0 / 165**| full                         |
| `ln_robot_stock_lag1` non-NA  | 109 / 165  | full                         |
| `coord_pre`, `ud_pre`         | non-NA     | non-NA                       |
| WIOD `K`, `VA_QI`, `CAP`      | non-NA     | non-NA                       |

CH is the only WIOD-Europe country that has WIOD SEA labour and capital
data but zero rows of usable `ln_robots_lag1`. Everything else (capital,
output, ICTWSS moderators, IFR robot **stocks**) is available — the missing
ingredient is specifically the IFR per-worker normalisation series.

## Alt denominators we considered

For CH to be added back to the headline intensity specification we would
need a denominator $D_{i,c,1995}$ that

1. Matches the IFR sub-industry granularity used in the rest of the panel
   (otherwise the normalisation object differs across countries).
2. Is available for Switzerland in 1995, ideally in the same source that
   defines the 28 other countries.
3. Is conceptually "employment in the same sub-industry that the IFR
   reports robots for", not a coarser aggregate.

The candidates we evaluated:

- **Total manufacturing IFR employment for CH (1995 IFR aggregate)**.
  Operationally collapses the per-worker denominator to a country-level
  scalar; every CH sub-industry would share the same denominator, which
  destroys the across-industry variation that the headline normalisation
  is supposed to preserve. We rejected this because the resulting
  "intensity" series for CH is no longer comparable to the other
  countries' per-sub-industry series; including it would mechanically
  attenuate the headline coefficient through measurement noise rather
  than economic content.

- **KLEMS hours (H_EMP or H_EMPE) at the CH-by-sub-industry level**.
  CH has KLEMS coverage in WIOD SEA (we use H_EMPE as the outcome
  variable), but using H_EMPE as both the normalisation denominator
  for the regressor AND the outcome introduces a mechanical
  by-construction relationship between LHS and RHS that the rest of the
  panel does not have. This is a worse measurement choice than simply
  reporting the stock specification.

- **WIOD H_EMPE itself (employees rather than hours) for 1995**.
  Same mechanical-link problem as KLEMS hours; H_EMPE is the LHS
  variable. Rejected.

- **EU-KLEMS national accounts headcount for 1995**.
  Not available at the IFR sub-industry granularity for CH in the
  1995 release; pre-merging at a coarser level reproduces the
  manufacturing-aggregate problem above.

## Verdict

CH stays excluded from the headline Eq. 1 and Eq. 2 specifications. This
is itself the robustness statement: the headline specification cannot be
estimated on CH without changing the measurement object of the right-hand
side regressor, and every workable alternative either trivialises the
across-industry variation in the denominator or introduces a mechanical
LHS/RHS link.

The closest CH-inclusive specification we can deliver without
re-normalising is the GH #20 robot-stock rerun
(`results/secondary/robustness/robust_robotstock_eq1_baseline_*` and
`robust_robotstock_eq2_coord_*`), where the regressor is
`ln_robot_stock_lag1` rather than `ln_robots_lag1`. That specification
mechanically brings CH back into both Eq. 1 (27 countries) and Eq. 2
coord (26 countries), and the resulting coefficients are reported in the
robustness overview. This is the de-facto CH-inclusive robustness check
that the data permit.
