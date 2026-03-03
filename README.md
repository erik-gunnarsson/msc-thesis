# MSc Thesis: Industrial Robots, Labour Demand, and Collective Bargaining Institutions

## Research question

> *Does union density change how automation affects unemployment in industries that are highly exposed to robots?*

More precisely, the thesis tests whether cross-country differences in collective bargaining institutions **moderate** the relationship between **robot adoption** and **labour demand**, and whether this moderation differs across **industry buckets within manufacturing**.

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

---

## Sample construction (high level)

* Unit of analysis: **country × industry × year**
* Period: **1995–2019** (baseline, as supported by merged sources)
* Manufacturing only: **NACE Rev.2 Section C (C10–C33)**
* Panel is typically **unbalanced** due to harmonization constraints across IFR, KLEMS, and ICTWSS.

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

## Robustness and sensitivity (👷‍♂️ TODO)

* Full vs common sample comparisons for `ud` and `coord`.
* Coordination robustness: continuous vs binary coding.
* Time-varying institution measures as sensitivity (baseline uses predetermined measures).
* Per-bucket separate regressions as descriptive robustness (lower power).
* Forced six-bucket mapping sensitivity.
* Alternative control sets and inference options (for example alternative clustering / dependence-robust SEs).
* Optional bucket or industry trends where relevant.

---

## Limitations (design-relevant)

* Observational panel design: estimates are conditional associations.
* Institutional moderators vary mainly at the country level; inference is constrained by the number of countries.
* Coverage-based models use a restricted country set.
* Theoretical six vs operational five buckets reflect secondary-data aggregation constraints.

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
