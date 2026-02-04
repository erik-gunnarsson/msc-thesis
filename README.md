# Msc Thesis 

**Latest Research Question**
> *Does robot adoption reduce employment in manufacturing industries, and to what extent do labor market institutions—specifically collective bargaining coverage and wage coordination—mediate this effect across countries and industries?*

## Layout
Initial Tesing Folders (Chronolgical order Asc):
- IFR x industry automation weights => we got an IFR data set 🚀
- uncomtradev1 => replacing IFR with EU Import data
- ICTWSSv1 => adding collective bargaining 
- europev1 => broader test on EU data
- swedenv1 => quick test on sweden

## Literature Map

![literature map](mapv1.png)

---

# Collective Bargaining Layer × Robot Adoption

## Methodology

### Data Sources

#### EU Data
* **Employment & Value Added**
  Eurostat Structural Business Statistics (SBS)
  [https://ec.europa.eu/eurostat/databrowser/view/sbs_na_ind_r2](https://ec.europa.eu/eurostat/databrowser/view/sbs_na_ind_r2)

* **Wage Proxy**
  Eurostat National Accounts (NAMA_10_A64)
  *Compensation of employees, manufacturing aggregate*
  [https://ec.europa.eu/eurostat/databrowser/view/nama_10_a64](https://ec.europa.eu/eurostat/databrowser/view/nama_10_a64)

#### Automation Data
* **IFR (Automation)**
  **IFR **
  *Operational Stock*
  [https://IFR.org](https://ifr.org)

#### 


#### Collective Bargaining Data
* **Labor Market Institutions**
  **ICTWSS Database (OECD)**
  [https://www.oecd.org/en/data/datasets/oecdaias-ictwss-database.html](https://www.oecd.org/en/data/datasets/oecdaias-ictwss-database.html)

  * **[AdjCov]** Adjusted Bargaining Coverage (lagged t−1)
  * **[Coord]** Wage Coordination Index (lagged t−1)

### Alterative Data (no longer used)
* **Robot Adoption (Automation Proxy)**
  **UN Comtrade**
  *Imports of industrial robots (HS 847950)*
  [https://comtradeplus.un.org](https://comtradeplus.un.org)

* **Industry Automation Weights**  
  **OECD – Task Content of Jobs (Routine & Physical Task Measures)**  
  https://www.oecd.org/employment/skills-and-work/task-content-of-jobs/  



---

### Panel Unit

**Country × Industry (NACE Rev. 2, 2-digit) × Year**

---

### Outcome Variable (Anchor)

Following Piva–Vivarelli–style specifications:

* **Employment** in country *c*, industry *i*, year *t*

  * Log of persons employed (or hours worked, robustness)

---

### Automation Proxy (No IFR Data)

#### Country-level robot imports

* Annual **imports of industrial robots** (HS 847950) from UN Comtrade
* Measured in **trade value (USD)**
* Aggregated at **country × year**

#### Industry allocation (shift-share logic)

Robot imports are allocated to industries using **fixed industry automation weights**, yielding:

[
RobotExposure_{c i t}
=====================

\frac{RobotImports_{c t} \times Weight_i}{Employment_{c i t}}
]

Where:

* `Weight_i` captures the **baseline automation/robot suitability** of industry *i*
  (e.g. task replaceability, routine intensity, or pre-period robot intensity)
* Employment scaling yields an **intensity measure**, comparable across industries and countries

This approach mirrors the exposure logic used in the robot adoption literature when direct industry-level robot data are unavailable.

---

### Institutions (Moderators)

From ICTWSS, both **lagged one period**:

* **[AdjCov]** Adjusted Bargaining Coverage
* **[Coord]** Wage Coordination Index

Measured at **country × year** and merged onto the panel.

---

### Controls

* **Value Added** (log), country × industry × year

  * Captures demand/output effects
* **Wage Proxy** (log), country × year

  * Compensation of employees in manufacturing
  * Included explicitly to address the critique that bargaining institutions merely proxy wage levels

---

## Dynamic Panel Specification

[
\begin{aligned}
\ln Emp_{c i t}
&= \alpha \ln Emp_{c i, t-1}

* \beta_1 RobotExp_{c i t}
* \beta_2 AdjCov_{c, t-1}
* \beta_3 Coord_{c, t-1} \
  &\quad + \beta_4 (RobotExp_{c i t} \times AdjCov_{c, t-1})
* \beta_5 (RobotExp_{c i t} \times Coord_{c, t-1}) \
  &\quad + \gamma_1 \ln VA_{c i t}
* \gamma_2 \ln Wage_{c t}
* \alpha_{c i}
* \delta_t
* \varepsilon_{c i t}
  \end{aligned}
  ]

---

### Estimation Method

* **LSDVC (Least Squares Dummy Variable Corrected)**

  * Suitable for **small-T, moderate-N** panels
  * Corrects Nickell bias in the lagged dependent variable
  * Bias approximation:
    [
    \text{Bias} \approx -\frac{1 + \alpha}{T - 1}
    ]
* **Fixed effects**

  * Entity: country × industry
  * Time: year
* **Standard errors**

  * Clustered at the country–industry level
* Unbalanced panels allowed

---

### Variable Treatment

* All continuous regressors **mean-centered**
* Institutional variables **lagged one period**
* Interaction terms constructed from centered components

---

## What the Model Tests

1. **Employment persistence** via lagged employment.
2. **Baseline employment effect of robot adoption** at the industry level.
3. **Direct association** between labor market institutions and employment.
4. **Institutional moderation** of robot impacts:

   * Does higher bargaining coverage attenuate displacement?
   * Does wage coordination alter adjustment margins?
5. Robustness of effects after controlling for:

   * Output demand (value added)
   * Wage levels (explicitly)

---

## Sample and Implementation

**Current implementation (mainv3.py):**

* Countries: EU-15 (subject to data availability)
* Industries: Manufacturing (NACE Rev. 2, C10–C33)
* Years: **≈2011–2019** (intersection of all sources)
* Panel: Country × Industry × Year (unbalanced)

**Notes:**

* Sample size contracts after lag construction
* LSDVC is appropriate under these constraints
* The setup is modular and extendable backward once Comtrade coverage is expanded

