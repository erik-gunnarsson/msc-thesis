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

### ICT as digtization proxy (no IFR)

* **EU KLEMS:** ICT capital services share / ICT investment share (industry × country × year)

### Welfare/institutions (moderator)

* **ICTWSS:** Two institutional measures (both lagged t-1), country × year
  - **[AdjCov]** Adjusted Bargaining Coverage (lagged t-1)
  - **[Coord]** Wage Coordination Index (lagged t-1)

### Controls (basic)

* **Value added** (log) — demand / output
* **Wages** — compensation of employees in manufacturing (log), country × year
  - Source: Eurostat NAMA_10_A64 (compensation of employees, manufacturing aggregate)
  - Used as a proxy to address "coverage is just wages" critique

### Dynamic panel model (implemented in mainv2.py)

This is a dynamic panel model with lagged dependent variable and bias correction:

[
\ln Emp_{c i t} = \alpha \ln Emp_{c i, t-1} + \beta_1 ICT_{c i t} + \beta_2 AdjCov_{c, t-1} + \beta_3 Coord_{c, t-1} + \beta_4 (ICT_{c i t} \times AdjCov_{c, t-1}) + \beta_5 (ICT_{c i t} \times Coord_{c, t-1}) + \gamma_1 \ln VA_{c i t} + \gamma_2 \ln Wage_{c t} + \alpha_{ci} + \delta_t + \epsilon_{c i t}
]

**Estimation method:**
* **LSDVC** (Least Squares Dummy Variable Corrected) — appropriate for small panels
* Corrects bias in LSDV estimator for dynamic panel models (Kiviet 1995, Bruno 2005)
* Bias correction applied to lagged dependent variable coefficient: bias ≈ -(1+α)/(T-1)
* Entity fixed effects (α_{ci}): country-industry
* Time fixed effects (δ_t): year
* Standard errors clustered at entity level (country-industry)

**Variables:**
* **lnEmp_{t-1}**: Lagged log employment (dynamics)
* **ICT**: ICT capital share (from KLEMS, mean-centered)
* **AdjCov_{t-1}**: Adjusted Bargaining Coverage, lagged one period (mean-centered)
* **Coord_{t-1}**: Wage Coordination Index, lagged one period (mean-centered)
* **ICT × AdjCov**: Interaction term (mean-centered variables)
* **ICT × Coord**: Interaction term (mean-centered variables)
* **lnVA**: Log value added (control)
* **lnWage**: Log wage proxy (control)

**What the model checks:**

1. The panel merges cleanly (keys align across all datasets).
2. Missingness is manageable after creating lagged variables.
3. Coefficients are plausible (signs; not crazy).
4. Both interaction terms are estimable (institutions vary over time).
5. Dynamic effects: persistence in employment (α coefficient on lagged employment).
6. Institutional moderation: how ICT effects vary with bargaining coverage and coordination.

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

* **[AdjCov]** Adjusted Bargaining Coverage — preferred measure, lagged t-1
* **[Coord]** Wage Coordination Index — secondary measure, lagged t-1

Target: **country + year** (both measures lagged one period before inclusion in model).

---

## 3) Sample and implementation


**Current implementation (mainv2.py):**
* Countries: Multiple European countries (varies by data availability)
* Industries: Manufacturing industries (NACE Rev.2 C10–C33)
* Years: **2011–2019** (based on data availability across all sources)
* Panel structure: Country × Industry × Year

**Note on sample size:**
* After merging and creating lagged variables, sample size is reduced
* LSDVC is appropriate for small T (time periods) panels
* Current implementation handles unbalanced panels



