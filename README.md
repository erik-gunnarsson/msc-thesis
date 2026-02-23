# MSc Thesis: Industrial Robots, Labour Demand, and Collective Bargaining Institutions

## Research question

> **How do collective bargaining institutions shape the labour-demand effects of industrial robots across European countries, and do these effects differ across types of manufacturing industries?**

More precisely, the thesis tests whether cross-country differences in collective bargaining institutions **moderate** the relationship between **robot adoption** and **manufacturing labour demand**, and whether this moderation differs across **theory-driven manufacturing buckets**.

---

## Motivation and research gap

Evidence on robots and labour-market outcomes is mixed across contexts. A key gap is a **Europe-focused, industry-granular** analysis that treats collective bargaining institutions as **mechanisms that condition adjustment**, not just background controls.

A practical constraint is **statistical power**: estimating fully industry-specific robot-by-institution effects across many industries is unstable in a European panel with a limited number of countries. This project addresses that constraint by:

* grouping manufacturing industries into a small number of **theory-driven buckets**, and
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

### Equation 1: Baseline robot-labour association

[
\ln(LI)*{ijt}=\beta_1 \ln(Robots)*{ij,t-1} + \gamma X_{ijt} + \alpha_{ij} + \delta_t + \varepsilon_{ijt}
]
(LI) denotes the labour input proxy.

### Equation 2: Institutional moderation (three channels)

For each moderator (M_c \in {UD_pre, COORD_pre, ADJCOV_pre}):
[
\ln(LI)*{ijt}=\beta_1 \ln(Robots)*{ij,t-1} + \beta_2 \left[\ln(Robots)*{ij,t-1}\times M_c\right] + \gamma X*{ijt} + \alpha_{ij} + \delta_t + \varepsilon_{ijt}
]

Notes:

* `ud` and `coord` are run on both full and common samples.
* `coord` is continuous in the main specification (`coord_pre_c`); the binary variant (`high_coord_pre`, Coord >= 4) is robustness only.
* `adjcov` results are explicitly labeled as restricted-sample (common sample only).

### Equation 3: Bucket heterogeneity (pooled interaction)

[
\ln(LI)*{ijt}=\beta_1 \ln(Robots)*{ij,t-1} + \sum_{b\neq ref}\beta_{2b}\left[\ln(Robots)*{ij,t-1}\times Bucket_b\right] + \gamma X*{ijt} + \alpha_{ij} + \delta_t + \varepsilon_{ijt}
]

### Equation 4: Bucket heterogeneity with institutional moderation (core contribution)

For each moderator (M_c):
[
\ln(LI)*{ijt}=
\beta_1 \ln(Robots)*{ij,t-1}
+\sum_{b\neq ref}\beta_{2b}\left[\ln(Robots)*{ij,t-1}\times Bucket_b\right]
+\beta_3\left[\ln(Robots)*{ij,t-1}\times M_c\right]
+\sum_{b\neq ref}\beta_{4b}\left[\ln(Robots)*{ij,t-1}\times M_c \times Bucket_b\right]
+\gamma X*{ijt}+\alpha_{ij}+\delta_t+\varepsilon_{ijt}
]

Outputs include:

* bucket-specific marginal robot effects at relevant moderator values, and
* formal bucket-to-bucket contrasts (Wald tests) under a single variance-covariance matrix.

### Planned contrasts

To reduce multiple-testing risk, the main text emphasizes a small set of pre-specified contrasts (for example Metals vs Low-tech, Transport vs Low-tech). Full pairwise contrast matrices are saved as appendix outputs.

---

## Robustness and sensitivity (planned)

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

## Repository structure

* `data/`
  Raw input extracts and merged panel (`cleaned_data.csv`)

* `code/`

  * `1-datacheck.py`
    Validates raw data files and coverage.
  * `2-build_panel.py`
    Merges IFR + KLEMS + ICTWSS + Eurostat; constructs robot intensity; builds baseline institution measures; assigns buckets; outputs `cleaned_data.csv`.
  * `3-equation1-baseline.py`
    Baseline FE regression.
  * `4-equation2-institutional-moderation-coordination.py`
    Institutional moderation models (generic runner: `--moderator ud|coord|adjcov`, `--sample full|common`). UD and Coord run on both samples; AdjCov on common only.
  * `5-equation3-institutional-moderation-coverage.py`
    Coverage moderation (defaults to `adjcov`, restricted/common sample). Outputs explicitly labeled as restricted-sample.
  * `6-equation4-bucket-heterogeneity-coordination.py`
    Pooled bucket x robots x moderator triple interactions with marginal effects and Wald contrasts (generic runner: `--moderator ud|coord|adjcov`).
  * `7-equation5-bucket-heterogeneity-coverage.py`
    Bucket heterogeneity with continuous moderator (defaults to `adjcov`, common sample).
  * `8-ictwss-triage.py`
    Moderator feasibility diagnostics and screening regressions for transparency (not a selection rule).
  * `_equation_utils.py`
    Shared constants (bucket definitions), panel helpers, diagnostics, contrast testing, sample filtering.
  * `runall.py`
    Runs the full pipeline sequentially.
  * `archive/`
    Superseded scripts retained for auditability.

* `outputs/`
  Regression tables, diagnostics, contrasts, and figures.

---

## How to reproduce (outline)

1. Place raw data in `data/` (IFR, KLEMS, ICTWSS, Eurostat).
2. Run the full pipeline:

   * `python code/runall.py`
3. Optional diagnostics:

   * `python code/8-ictwss-triage.py` to generate moderator leverage summaries and screening outputs.
4. Outputs are written to `outputs/` with filenames indicating moderator and sample (full vs common, where relevant).
