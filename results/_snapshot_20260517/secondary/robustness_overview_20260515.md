# Phase-3 robustness overview — 2026-05-15

Snapshot reference (`results/_snapshot_20260515/core/`):

- **Eq. 1 baseline (`wiod_eq1_baseline_k`)**: ln_robots_lag1 = **0.00964**, p_cluster = **0.119**, p_wild = **0.126** on 2 571 obs / 26 countries. The labour-input level coefficient is the WIOD null reference; we do not expect to recover significance on it.
- **Eq. 2 coord (`primary_contribution_eq2_wiod_coord_full_k_continuous`)**: interaction beta = **0.01244**, p_cluster = **0.0199**, p_wild = **0.108** on 2 500 obs / 25 countries. This is the thesis contribution claim and the target of every robustness check below.

All robustness reruns use 999 wild-cluster bootstrap reps (Rademacher, restricted residuals), the same convention as the snapshot, and write to `results/secondary/robustness/` or `results/secondary/`.

## Scoreboard

| GH | check | sample (n_obs / n_countries) | key coef | p_cluster | p_wild | verdict |
| --- | --- | --- | ---: | ---: | ---: | --- |
| #17a | Eq.1 excl 2008-2009 | 2 118 / 26 | 0.00927 | 0.181 | 0.181 | DIRECTIONALLY HOLDS (null stays null) |
| #17b | Eq.2 coord excl 2008-2009 | 2 059 / 25 | 0.01218 | **0.023** | 0.104 | HOLDS |
| #18a | Eq.1 CAP (capcomp) | 2 571 / 26 | 0.02195 | **0.001** | 0.008 | DIRECTION FLIP IN MAGNITUDE — cap proxy doubles the coef and turns Eq.1 significant; flags capital control mis-specification rather than a robustness pass |
| #18b | Eq.2 coord CAP (capcomp) | 2 500 / 25 | 0.00618 | 0.199 | 0.281 | FRAGILE (interaction halves and loses both cluster and wild significance under CAP) |
| #19 | Eq.2 binary coord (Coord >= 4) | 2 500 / 25 | 0.01110 | 0.408 | 0.439 | FRAGILE / NULL on binary recode (expected power loss, but worth flagging) |
| #20a | Eq.1 robot stock | 2 712 / 27 (CH included) | 0.01300 | 0.053 | 0.068 | DIRECTIONALLY HOLDS / STRENGTHENS (just below 5% cluster) |
| #20b | Eq.2 coord robot stock | 2 641 / 26 (CH included) | 0.01487 | **0.004** | **0.050** | HOLDS / STRENGTHENS (cleanest non-snapshot estimate) |
| #16 | Eq.2 coord country jackknife | drop-one over 25 countries | range 0.0079-0.0152 | range 0.002-0.172 | range 0.04-0.23 | HOLDS WITH HU SENSITIVITY (sign stable in 25/25, p_cluster < 0.05 in 23/25, dropping HU bumps p to 0.17) |
| #21 | CH alt-normalisation | n/a (negative-result note) | n/a | n/a | n/a | NEGATIVE RESULT — CH cannot be normalised on IFR sub-industry employment; #20 robot-stock rerun is the de-facto CH-inclusive substitute |
| #22 | VIF audit (Eq.1 / Eq.2 coord / Eq.2b) | 2 571 / 2 500 / 2 356 | max FE-style VIF = 1.741 | n/a | n/a | CLEAN — no regressor above the VIF=5 watch level on entity+year demeaned design |
| #4 | Bootstrap seed audit (Eq.2 coord interaction) | 2 500 / 25 | beta = 0.01245 | p_cluster = 0.0199 | p_wild range 0.1031-0.1181 across 4 seeds | STABLE — wild p is robust to seed; snapshot p_wild = 0.1081 reproduces exactly. Cluster-vs-wild gap of ~0.09 is the few-cluster correction, not a numerical artefact. |

**One-line read for Rebecka**: the coordination contribution survives the year-shock drop (#17), the robot-stock specification (#20), and the bootstrap seed audit (#4) cleanly; it is meaningfully sensitive to switching the capital control to CAP (#18b) and to dropping Hungary in the jackknife (#16); the binary recode (#19) is expectedly underpowered. VIF is not a binding concern (#22), and CH stays excluded with the robot-stock rerun as the closest substitute (#21).

---

## #17 Exclude 2008-2009 (year-shock drop)

Source files:
- `results/secondary/robustness/robust_excl0809_eq1_baseline_k_*`
- `results/secondary/robustness/robust_excl0809_eq2_coord_*`

**Eq. 1 (labour-input level)**: dropping 2008 and 2009 leaves 2 118 obs across the same 26 countries. ln_robots_lag1 = 0.00927 (vs snapshot 0.00964), p_cluster = 0.181, p_wild = 0.181. The point estimate is essentially identical to the snapshot and remains insignificant; the labour-input null reference is unaffected by the GFC years. Verdict: **DIRECTIONALLY HOLDS**.

**Eq. 2 coord (contribution claim)**: 2 059 obs / 25 countries. ln_robots_lag1:coord_pre_c = 0.01218 (vs snapshot 0.01245), p_cluster = 0.023, p_wild = 0.104. The interaction coefficient barely moves once the GFC years are removed and the wild bootstrap p stays essentially at the snapshot value (0.104 vs 0.108). Verdict: **HOLDS** — the contribution is not a 2008-2009 artefact.

## #18 CAP vs K (capital control sensitivity)

Source files:
- `results/secondary/robustness/robust_capcomp_eq1_baseline_*`
- `results/secondary/robustness/robust_capcomp_eq2_coord_*`

**Eq. 1**: substituting `ln_capcomp_wiod` (capital compensation) for `ln_k_wiod` (capital stock) on the full sample raises ln_robots_lag1 from 0.00964 to **0.02195** and pushes p_cluster from 0.119 to 0.001, with p_wild = 0.008. This is not a typical robustness pass — it is a meaningful sensitivity to the capital control. Because the two controls absorb different shares of the labour-input variation, the Eq. 1 null is conditional on the capital stock specification. Reporting recommendation: keep K as the headline capital control and flag the CAP rerun as a known sensitivity in the table caption (it strengthens the level coefficient rather than killing it).

**Eq. 2 coord**: the interaction coefficient halves from 0.01244 to 0.00618 and loses significance (p_cluster = 0.199, p_wild = 0.281). This is the **most important fragility** in the battery: the contribution claim is meaningfully attenuated when capital compensation replaces capital stock as the control. Verdict: **FRAGILE**. This should be presented in the thesis text as an explicit sensitivity, with the WIOD comparability rows from `control_comparability_rows()` already explaining why CAP is a noisier capital proxy.

## #19 Binary coord moderator (Coord >= 4)

Source file:
- `results/secondary/robustness/robust_binarycoord_eq2_coord_*`

Recoding the moderator from the continuous centred ICTWSS Coord score to a binary "high-coord" indicator (Coord >= 4) yields ln_robots_lag1:high_coord_pre = 0.01110, p_cluster = 0.408, p_wild = 0.439, on the same 2 500 obs / 25 countries. The point estimate keeps the same direction but the binary recode collapses cross-country variation to two categories and noisier inference, so significance evaporates. Verdict: **FRAGILE / NULL on binary recode** — best read as a "the continuous Coord variation is doing the work" diagnostic rather than as a true robustness failure of the underlying mechanism.

## #20 Robot stock instead of intensity

**GH #29 packaging:** thesis appendix table combining Eq. 1 + Eq. 2 coord stock columns — `results/tables/wiod_regression_table_appendix_robot_stock_ch_inclusive.{md,tex,csv}` (same artefact referenced from §6.2.2 **and** §6.2.3).

Source files:
- `results/secondary/robustness/robust_robotstock_eq1_baseline_*`
- `results/secondary/robustness/robust_robotstock_eq2_coord_*`

**Eq. 1**: switching the regressor from per-worker robot intensity (`ln_robots_lag1`) to log robot stock (`ln_robot_stock_lag1`) **brings CH back in** (27-country sample, 2 712 obs). ln_robot_stock_lag1 = 0.01300, p_cluster = 0.053, p_wild = 0.068. This is the cleanest Eq. 1 estimate in the battery and sits right on the conventional 5% threshold. Verdict: **DIRECTIONALLY HOLDS / STRENGTHENS** — the level effect is borderline-significant rather than null when measured on stocks instead of per-worker intensity.

**Eq. 2 coord**: 2 641 obs / 26 countries with CH included. ln_robot_stock_lag1:coord_pre_c = **0.01487**, p_cluster = 0.004, p_wild = 0.050. Verdict: **HOLDS / STRENGTHENS** — the contribution is at least as strong on the stock specification, and the wild bootstrap p sits right at conventional significance with the broader country panel. This is the strongest auxiliary evidence in the battery; GH #21 documents why headline intensity cannot include CH, while this specification delivers the CH-inclusive substitute in the appendix table above.

## #16 Country leave-one-out jackknife — Eq. 2 coord

Source files:
- `results/secondary/wiod_jackknife_eq2_coord.csv`
- `results/secondary/wiod_jackknife_eq2_coord.md`

Drop-one jackknife over the 25-country Eq. 2 coord sample, using 199 wild-cluster bootstrap reps per fit (smaller than the headline 999 to fit the time budget; noted in the .md). Across the 25 re-fits the interaction coefficient ranges 0.0079 (drop HU) to 0.0152 (drop DK), p_cluster ranges 0.0023 to 0.1715, p_wild ranges 0.040 to 0.226. **No sign flips across any drop.** 23 of 25 jackknife fits remain significant at p_cluster < 0.05; the two exceptions are dropping HU (p_cluster = 0.17, p_wild = 0.23) and dropping NL (p_cluster = 0.07, p_wild = 0.19). Dropping DK alone produces the strongest version of the result (p_cluster = 0.002, p_wild = 0.040).

Verdict: **HOLDS WITH HU SENSITIVITY**. The sign of the contribution is fully stable, and the effect is not driven by any single country, but the headline significance is sensitive to Hungary. A safe write-up is to keep the 25-country headline and note in a footnote that the wild bootstrap p ranges 0.04-0.23 across leave-one-out drops, with HU as the single most influential observation.

## #21 CH alt-normalisation

Source file:
- `results/secondary/wiod_ch_alt_normalisation.md`

Switzerland is structurally excluded from the headline panel because the IFR data ships zero rows of `robot_wrkr_stock_95` for CH (the per-worker normalisation we use everywhere else). Every alternative denominator we considered either collapses to a single sub-industry-invariant manufacturing aggregate, re-uses the LHS variable as the RHS denominator (mechanical link), or is unavailable at sub-industry granularity for CH in 1995. **CH stays excluded from the headline intensity specification**; **GH #29** publishes the CH-inclusive **log-stock** Eq. 1 + Eq. 2 coord estimates as one appendix table (`wiod_regression_table_appendix_robot_stock_ch_inclusive.*`), consistent with the measurement audit below.

Verdict: **NEGATIVE RESULT on alternative intensity denominators** (documented); **positive delivered substitute** via robot-stock appendix column pair.

## #22 VIF audit (Eq. 1 / Eq. 2 coord / Eq. 2b coord x ud)

Source files:
- `results/secondary/wiod_vif_audit.csv`
- `results/secondary/wiod_vif_audit.md`

We compute variance inflation factors on entity + year two-way demeaned regressors so that the reported numbers reflect within-FE collinearity, not the well-known FE-induced VIF inflation. The maximum FE-style VIF across the three active equations is **1.741** (Eq. 2 coord, ln_robots_lag1). Every regressor sits well below the VIF=5 watch level and orders of magnitude below the VIF=10 rule-of-thumb.

Verdict: **CLEAN**. Multicollinearity is not the binding inference concern for any of the three active equations. The previously-reported Eq. 2b interaction VIFs (`results/archive/exploration/wiod_feasibility/wiod_eq2b_coord_ud_vif.csv`, max 1.38; live reruns also write `results/exploration/wiod_feasibility/`) are consistent with this audit.

## #4 Wild-cluster bootstrap seed audit (Eq. 2 coord interaction)

Source files:
- `results/secondary/bootstrap_audit_eq2_coord.csv`
- `results/secondary/bootstrap_audit_eq2_coord.md`

Re-derives p_wild for `ln_robots_lag1:coord_pre_c` at 999 reps each across base seeds 123 (snapshot), 7, 31, 42. The snapshot reproduces exactly (p_wild = 0.1081 vs the snapshot 0.10811), and the other three seeds give p_wild = 0.1041, 0.1181, 0.1031. **Range across four seeds: 0.103-0.118 (~1.5 percentage points).** The wild bootstrap is therefore not seed-fragile.

The cluster-vs-wild gap (p_cluster = 0.0199 vs p_wild ~ 0.108) is approximately 0.09 and is the few-cluster correction expected with ~25 country clusters (Cameron-Gelbach-Miller 2008, MacKinnon-Webb 2017): the asymptotic cluster sandwich under-rejects in this regime and the wild bootstrap is the conservative reference. **Reporting recommendation**: headline the wild-cluster bootstrap p in the regression table (label: `p_wild_cluster (999 reps, seed=123)`) and keep p_cluster as a secondary column. The table caption should explicitly state that with 25 country clusters the wild bootstrap is the conservative reference (feeds the table-policy decision in GH #9).

Verdict: **STABLE** — bootstrap inference is not a knife-edge call and the wild-bootstrap p is the right number to lead with.

---

## Reporting plan for the 14:00 meeting

1. Lead with the contribution claim: Eq. 2 coord interaction beta = 0.01244, p_wild = 0.108 (seed-stable; snapshot reproduces). The number is borderline-significant under the conservative wild bootstrap and clearly significant under the country-cluster sandwich.
2. Robustness that the contribution **holds**: year-shock drop (#17b), robot-stock specification (#20b — which is also the CH-inclusive specification, see #21), bootstrap seed audit (#4), VIF audit (#22), jackknife sign stability across all 25 drops (#16).
3. Robustness that the contribution is **sensitive to**: CAP vs K capital control (#18b, the interaction halves), the Hungary jackknife (#16, one of 25 drops bumps p_cluster to 0.17), and the binary moderator recode (#19, expected loss of power but worth flagging).
4. **GH #30 (closed):** thesis **headline = `K`**, full **2001–2014**; **appendix-only** sensitivities for **`--exclude-years 2008 2009`** (interaction ~stable at ~**0.012**) and **`--capital-proxy capcomp`** (interaction **attenuates** — report transparently). Placement + prose templates: [`README.md`](../../README.md) § Thesis vs appendix specification defaults; [`results/RESULTS_BRIEF.md`](../RESULTS_BRIEF.md); [`results/interpretation_memo.md`](../interpretation_memo.md) §6.2.4.
5. Open follow-up (optional): whether to elevate **#20b** (robot stock + CH) to co-headline status given how clean it is — separate from capital-proxy placement.
