# Collective bargaining layer 

## Update Logs 
### ======================== Jan 27th updated => mainv2.py ========================

- Add dynamics: include lagged employment and move to system GMM or LSDVC ==> decide don LSDVC as the pannel was small and system GMM buggy on python
- Add a wage proxy (even if imperfect) to avoid “coverage is just wages” critique. 
  - added at data/eurostat_wageproxy
- Use lagged ICTWSS and pre-specify 1–2 core institutional measures ===> Keep this simple! MAX 2
  - [AdjCov] Adjusted Bargaining Coverage (lagged t-1)
  - [coord] Wage Coordination Index (lagged t-1)

### ======================== Jan 26th ideas ========================

testing a country–industry–year panel where an automation proxy (ICT capital / ICT usage) affects employment, and where that effect is moderated by institutions (ICTWSS)?”

## Methodology

### data

- employment: Eurostat => https://ec.europa.eu/eurostat/databrowser/view/sbs_na_ind_r2__custom_19815875/default/table 
- wage proxy: Eurostat => https://ec.europa.eu/eurostat/databrowser/view/nama_10_a64/default/table?lang=en
- ICT: KLEMS => https://euklems-intanprod-llee.luiss.it/
- Collective Bargaining: ICTWSS => https://www.oecd.org/en/data/datasets/oecdaias-ictwss-database.html
  - [AdjCov] Adjusted Bargaining Coverage (lagged t-1)
  - [coord] Wage Coordination Index (lagged t-1)


### Panel unit

**Country × Industry (NACE 2-digit) × Year**

### Anchor outcome (like Piva–Vivarelli)

* **Employment** in industry (i), country (c), year (t)
  (log of persons employed or hours worked)

### Automation proxy (no IFR)

Pick **one** for the mini test:

* **EU KLEMS:** ICT capital services share / ICT investment share (industry × country × year)
  or
* **Eurostat ICT usage in enterprises:** adoption of ERP/cloud/big data (usually country × year, sometimes by size/sector; use what’s available)

### Welfare/institutions (moderator)

* **ICTWSS:** bargaining coverage (or union density), country × year

### Controls (basic)

* **Value added** (log) — demand / output
* **Wages** or compensation per employee (log) — labor cost
  (If wage at industry level is hard to get quickly, omit for mini test; the goal is feasibility.)

### Simple model (feasible and interpretable)

This is a reduced-form version of the Piva–Vivarelli logic:

[
\ln Emp_{c i t} = \beta_1 , Auto_{c i t} + \beta_2 , Inst_{c t} + \beta_3 , (Auto_{c i t}\times Inst_{c t}) + \gamma \ln VA_{c i t} + \alpha_{ci} + \delta_t + \epsilon_{c i t}
]

* ( \alpha_{ci} ): country-industry fixed effects
* ( \delta_t ): year fixed effects
* cluster SE at **country-industry** (or country)

**What you’re checking in the mini test**

1. The panel merges cleanly (keys align).
2. Missingness is manageable.
3. Coefficients are plausible (signs; not crazy).
4. The interaction term is estimable (institutions vary over time).

---

## 2) Minimal dataset recipe (fastest path)

### A. Employment + value added (Eurostat SBS)

From Eurostat database:

* Industry employment (persons employed)
* Value added (or turnover if VA is messy)

Target: **NACE Rev. 2**, 2-digit industries, annual.

### B. Automation proxy (EU KLEMS)

From EU KLEMS download:

* ICT capital services / ICT capital share / ICT investment share (depends on release table names)

Target: same **industry codes + countries + years**.

### C. Institutions (ICTWSS)

From ICTWSS:

* **Bargaining coverage** (preferred)
  or **Union density**

Target: **country + year**.

---

## 3) Mini-sample suggestion (so it doesn’t explode)

Pick something like:

* Countries: **DE, FR, IT, NL, SE** (or any 3–5 that exist across all datasets)
* Industries: manufacturing + a few services
  e.g. C10–C33, plus G, H, J (whatever matches across SBS & KLEMS)
* Years: **2005–2012** (or any window with overlap)

Goal: end up with **~300–1200 observations**, not 10k.

---

## 4) Practical merge keys (this is where most mini tests fail)

You’ll standardize:

* `country` (ISO2 like DE, FR…)
* `year` (int)
* `industry` (NACE Rev.2 2-digit like C10, C11… OR numeric 10, 11…)

You’ll almost certainly need a small **crosswalk** between:

* EU KLEMS industry naming (often “C10T12” style aggregates)
  and
* Eurostat SBS codes.

For the mini test, avoid aggregates unless you’re confident both sides match.


