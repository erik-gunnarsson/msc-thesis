# MSc Thesis: Industrial Robots, Labour Demand, and Collective Bargaining Institutions

## Research question

> *Do labour market institutions change how automation affects unemployment in industries that are highly exposed to robots?*

More precisely, the thesis tests whether cross-country differences in collective bargaining institutions **moderate** the relationship between **robot adoption** and **labour demand**, and whether this moderation differs across **industry buckets within manufacturing**. An extension examines whether the same moderation differs between **exposed** (tradeable) and **sheltered** industries.

---

## Motivation and research gap

Evidence on robots and labour-market outcomes is mixed across contexts. A key gap is a **industry-granular** analysis that treats collective bargaining institutions as **mechanisms that condition adjustment**.

A practical constraint is **statistical power**: estimating fully industry-specific robot-by-institution effects across many industries is unstable in a European panel due to the limited number of countries. 

This project addresses that constraint by:
* grouping manufacturing industries into a small number of **industry buckets**.
* estimating **pooled interaction models** that enable coherent inference and formal comparisons across buckets.

---

## Data sources

### 1) Industrial robots (IFR)

* **Source:** International Federation of Robotics (IFR), accessed via replication materials.
* **Coverage:** country × industry × year.
* **Main exposure:** robot intensity (log), lagged one year: `ln_robots_lag1`.

### 2) Labour outcomes and industry controls (EU KLEMS)

* **Source:** EU KLEMS Growth and Productivity Accounts (2023 release).
* **Coverage:** country × NACE Rev.2 manufacturing industry × year.
* **Main outcome:** a labour input proxy from KLEMS growth accounts (for example labour services / labour input indices such as `LAB_QI`).

  * In code and outputs, treat this as **labour input (proxy)** rather than claiming it is raw hours.
* **Controls (industry-level):**

  * log value added
  * log capital inputs (ICT and non-ICT)
  * macro controls where used (GDP, unemployment)

### 3) Collective bargaining institutions (ICTWSS / OECD-AIAS)

* **Source:** ICTWSS database.
* **Pre-declared moderator set (three institutional channels):**

  1. **Union strength:** `ud` (Union Density) -- strongest measurement leverage: available for the most countries, continuous, high cross-country variation.
  2. **Bargaining coordination:** `coord` (Coordination index) -- continuous specification is the main model; binary (Coord >= 4) is robustness only.
  3. **Agreement coverage:** `adjcov` (Adjusted collective bargaining coverage) -- restricted-sample (available for fewer countries).

#### Triage Test

The triage script screens candidate ICTWSS moderators (descriptive leverage + screening regressions). Moderators are chosen on theory and measurement feasibility, not on p-values. The final variables used are:

| Variable | Label                    | Sample        | Specification                                      |
| -------- | ------------------------ | ------------- | -------------------------------------------------- |
| ud       | Union Density            | full, common  | Continuous; strongest leverage (most countries)   |
| coord    | Coordination             | full, common  | Continuous (main); binary (Coord ≥ 4) robustness   |
| adjcov   | Adjusted Coverage        | restricted    | Fewer countries; common-sample models only        |

#### Predetermined institutions (baseline freeze)

Institutions are treated as structural country characteristics by measuring them using a **pre-period baseline** (1990-1995 averages, stored as `*_pre` raw and `*_pre_c` centered), to mitigate simultaneity concerns.

#### Feasibility diagnostics (not a selection rule)

A dedicated triage script summarizes moderator data quality (coverage, distinct values, dispersion, missingness) and provides screening regressions for transparency. Moderators are chosen on theory and measurement feasibility, not on p-values.

### 4) Macro controls (Eurostat)

* Real GDP and unemployment rate (where used).
* Missingness is documented; coverage-based models may imply a restricted country sample.

### 5) Market exposure (extension only: WIOD / TiVA)

* **Source:** World Input-Output Database (WIOD) or OECD TiVA, for the exposed/sheltered extension.
* **Variables:** Export intensity (exports / gross output) by country × industry, averaged over a pre-period baseline (e.g., 1995–2000).
* **Exposed_j:** Binary classification derived from baseline export intensity (e.g., above median = exposed).

---

## Sample construction (high level)

* Unit of analysis: **country × industry × year**
* Period: **1995–2019** (baseline, as supported by merged sources)
* Manufacturing only: **NACE Rev.2 Section C (C10–C33)**
* Panel is typically **unbalanced** due to harmonization constraints across IFR, KLEMS, and ICTWSS.

### Panel breakdown

| Dimension       | Definition                                      | Full sample   | Common sample (adjcov) |
| --------------- | ----------------------------------------------- | ------------- | ---------------------- |
| Unit            | country × industry × year                       | —             | —                      |
| Entity          | country–industry cell                            | ~265–290      | ~200–250               |
| Countries       | EU member states (IFR + KLEMS + ICTWSS overlap)  | ~13           | ~9                     |
| Industries      | KLEMS `nace_r2_code` (merged via IFR crosswalk) | ~11 groups    | ~11 groups             |
| Year range      | After lag and `dropna` on core vars              | ~2003–2019    | ~2003–2019             |
| Observations    | entity-year cells                               | ~2 600–2 700  | ~1 900–2 000           |

**Merge logic:** IFR (robots) and KLEMS (outcome, controls) are inner-joined on country × industry × year via IFR→NACE crosswalk. GDP, unemployment, and ICTWSS baseline are left-joined. Rows with missing `ln_hours`, `ln_robots_lag1`, `ln_va`, or `ln_cap` are dropped. Exact counts depend on the merge and vary slightly across runs.

### Full vs common samples

Some moderators are available for fewer countries (notably `adjcov`). To avoid confusing sample-driven differences with substantive differences:

* models using `ud` and `coord` are run on both:

  * **full sample**, and
  * **common sample** restricted to countries with `adjcov` availability.
* `adjcov` models are explicitly labeled as **restricted-sample** results.

---

## Key measurement choices

### Lagged robots (t-1)

Robots are lagged to strengthen temporal ordering (adoption precedes adjustment).

### Fixed-denominator robot intensity

Robot intensity uses a fixed base-year employment denominator to avoid mechanical correlation from a changing denominator.

### Institutions as predetermined (baseline freeze)

Country-level institutions are measured as baseline constants (for example early-window averages or earliest available values) and used as moderators.

---

## Industry heterogeneity strategy: theory-driven manufacturing buckets (NACE Rev.2)

### Six theoretical buckets

The conceptual framework distinguishes six groups:

| Bucket | Label                            | NACE 2-digit codes                                      |
| -----: | -------------------------------- | ------------------------------------------------------- |
|      1 | High-tech                        | C21 Pharmaceuticals; C26 Computer, electronic & optical |
|      2 | Transport equipment              | C29 Motor vehicles; C30 Other transport                 |
|      3 | Electro-mechanical capital goods | C27 Electrical equipment; C28 Machinery n.e.c.          |
|      4 | Metals                           | C24 Basic metals; C25 Fabricated metals                 |
|      5 | Process and materials            | C19; C20; C22; C23                                      |
|      6 | Low-tech / traditional           | C10–C18; C31–C33                                        |

### Five operational buckets (data constraint)

The IFR–KLEMS merge contains combined NACE groups that cannot be split (notably `C20-C21` and `C26-C27`). This prevents separate identification of the theoretical High-tech bucket in the main panel.

Main analysis therefore uses **five operational buckets**:

| Bucket | Label                              | KLEMS `nace_r2_code`               |
| -----: | ---------------------------------- | ---------------------------------- |
|      1 | Transport equipment                | C29-C30                            |
|      2 | Electro-mechanical capital goods   | C26-C27, C28                       |
|      3 | Metals                             | C24-C25                            |
|      4 | Process and materials              | C19, C20-C21, C22-C23              |
|      5 | Low-tech / traditional (reference) | C10-C12, C13-C15, C16-C18, C31-C33 |

Bucket 5 is the omitted reference category. A forced six-bucket mapping is reported only as a sensitivity analysis and labeled as assumption-driven.

---

## Empirical strategy

All main models are estimated as two-way fixed effects panels with:

* **Entity effects:** country–industry fixed effects
* **Time effects:** year fixed effects
* **Inference:** clustered standard errors at the entity level (baseline), with robustness options documented.


### Notations used in Equations 1–4:

| Symbol | Definition |
|--------|------------|
| $i$ | Country index |
| $j$ | Industry index |
| $t$ | Year index |
| $b$ | Bucket index |
| $\ln(LI)_{ijt}$ | Log labour input proxy (country $i$, industry $j$, year $t$) |
| $\ln(Robots)_{ij,t-1}$ | Log robot intensity, lagged one period |
| $X_{ijt}$ | Industry-level controls (value added, capital, etc.) |
| $M_c$ | Institutional moderator (UD, COORD, or ADJCOV; baseline 1990–1995) |
| $\alpha_{ij}$ | Country–industry fixed effects |
| $\delta_t$ | Year fixed effects |
| $\varepsilon_{ijt}$ | Error term |
| $Bucket_b$ | Indicator for bucket $b$ (reference: Low-tech) |
| $\beta_1$ | Coefficient on robots (main effect) |
| $\beta_2$ | Coefficient on robot × moderator interaction (Eq 2) |
| $\beta_{2b}$ | Bucket-specific robot coefficients (Eq 3, 4) |
| $\beta_3$ | Coefficient on robot × moderator (Eq 4) |
| $\beta_{4b}$ | Bucket-specific robot × moderator coefficients (Eq 4) |
| $\gamma$ | Coefficient vector for controls |

---

### Equation 1: Baseline robot–labour association

$$
\ln(LI)_{ijt} = \beta_1 \ln(Robots)_{ij,t-1} + \gamma X_{ijt} + \alpha_{ij} + \delta_t + \varepsilon_{ijt}
$$

### Equation 2: Institutional moderation (three channels)

For each moderator $M_c$:

$$
\ln(LI)_{ijt} = \beta_1 \ln(Robots)_{ij,t-1} + \beta_2 \left[ \ln(Robots)_{ij,t-1} \times M_c \right] + \gamma X_{ijt} + \alpha_{ij} + \delta_t + \varepsilon_{ijt}
$$

**Notes:** `ud` and `coord` are run on both full and common samples. `coord` is continuous in the main specification; binary (Coord ≥ 4) is robustness only. `adjcov` models are restricted-sample only.

### Equation 3: Bucket heterogeneity (pooled interaction)

$$
\ln(LI)_{ijt} = \beta_1 \ln(Robots)_{ij,t-1} + \sum_{b \neq \text{ref}} \beta_{2b} \left[ \ln(Robots)_{ij,t-1} \times Bucket_b \right] + \gamma X_{ijt} + \alpha_{ij} + \delta_t + \varepsilon_{ijt}
$$

### Equation 4: Bucket × institution (core contribution)

For each moderator $M_c$:

$$
\begin{aligned}
\ln(LI)_{ijt}
&= \beta_1 \ln(Robots)_{ij,t-1} \\
&\quad + \sum_{b \neq \text{ref}} \beta_{2b} \left[ \ln(Robots)_{ij,t-1} \times Bucket_b \right] \\
&\quad + \beta_3 \left[ \ln(Robots)_{ij,t-1} \times M_c \right] \\
&\quad + \sum_{b \neq \text{ref}} \beta_{4b} \left[ \ln(Robots)_{ij,t-1} \times M_c \times Bucket_b \right] \\
&\quad + \gamma X_{ijt} + \alpha_{ij} + \delta_t + \varepsilon_{ijt}
\end{aligned}
$$

**Outputs:** bucket-specific marginal robot effects at moderator values; formal bucket-to-bucket Wald contrasts under a single variance–covariance matrix.

### Accounting for Multiple-Testing risk

To reduce multiple-testing risk, the main text emphasizes a small set of pre-specified contrasts (for example Metals vs Low-tech, Transport vs Low-tech). Full pairwise contrast matrices are saved as appendix outputs.

---

## Control variables: definition and justification

Control variables are included to isolate the robot–labour association from confounding factors that jointly determine labour demand and robot adoption. Each control is pre-specified on theoretical and measurement grounds.

| Control | Symbol (in equations) | Definition | Justification |
|---------|----------------------|------------|---------------|
| **Value added** | $\ln(VA)_{ijt}$ in $X_{ijt}$ | Log of real gross value added (industry $j$, country $i$, year $t$). Source: EU KLEMS. | Captures industry scale and output demand. Labour demand is derived from output; omitting value added would conflate demand-driven employment changes with automation effects. Standard in labour demand functions (e.g., Hamermesh, 1993). |
| **Capital inputs** | $\ln(Cap)_{ijt}$ in $X_{ijt}$ | Log of aggregate capital services (ICT + non-ICT) in industry $j$, country $i$, year $t$. Source: EU KLEMS. | Capital and robots are substitute/complement inputs. Labour demand depends on the capital stock; robot adoption often co-occurs with other capital deepening. Controlling for capital partials out non-robot capital accumulation and reduces omitted-variable bias (Brynjolfsson & McAfee, 2014; Acemoglu & Restrepo, 2020). |
| **Real GDP** | (macro, where used) | Log of real GDP at country level.q

 Source: Eurostat. | Macroeconomic activity affects labour demand across industries. Inclusion coqntrols for country-level business-cycle and growth effects that could correlate with robot adoption. |
| **Unemployment rate** | (macro, where used) | National unemployment rate. Source: Eurostat. | Captures slack in the labour market and may reflect aggregate demand conditions. Inclusion ensures robot coefficients are not confounded by country–year cyclical variation. |

**Why these controls?** The baseline specification (Equation 1) conditions on value added and capital to identify the robot–labour association holding industry structure constant. Macro controls are used in robustness or when pooling across countries with different business-cycle phases; their inclusion may restrict the sample due to missingness and is documented.

**Textbook anchor:** Bell, Bryman & Harley (Ch. 11, secondary data analysis) — control variables are selected to block plausible confounders on theoretical grounds, not by stepwise or data-driven selection.

---

## Extension: sheltered vs. exposed industries (market-exposure heterogeneity)

In addition to the bucket-based heterogeneity (Equations 3–4), the thesis explores whether the robot–labour association and its institutional moderation differ by **international market exposure** — distinguishing **exposed** (tradeable) from **sheltered** industries. This extension tests whether the hawk–dove mechanism (institutional moderation of automation’s labour impact) operates differently in industries facing international competition.

### Notation extensions

| Symbol | Definition |
|--------|------------|
| $\text{Exposed}_j$ | Binary indicator: = 1 if industry $j$ is classified as exposed (tradeable); = 0 if sheltered. Time-invariant, measured from a pre-period baseline (e.g., average export intensity 1995–2000 from WIOD/TiVA). |
| $\text{ExpInt}_{ij}$ | Continuous export intensity: exports / gross output for industry $j$ in country $i$, averaged over a pre-period baseline window. Varies at the country × industry level. |
| $M_c$ | Institutional moderator (ud, coord, or adjcov), baseline-frozen as in the main design. |

**Predetermined measurement of exposure:** The choice to baseline-freeze ExpInt (or fix the binary Exposed classification from a pre-period window) follows the same logic applied to institutions: it mitigates simultaneity between robot adoption and trade structure. If automation shifts an industry’s export profile, using contemporaneous export intensity would introduce endogeneity.

*Textbook anchor:* Bell, Bryman & Harley (Ch. 11, secondary data analysis; Ch. 7, measurement) — predetermined measurement of moderators avoids contamination by the treatment, a standard practice for variables hypothesized to condition rather than mediate the main relationship.

---

### A. Binary specification: exposed / sheltered

#### Equation 5a — Market-exposure heterogeneity (replaces Eq. 3 in this extension)

Direct analogue of Equation 3, substituting five-bucket indicators with a single binary:

$$
\ln(LI)_{ijt} = \beta_1 \ln(Robots)_{ij,t-1} + \beta_2 \left[ \ln(Robots)_{ij,t-1} \times \text{Exposed}_j \right] + \gamma X_{ijt} + \alpha_{ij} + \delta_t + \varepsilon_{ijt}
$$

**Interpretation:**
- $\beta_1$ = marginal association of robots with labour input in sheltered industries (omitted reference).
- $\beta_1 + \beta_2$ = marginal association in exposed industries.
- $\beta_2$ = the differential robot–labour association attributable to international market exposure.

Under the hawk–dove logic, $\beta_2 < 0$ would indicate that exposed-sector unions behave more dovishly (accepting wage restraint and redeployment for employment security), leading to smoother adjustment — but the sign prediction depends on the theorised interpretation (muting job loss vs. facilitating productivity-driven employment growth) and should be specified in the framework section.

#### Equation 5b — Exposed × institution (replaces Eq. 4 in this extension)

The core contribution — triple interaction:

$$
\begin{aligned}
\ln(LI)_{ijt}
&= \beta_1 \ln(Robots)_{ij,t-1} + \beta_2 \left[ \ln(Robots)_{ij,t-1} \times \text{Exposed}_j \right] \\
&\quad + \beta_3 \left[ \ln(Robots)_{ij,t-1} \times M_c \right] \\
&\quad + \beta_4 \left[ \ln(Robots)_{ij,t-1} \times M_c \times \text{Exposed}_j \right] \\
&\quad + \gamma X_{ijt} + \alpha_{ij} + \delta_t + \varepsilon_{ijt}
\end{aligned}
$$

**Interpretation (key payoff):** The marginal effect of robots on labour input is a function of both market exposure and institutional setting:

| | Sheltered (Exposed = 0) | Exposed (Exposed = 1) |
|---|------------------------|------------------------|
| At moderator value $M_c$ | $\beta_1 + \beta_3 M_c$ | $(\beta_1 + \beta_2) + (\beta_3 + \beta_4) M_c$ |

- $\beta_3$ = how institutions moderate the robot–labour link in sheltered industries.
- $\beta_3 + \beta_4$ = how institutions moderate the robot–labour link in exposed industries.
- $\beta_4$ = **differential institutional moderation** between exposed and sheltered sectors — headline test of whether the hawk–dove mechanism operates differently across market-exposure types.

Under the theoretical framework: in coordinated systems (high coord), exposed-sector unions are archetypical "doves" — they set pattern bargains, exercise wage restraint, and facilitate adjustment. One would expect $\beta_4 < 0$ if coordination more strongly mutes the negative robot–employment association in exposed than in sheltered sectors.

**Identification note:** $\text{Exposed}_j$ is time-invariant and industry-specific. Country–industry fixed effects ($\alpha_{ij}$) absorb the level of Exposed; what is identified is the interaction — how exposure conditions the robot–labour slope and the robot × institution slope.

*Textbook anchor:* Bell, Bryman & Harley (Ch. 11, Ch. 24 on interaction terms) — the three-way interaction tests whether the second-order moderation (robot × institution) itself varies by a third conditioning variable.

---

### B. Continuous specification: export intensity

#### Equation 6a — Continuous market exposure (replaces Eq. 3 in this extension)

$$
\ln(LI)_{ijt} = \beta_1 \ln(Robots)_{ij,t-1} + \beta_2 \left[ \ln(Robots)_{ij,t-1} \times \text{ExpInt}_{ij} \right] + \gamma X_{ijt} + \alpha_{ij} + \delta_t + \varepsilon_{ijt}
$$

**Interpretation:** Marginal effect of robots on labour input = $\beta_1 + \beta_2 \times \text{ExpInt}_{ij}$. A continuous gradient: as export intensity rises, the robot–labour association shifts by $\beta_2$ per unit of ExpInt. Evaluate and plot at meaningful values (e.g., 25th, 50th, 75th percentiles).

#### Equation 6b — Continuous exposure × institution (replaces Eq. 4 in this extension)

$$
\begin{aligned}
\ln(LI)_{ijt}
&= \beta_1 \ln(Robots)_{ij,t-1} + \beta_2 \left[ \ln(Robots)_{ij,t-1} \times \text{ExpInt}_{ij} \right] \\
&\quad + \beta_3 \left[ \ln(Robots)_{ij,t-1} \times M_c \right] \\
&\quad + \beta_4 \left[ \ln(Robots)_{ij,t-1} \times M_c \times \text{ExpInt}_{ij} \right] \\
&\quad + \gamma X_{ijt} + \alpha_{ij} + \delta_t + \varepsilon_{ijt}
\end{aligned}
$$

**Interpretation:** Marginal effect:
$$
\frac{\partial \ln(LI)}{\partial \ln(Robots)} = \beta_1 + \beta_2 \, \text{ExpInt}_{ij} + \beta_3 M_c + \beta_4 (M_c \times \text{ExpInt}_{ij})
$$

This is a response surface in two dimensions ($M_c$, $\text{ExpInt}_{ij}$). Present as:
- Marginal-effects plot: ExpInt on x-axis, separate lines for low vs. high $M_c$ (e.g., ±1 SD of coord), with confidence bands.
- Or heatmap/contour plot of the marginal robot effect across the (coord, ExpInt) space.

$\beta_4$ again tests whether institutional moderation of automation’s labour impact varies continuously with export intensity — more informative than the binary specification as it exploits full variation in trade exposure.

---

## Robustness and sensitivity (👷‍♂️ TODO)

* Full vs common sample comparisons for `ud` and `coord`.
* Coordination robustness: continuous vs binary coding.
* Time-varying institution measures as sensitivity (baseline uses predetermined measures).
* Per-bucket separate regressions as descriptive robustness (lower power).
* Forced six-bucket mapping sensitivity.
* Alternative control sets and inference options (for example alternative clustering / dependence-robust SEs).
* Optional bucket or industry trends where relevant.
* **Exposed/sheltered extension:** binary vs continuous (ExpInt) specifications; alternative exposure baselines (e.g., 1995–2000 vs 1990–1995); sensitivity to exposure classification threshold.

---

## Limitations (design-relevant)

* Observational panel design: estimates are conditional associations.
* Institutional moderators vary mainly at the country level; inference is constrained by the number of countries.
* Coverage-based models use a restricted country set.
* Theoretical six vs operational five buckets reflect secondary-data aggregation constraints.
* Exposed/sheltered extension: industry concordance between WIOD/TiVA and IFR–KLEMS may limit coverage; exposure is predetermined to mitigate endogeneity but reduces time variation.

---

# Coding Related 

## Streamlit (👷‍♂️ TODO)
info on how streamlit dashboard works 

## Repository structure

```
.
├── .github
│   └── workflows
│       └── ci.yml
├── code
│   ├── archive
│   │   ├── 2-cleaning-data.py
│   │   ├── 6-equation4-industry-heterogeneity-coordination.py
│   │   ├── 7-equation5-industry-heterogeneity-coverage.py
│   │   ├── 8-equation6-routinetaskintensity.py
│   │   └── README.md
│   ├── logs
│   ├── 1-datacheck.py
│   ├── 2-build_panel.py
│   ├── 3-equation1-baseline.py
│   ├── 4-equation2-institutional-moderation-coordination.py
│   ├── 5-equation3-institutional-moderation-coverage.py
│   ├── 6-equation4-bucket-heterogeneity-coordination.py
│   ├── 7-equation5-bucket-heterogeneity-coverage.py
│   ├── 8-ictwss-triage.py
│   ├── _equation_utils.py
│   └── runall.py
├── streamlit
│   ├── components
│   │   ├── __init__.py
│   │   ├── decisiontree.py
│   │   ├── utils.py
│   │   └── vectorspace.py
│   ├── pages
│   │   ├── 1-home.py
│   │   ├── 2-decision-tree.py
│   │   ├── 3-vector-space.py
│   │   └── 4-results.py
│   └── streamlit.py
├── .gitignore
├── README.md
├── mapv1.png
└── requirements.txt
```

---

## How to reproduce (outline)

Will update once finished
