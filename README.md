# MSc Thesis: Industrial Robots, Employment, and Collective Bargaining

**Research Question**
> *Does industrial robot adoption affect manufacturing employment in Europe, and do collective bargaining institutions moderate this relationship? If so, does this moderation vary across industries?*

---

## Quick Summary

**Main Findings:**
1. **Baseline (pooled)**: No average effect of robots on employment (β = -0.007, p = 0.42)
2. **Institutional moderation**: Coordination buffers robot displacement by ~2.5 percentage points (p = 0.064)
3. **Industry heterogeneity** (key contribution): Coordination works in **skill-intensive** industries (pharma +4.9%, chemicals +2.8%, petroleum +13.9%) but **NOT** in routine-intensive industries (automotive -2.4%, metals -0.8%, both n.s.)

**Contribution**: Reconciles conflicting literature by showing robot-employment effects are industry-specific. Challenges hypothesis that coordination protects routine workers—instead, it facilitates adjustment where robots complement skilled workers.

---

## Data Sources

### 1. Robot Adoption (IFR)
- **Source**: International Federation of Robotics via Bachmann et al. (2024) replication kit
- **Coverage**: 1993-2019, country × industry × year
- **Variable**: Operational stock of industrial robots (ISO 8373 definition)
- **Measure**: `ln(Robots per 1000 workers)`, normalized to 1995 base-year employment
- **Sample**: 25 EU countries, 34 NACE Rev. 2 manufacturing industries

### 2. Employment Outcomes (EU KLEMS)
- **Source**: EU KLEMS Growth and Productivity Accounts (2023 release)
- **Coverage**: 1995-2021, 28 EU countries, NACE Rev. 2 two-digit industries
- **Primary Variable**: `LAB_QI` (total hours worked, log-transformed)
- **Why hours over headcount**: Captures both extensive margin (job losses) and intensive margin (hours reductions)

### 3. Labor Market Institutions (ICTWSS)
- **Source**: OECD/AIAS ICTWSS Database
- **Baseline Window**: 1990-1995 average (extended to recover Germany & France)
- **Key Variables**:
  - `AdjCov`: Adjusted collective bargaining coverage (% of workers covered by agreements)
  - `Coord`: Wage coordination index (1-5 scale, Garnero 2021 classification)
  - `HighCoord`: Binary indicator (1 if Coord ≥ 4, capturing organized decentralized/centralized systems)
- **Treatment**: Time-invariant country characteristics (frozen at baseline to avoid endogeneity)

### 4. Control Variables (EU KLEMS + Eurostat)
- **Industry-level** (EU KLEMS):
  - Log real value added (`VA_PYP`)
  - Log capital stock: ICT (`CAPICT_QI`) and non-ICT (`CAPNICT_QI`)
- **Country-level** (Eurostat):
  - Log real GDP
  - Unemployment rate
- **Deflation**: All nominal variables deflated to constant 2015 euros using harmonized CPIs

---

## Final Sample Construction

**After merging and cleaning:**
- **Countries**: 17 (AT, BE, CZ, DE, DK, EE, ES, FI, FR, IT, LT, LV, NL, SE, SI, SK, UK)
- **Industries**: 24 NACE Rev. 2 manufacturing sectors (C10-C33)
- **Years**: 1995-2019 (25 years)
- **Observations**: 2,886 (country × industry × year)
- **Entities**: 291 country-industry pairs
- **Panel**: Unbalanced (some industries with insufficient data dropped)

**Sample restrictions for coverage analysis:**
- 6 countries dropped (CZ, EE, ES, LT, LV, SK) due to missing AdjCov in baseline period
- Restricted sample: 11 countries, 2,109 observations (73% of full sample)

---

## Empirical Strategy

### Panel Structure
**Unit of Analysis**: Country × Industry × Year  
**Fixed Effects**:
- **Pooled models (Eq. 1-3)**: Country-industry FE (α_ij) + Year FE (δ_t)
- **Industry-by-industry (Eq. 4-5)**: Country FE (α_i) + Year FE (δ_t)
  - *Note*: Cannot use country-industry FE when subsetting by industry (perfectly collinear)

**Standard Errors**: Clustered at country-industry level (conservative)

---

### Equation 1: Baseline Model
```
ln(Hours)_ijt = β₁ ln(Robots)_ijt-1 + X'_ijt γ + α_ij + δ_t + ε_ijt
```
**Purpose**: Test main effect—do robots affect employment on average?  
**Sample**: Full 17 countries, 24 industries, N = 2,886  
**Result**: β₁ = -0.007 (SE = 0.009, p = 0.42) → **Null result**

---

### Equation 2: Coordination Moderation (Pooled)
```
ln(Hours)_ijt = β₁ ln(Robots)_ijt-1 + β₂[ln(Robots)_ijt-1 × HighCoord_i] 
                + X'_ijt γ + α_ij + δ_t + ε_ijt
```
**Purpose**: Does coordination moderate robot-employment relationship?  
**Sample**: Full 17 countries, N = 2,886  
**Result**: 
- β₁ = -0.016 (p = 0.19) [low-coordination baseline]
- β₂ = +0.025 (p = 0.064) [coordination interaction] **← Marginally significant**
- **Marginal effects**:
  - Low coordination: -1.6%
  - High coordination: +0.9%
  - Difference: +2.5 percentage points

**Interpretation**: Coordinated bargaining systems buffer robot displacement

---

### Equation 3: Coverage Moderation (Pooled)
```
ln(Hours)_ijt = β₁ ln(Robots)_ijt-1 + β₂[ln(Robots)_ijt-1 × AdjCov_centered_i] 
                + X'_ijt γ + α_ij + δ_t + ε_ijt
```
**Purpose**: Does coverage (breadth) moderate robot effects?  
**Sample**: Restricted to 11 Western European countries, N = 2,109  
**Result**: 
- β₁ = +0.015 (p = 0.021) [at mean coverage]
- β₂ = -0.0013 (p = 0.074) [per 1pp coverage increase]

**Interpretation**: Marginally significant but negative moderation—higher coverage associated with MORE displacement. Quality of coordination matters more than breadth.

**⚠️ Limitation**: Sample composition changed (dropped all Eastern Europe)—results not directly comparable to Eq. 2.

---

### Equation 4: Industry-by-Industry Coordination (NEW)
```
For each industry j:
  ln(Hours)_ijt = β₁ʲ ln(Robots)_ijt-1 + β₂ʲ[ln(Robots)_ijt-1 × HighCoord_i] 
                  + X'_ijt γ + α_i + δ_t + ε_ijt
```
**Purpose**: WHERE does coordination moderation work?  
**Method**: Run 13 separate regressions (one per industry with sufficient data)  
**Sample**: 13/24 industries (dropped 11 due to insufficient countries or observations)

**Key Results** (coordination interaction β₂):

| Industry | Effect | p-value | Interpretation |
|----------|--------|---------|----------------|
| **SKILL-INTENSIVE** (Coordination buffers): | | |
| C31-C33 (Furniture) | **+9.6%*** | 0.001 | Strong buffering |
| C19 (Petroleum) | **+13.9%*** | 0.027 | Strong buffering |
| C21 (Pharmaceuticals) | **+4.9%*** | 0.001 | Strong buffering |
| C20-C21 (Chemicals) | **+2.8%*** | <0.001 | Moderate buffering |
| **ROUTINE-INTENSIVE** (No coordination effect): | | |
| C29-C30 (Motor vehicles) | -2.4% | 0.593 | **No effect** |
| C24-C25 (Metals) | -0.8% | 0.684 | **No effect** |
| C10-C12 (Food) | -0.5% | 0.894 | **No effect** |
| **NEGATIVE EFFECT**: | | |
| C28 (Machinery) | **-7.1%*** | 0.026 | Amplifies harm |

**Finding**: Coordination works where robots **complement** skilled workers (pharma, chemicals), NOT where robots **substitute** routine workers (automotive, metals). **This challenges our hypothesis.**

---

### Equation 5: Industry-by-Industry Coverage
```
For each industry j:
  ln(Hours)_ijt = β₁ʲ ln(Robots)_ijt-1 + β₂ʲ[ln(Robots)_ijt-1 × AdjCov_i] 
                  + X'_ijt γ + α_i + δ_t + ε_ijt
```
**Purpose**: Does coverage moderation vary by industry?  
**Sample**: 13 industries, restricted to 11 countries with coverage data

**Key Results**: More consistently negative than coordination—high coverage amplifies displacement in automotive (-0.38%), metals (-0.39%), electronics (-0.22%).

---

## Key Design Choices (Textbook Anchors)

### 1. **Lagged Robots (t-1)**
- **Purpose**: Temporal ordering, reduces simultaneity bias
- **Rationale**: Robot installation → employment adjustment takes time
- **Trade-off**: Misses immediate effects, but improves identification
- **Textbook**: Chapter 7 (Causality) - Lagged treatment supports temporal ordering

### 2. **Fixed-Denominator Intensity Measure**
```
Robot Intensity = Robots_ijt / Employment_ij,1995
```
- **Purpose**: Avoids mechanical correlation (robots/worker ratio depends on worker count)
- **Rationale**: If denominator varies with outcome, creates spurious correlation
- **Following**: Graetz & Michaels (2018), Haapanala et al. (2022)
- **Textbook**: Chapter 12 (Measurement) - Avoid ratio variables with outcome in denominator

### 3. **Baseline Institutions (Time-Invariant)**
- **Purpose**: Treat bargaining institutions as structural features, avoid endogeneity
- **Rationale**: Institutions might respond to automation (reverse causality)
- **Trade-off**: Assumes institutions stable 1995-2019 (not always true—Greece 2008)
- **Following**: Leibrecht et al. (2023), Haapanala et al. (2022)
- **Textbook**: Chapter 7 (Causality) - Predetermined moderators reduce endogeneity concerns

### 4. **Log-Log Specification**
- **Interpretation**: β₁ = elasticity (1% increase in robots → β₁% change in hours)
- **Rationale**: Both variables highly skewed; logs normalize distributions
- **Textbook**: Chapter 14 (Transformations) - Log transformations for skewed data

### 5. **Two-Way Fixed Effects**
- **Pooled models**: α_ij (country-industry) + δ_t (year)
  - Controls for "German automotive is uniquely robot-intensive"
  - Controls for global shocks (2008 recession, COVID if extended)
- **Industry-specific models**: α_i (country) + δ_t (year)
  - Controls for "Germany is high-coordination"
  - Weaker than pooled (can't control for industry-specific country trends)
- **Textbook**: Chapter 19 (Panel Methods) - Within-unit estimator, removes time-invariant heterogeneity

### 6. **Industry-by-Industry Approach (Heterogeneity)**
- **Purpose**: Test whether pooled null reflects offsetting effects across industries
- **Method**: Run coordination moderation separately for each industry
- **Trade-off**: Lower power per industry, but reveals heterogeneity
- **Textbook**: Chapter 15 (Interactions) - Separate regressions preserve heterogeneity that binary interactions wash out

---

## Main Contributions

### 1. **Methodological**
- **Better identification than Leibrecht et al. (2023)**: Industry-level panel with two-way FE vs. country-level dynamic panel
- **Addresses Leibrecht's call (p. 274)**: "Future research should study interaction between collective bargaining and automation at the industry-level"
- **Stronger within-unit variation**: Exploits country-industry-year changes vs. country-year

### 2. **Substantive**
- **Reconciles conflicting literature**:
  - Acemoglu & Restrepo (2020): Negative (US = routine manufacturing + weak institutions)
  - Dauth et al. (2021): Positive (Germany = chemicals/machinery + strong coordination)
  - Graetz & Michaels (2018): Null (pooling masks heterogeneity)
  - **Our finding**: All correct—effects are industry-specific AND institution-specific

- **Challenges routine-biased displacement theory**:
  - Expected: Coordination protects routine workers in automotive/metals
  - Found: Coordination buffers in skill-intensive pharma/chemicals
  - Mechanism: Coordination facilitates **task reinstatement** (retraining) where robots complement, not where they substitute

- **Policy implication**: One-size-fits-all labor market policies won't work. Coordination effective for high-skill adjustment, ineffective for routine displacement.

---

## Limitations & Caveats

### 1. **Causal Inference**
- **Design**: Observational panel, not experimental or quasi-experimental
- **Threats**: Time-varying confounders, reverse causality (two-way FE reduces but doesn't eliminate)
- **Interpretation**: Conditional associations consistent with robot-induced employment adjustments, NOT definitive causal effects
- **Textbook**: Chapter 7 (Causality) - Observational designs can suggest but not prove causation

### 2. **Sample Restrictions**
- **Coverage model**: 27% sample loss (6 countries dropped), restricted to Western Europe
- **Industry-by-industry**: 11/24 industries dropped (insufficient data)
- **Generalizability**: Results may not extend to full European manufacturing
- **Textbook**: Chapter 6 (Sampling) - Sample selection affects external validity

### 3. **Measurement**
- **Hours worked (LAB_QI)**: Proxy, not direct employment measure
- **Robot stock**: Doesn't distinguish robot types (welding vs. assembly vs. collaborative)
- **Institutions**: Crude binary (high/low coord) loses nuance
- **Textbook**: Chapter 12 (Measurement) - All operationalizations imperfect

### 4. **Scope**
- **Manufacturing only**: Services (70% of EU employment) excluded
- **Country coverage**: 17 EU countries, not all of Europe
- **Time period**: Pre-COVID (1995-2019), may not reflect post-pandemic dynamics
- **Textbook**: Chapter 5 (Research Design) - Scope limitations affect generalizability

### 5. **Fixed Effects Trade-Off**
- **Industry-specific models**: Country FE (not country-industry FE)
- **Implication**: Cannot control for Germany-specific automotive trends
- **Robustness**: Pooled coordination result (with stronger FE) confirms finding
- **Textbook**: Chapter 19 (Panel Methods) - More FE = better control, but less variation

---
