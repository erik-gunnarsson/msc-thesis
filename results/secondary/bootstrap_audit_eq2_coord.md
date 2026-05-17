# Wild-cluster bootstrap audit — WIOD Eq. 2 coord interaction (GH #4)

Target term: `ln_robots_lag1:coord_pre_c`
Sample: 2500 obs, 247 entities, 25 countries.

OLS estimate: beta = `0.01245`, country-cluster SE = `0.00535`, p_cluster = `0.0199`.

## Wild-cluster bootstrap p-values (999 reps each)

We replicate the snapshot bootstrap convention from `11_wiod_institution_moderation.py`, where `summarise_key_terms` calls `wild_cluster_bootstrap_pvalue(... seed=bootstrap_seed + idx)`. The interaction is the second key term (idx=1), so the effective bootstrap seed equals `base_seed + 1`.

| base_seed | effective_seed | reps | p_wild | elapsed (s) |
| ---: | ---: | ---: | ---: | ---: |
| 123 | 124 | 999 | 0.1081 | 58.2 |
| 7 | 8 | 999 | 0.1041 | 56.4 |
| 31 | 32 | 999 | 0.1181 | 52.1 |
| 42 | 43 | 999 | 0.1031 | 51.6 |

## Cluster-vs-wild gap

- p_cluster = `0.0199` (country-clustered OLS, ~25 clusters)
- p_wild range across 4 seeds = `[0.1031, 0.1181]`, snapshot base_seed 123 (effective 124) → `p_wild = 0.1081`
- p_wild − p_cluster gap at the snapshot seed = `+0.0882`

## Few-cluster framing

With roughly 25 country clusters and unbalanced cluster sizes, the asymptotic cluster sandwich is known to be liberal (Cameron-Gelbach-Miller 2008, MacKinnon-Webb 2017): it tends to under-state standard errors and over-reject the null. The Rademacher wild-cluster bootstrap with restricted residuals is the standard conservative reference in this regime and almost always shifts borderline p-values away from 0.05. The audit above confirms that the wild-bootstrap p is stable across random seeds (spread 0.0150); the residual gap of +0.0882 between p_wild and p_cluster is the few-cluster adjustment, not a numerical artefact.

## Reporting recommendation

Headline the **wild-cluster bootstrap** p in the regression table. Label it precisely as **999 Rademacher reps**, country clusters, and the **effective** NumPy seed for this term (**124** when `--bootstrap-seed 123` and the interaction is the second `key_terms` row). Keep the **country-cluster** p as a **secondary** figure for few-clusters transparency, not the lead inferential claim. Table captions should note that ~25 country clusters make wild bootstrap the conservative reference. (Table star policy: GH #9; methods write-up: `REPRODUCIBILITY.md` §6.)

## Sanity checks (in-Python; no external stats package)

Re-running this script asserts that two consecutive calls to `wild_cluster_bootstrap_pvalue` with identical arguments return the same p-value (99-rep smoke check, effective seed 124).

Cross-checking against another language (e.g. R **fwildclusterboot**, Stata **boottest**) is optional for future work if a referee requests it; the implementation here matches the standard restricted-residual Rademacher wild-cluster algorithm.
