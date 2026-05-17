### Meeting agenda (Rebecka, 15 May 2026) — Q8

**Question:** Capital proxy `K` vs `CAP`, and whether 2008–2009 exclusion belongs in the main table or appendix.

**Code:** Default `K` (WIOD SEA capital stock); `--capital-proxy capcomp` and `--exclude-years 2008 2009` are wired in the regression scripts.

**Instinct:** `K` thesis-facing + `CAP` appendix; pre-crisis subsample appendix-only unless she wants a §6.2.4 column.

### Live notes

- Locked **without** supervisor sign-off per GH #30: headline **`K`** + full window; **`CAP`** and **drop 2008–2009** are **appendix-only** with §6.2.4 forward reference (Table A.X placeholder).

### Decision / next action

- **Capital:** **`K`** main tables — Graetz & Michaels-style stock benchmark; **`CAP`** appendix — flow vs VA overlap; interaction **attenuates** under **`CAP`** (report honestly).
- **Crisis:** **Exclude 2008–2009** appendix — Eq. 2 coord interaction **~0.01218**, wild **p ~0.104** (`robust_excl0809_eq2_coord_key_terms.csv`); one sentence in §6.2.4 pointing to appendix table.
- **Docs:** `README.md` § Thesis vs appendix specification defaults; `results/RESULTS_BRIEF.md`; `results/interpretation_memo.md` §6.2.4; `results/secondary/robustness_overview_20260515.md` closing bullets.
