# MSc Thesis — Industrial Robots, Employment, and Collective Bargaining   

## Research question
**How does collective bargaining shape the aggregate employment effects of industrial robots across European countries?**

More precisely, we study whether national collective bargaining institutions (e.g., **wage coordination** and **collective bargaining coverage**) **moderate** the relationship between **robot adoption** and **manufacturing labour demand**, and whether this moderation differs across **types of manufacturing industries**.

---

## Motivation and research gap
Empirical evidence on robots and employment is mixed across contexts. A core gap is a **Europe-focused, industry-granular** account that explicitly incorporates **collective bargaining institutions** as moderators, rather than treating them as background country controls.

The key methodological constraint is **statistical power**: estimating fully industry-specific robot × institution effects across many industries is unstable in a European panel with a limited number of countries. This project addresses that by using a **theory-driven industry grouping** into a small number of buckets, enabling defensible heterogeneity analysis without over-parameterizing the model.

---

## Data sources
### 1) Industrial robots (IFR)
- **Source:** International Federation of Robotics (IFR), accessed via a replication dataset (Bachmann et al. replication kit)
- **Coverage:** Country × industry × year
- **Core measure:** Operational stock of industrial robots (ISO 8373 definition)
- **Main variable:** `ln_robots_it-1` (log robot intensity, lagged 1 year)

### 2) Labour outcomes and industry controls (EU KLEMS)
- **Source:** EU KLEMS Growth and Productivity Accounts (2023 release)
- **Coverage:** Country × NACE Rev.2 manufacturing industry × year
- **Main outcome:** `ln_hours` (log of total hours worked, e.g., `LAB_QI`)
- **Controls (industry-level):**
  - log real value added
  - log ICT capital stock
  - log non-ICT capital stock
  - (other standard production controls as used in the empirical strategy)

### 3) Collective bargaining institutions (ICTWSS / OECD–AIAS)
- **Source:** ICTWSS database
- **Key constructs:**
  - `Coord`: Wage coordination index (ordinal scale)
  - `AdjCov`: Adjusted collective bargaining coverage (%)
- **Design choice:** Institutions are treated as **predetermined** (time-invariant) by freezing them at a **baseline window** (e.g., early 1990s average) to reduce simultaneity concerns.

### 4) Macro controls (Eurostat / national accounts)
- **Country-level controls:** e.g., real GDP, unemployment rate (where used)
- **Deflation:** nominal variables deflated to constant euros (harmonized price indices)

---

## Sample construction (high level)
- Unit of analysis: **country × industry × year**
- Period: **1995–2019** (baseline; can be extended if data support)
- Manufacturing only: **NACE Rev.2 Section C (C10–C33)**
- Panel is typically **unbalanced** due to missingness and harmonization constraints across sources.
- Coverage-based analyses may require a restricted country sample if baseline `AdjCov` is missing for some countries.

---

## Key measurement choices
### Lagged robots (t−1)
Robots are lagged to improve temporal ordering: adoption precedes labour adjustment.

### Fixed-denominator robot intensity
Robot intensity is constructed using a **fixed base-year employment denominator** (e.g., 1995) to avoid mechanical correlation from a changing employment denominator.

### Institutions as predetermined (baseline “freeze”)
Collective bargaining institutions are treated as structural country characteristics by freezing them at a pre-period baseline window to mitigate reverse causality concerns.

---

## Industry heterogeneity strategy: Six theory-driven manufacturing buckets (NACE Rev.2)
Instead of estimating separate robot–institution slopes for every 2-digit industry (which is underpowered), manufacturing industries are grouped into six ex-ante buckets grounded in standard technology-intensity classifications and aligned with common robot-use patterns in manufacturing.

**Bucket 1 — High-tech**
- C21 Pharmaceuticals
- C26 Computer, electronic & optical

**Bucket 2 — Transport equipment (robot-intensive)**
- C29 Motor vehicles, trailers & semi-trailers
- C30 Other transport equipment

**Bucket 3 — Electro-mechanical capital goods (robot-intensive)**
- C27 Electrical equipment
- C28 Machinery & equipment n.e.c.

**Bucket 4 — Metals**
- C24 Basic metals
- C25 Fabricated metal products (excl. machinery)

**Bucket 5 — Process & materials**
- C19 Coke & refined petroleum
- C20 Chemicals
- C22 Rubber & plastics
- C23 Other non-metallic mineral products

**Bucket 6 — Low-tech / traditional manufacturing**
- C10–C18 (food; textiles; wood; paper/printing; etc.)
- C31–C32 (furniture; other manufacturing)
- C33 (repair/installation) is treated as a documented edge case and assigned consistently (default: bundled with capital goods ecosystem; reported as a robustness variation if needed).

This grouping is used to estimate heterogeneity at a **manageable dimensionality (3–6 groups)** while preserving interpretability and reducing overfitting risk.

---

## Empirical strategy (conceptual)
We estimate two-way fixed effects panel models that relate industry labour outcomes to robot adoption, and test moderation by bargaining institutions.

### Baseline structure
- **Fixed effects:** country–industry FE + year FE
- **Standard errors:** clustered at the country–industry level (baseline choice)

### Moderation + heterogeneity via buckets
The central specification interacts:
- robots (lagged) × bargaining institution (coordination and/or coverage) × bucket indicators

This yields:
- an average robots–labour relationship (within country–industry over time)
- how that relationship differs in **high vs low coordination (or varying coverage)**
- how those moderation patterns differ across **industry buckets**

---

## Robustness and sensitivity (planned)
- Alternative institution coding (binary vs ordinal coordination; centered coverage; alternative baseline windows)
- Alternative bucket assignment for edge cases (e.g., C33)
- Alternative control sets (production controls; macro controls)
- Alternative clustering choices / small-country inference checks (documented as sensitivity)

---

## Limitations (design-relevant)
- Observational panel design: estimates are **conditional associations**, not experimental causal effects.
- Institutions vary mainly at the country level; moderation inference is constrained by the number of countries.
- Industry granularity is intentionally reduced via buckets to maintain statistical stability.

---

## Repository structure (suggested)
- `data_raw/` — raw input extracts (IFR, EU KLEMS, ICTWSS, Eurostat)
- `data_processed/` — merged panel datasets and intermediates
- `src/`
  - `01_build_panel.*` — merges and harmonizes datasets
  - `02_construct_measures.*` — robot intensity, baseline institutions, deflation, buckets
  - `03_models.*` — fixed-effects regressions and outputs
  - `04_figures_tables.*` — summary tables and plots
- `output/` — regression tables, figures
- `docs/` — thesis write-up materials

---

## How to reproduce (outline)
1. Place raw data in `data_raw/` and set paths in config.
2. Run `01_build_panel` to merge IFR + EU KLEMS + ICTWSS (+ macro controls).
3. Run `02_construct_measures` to:
   - compute fixed-denominator robot intensity
   - apply baseline institution freeze
   - assign 2-digit industries into six buckets
4. Run `03_models` to estimate FE specifications.
5. Run `04_figures_tables` to export tables/figures.
