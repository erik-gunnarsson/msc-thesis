'''
# version 2
- switched to LSDVC (Least Squares Dummy Variable Corrected) for small panel
- added wage proxy
- added lagged employment (dynamics)
- added lagged institutional measures (AdjCov, Coord at t-1)


Regression Analysis: Employment vs ICT, Institutions, and Interaction
=======================================================================
Model: lnEmp_t = α·lnEmp_{t-1} + β₁·ICT + β₂·Institution_{t-1} + β₃·(ICT × Institution_{t-1}) + β₄·lnVA + β₅·lnWage + FE + ε

Data Sources:
- employment: Eurostat => https://ec.europa.eu/eurostat/databrowser/view/sbs_na_ind_r2__custom_19815875/default/table 
- wage proxy: Eurostat => https://ec.europa.eu/eurostat/databrowser/view/nama_10_a64/default/table?lang=en
- ICT: KLEMS => https://euklems-intanprod-llee.luiss.it/
- insitutions: ICTWSS => https://www.oecd.org/en/data/datasets/oecdaias-ictwss-database.html
'''

import pandas as pd
import numpy as np
from loguru import logger
from linearmodels.panel import PanelOLS

# --- Load ---

logger.info(f"===== Loading data ============================================\n\n\n")

# Load raw data
sbs_raw = pd.read_csv("data/eurostat_employment.csv")
klem_raw = pd.read_csv("data/klems_growth_accounts_basic.csv")        
ictwss_raw = pd.read_csv("data/ictwss_institutions.csv")
wage_raw = pd.read_csv("data/eurostat_wageproxy.csv")

logger.info(f"Loaded {len(sbs_raw)} observations from Eurostat")
logger.info(f"Eurostat headers: {sbs_raw.columns.tolist()}\n")   
logger.info(f"Loaded {len(ictwss_raw)} observations from ICTWSS")
logger.info(f"ICTWSS headers: {ictwss_raw.columns.tolist()}\n")
logger.info(f"Loaded {len(klem_raw)} observations from KLEMS")
logger.info(f"KLEMS headers: {klem_raw.columns.tolist()}\n")
logger.info(f"Loaded {len(wage_raw)} observations from Eurostat wage proxy")
logger.info(f"Wage proxy headers: {wage_raw.columns.tolist()}\n")

logger.info(f"===== Data loaded complete =====\n\n\n")

#%%

# --- Process Eurostat (SBS) data ---
logger.info("\n\n\n===== Processing Eurostat data ============================================\n\n\n")

# Filter for employment and value added
sbs_emp = sbs_raw[sbs_raw['indic_sb'] == 'Persons employed - number'].copy()
sbs_va = sbs_raw[sbs_raw['indic_sb'] == 'Value added at factor cost - million euro'].copy()

# Standardize country names to ISO2 codes (create mapping)
# Map common country names to ISO2 codes
country_mapping = {
    'Austria': 'AT', 'Belgium': 'BE', 'Bulgaria': 'BG', 'Croatia': 'HR',
    'Cyprus': 'CY', 'Czech Republic': 'CZ', 'Czechia': 'CZ', 'Denmark': 'DK',
    'Estonia': 'EE', 'Finland': 'FI', 'France': 'FR', 'Germany': 'DE',
    'Greece': 'GR', 'Hungary': 'HU', 'Ireland': 'IE', 'Italy': 'IT',
    'Latvia': 'LV', 'Lithuania': 'LT', 'Luxembourg': 'LU', 'Malta': 'MT',
    'Netherlands': 'NL', 'Poland': 'PL', 'Portugal': 'PT', 'Romania': 'RO',
    'Slovakia': 'SK', 'Slovenia': 'SI', 'Spain': 'ES', 'Sweden': 'SE',
    'United Kingdom': 'GB', 'UK': 'GB', 'Albania': 'AL', 'Iceland': 'IS',
    'Norway': 'NO', 'Switzerland': 'CH', 'Turkey': 'TR', 'Bosnia and Herzegovina': 'BA'
}

# Map Eurostat industry names to NACE Rev.2 codes
industry_mapping = {
    'Manufacture of food products': 'C10',
    'Manufacture of beverages': 'C11',
    'Manufacture of tobacco products': 'C12',
    'Manufacture of textiles': 'C13',
    'Manufacture of wearing apparel': 'C14',
    'Manufacture of leather and related products': 'C15',
    'Manufacture of wood and of products of wood and cork, except furniture; manufacture of articles of straw and plaiting materials': 'C16',
    'Manufacture of paper and paper products': 'C17',
    'Printing and reproduction of recorded media': 'C18',
    'Manufacture of coke and refined petroleum products': 'C19',
    'Manufacture of chemicals and chemical products': 'C20',
    'Manufacture of basic pharmaceutical products and pharmaceutical preparations': 'C21',
    'Manufacture of rubber and plastic products': 'C22',
    'Manufacture of other non-metallic mineral products': 'C23',
    'Manufacture of basic metals': 'C24',
    'Manufacture of fabricated metal products, except machinery and equipment': 'C25',
    'Manufacture of computer, electronic and optical products': 'C26',
    'Manufacture of electrical equipment': 'C27',
    'Manufacture of machinery and equipment n.e.c.': 'C28',
    'Manufacture of motor vehicles, trailers and semi-trailers': 'C29',
    'Manufacture of other transport equipment': 'C30',
    'Manufacture of furniture': 'C31',
    'Other manufacturing': 'C32',
    'Repair and installation of machinery and equipment': 'C33'
}

# Process employment data
sbs_emp['country'] = sbs_emp['geo'].map(country_mapping)
sbs_emp['industry'] = sbs_emp['nace_r2'].str.strip().map(industry_mapping)
sbs_emp['year'] = pd.to_numeric(sbs_emp['TIME_PERIOD'], errors='coerce')
sbs_emp['emp'] = pd.to_numeric(sbs_emp['OBS_VALUE'], errors='coerce')

sbs_emp = sbs_emp[['country', 'industry', 'year', 'emp']].dropna(subset=['country', 'industry', 'year', 'emp'])
sbs_emp = sbs_emp.groupby(['country', 'industry', 'year'])['emp'].sum().reset_index()

logger.info(f"Eurostat employment: {len(sbs_emp)} observations after processing")

# Process value added data
sbs_va['country'] = sbs_va['geo'].map(country_mapping)
sbs_va['industry'] = sbs_va['nace_r2'].str.strip().map(industry_mapping)
sbs_va['year'] = pd.to_numeric(sbs_va['TIME_PERIOD'], errors='coerce')
sbs_va['va'] = pd.to_numeric(sbs_va['OBS_VALUE'], errors='coerce')

sbs_va = sbs_va[['country', 'industry', 'year', 'va']].dropna(subset=['country', 'industry', 'year', 'va'])
sbs_va = sbs_va.groupby(['country', 'industry', 'year'])['va'].sum().reset_index()

logger.info(f"Eurostat value added: {len(sbs_va)} observations after processing")

# Merge employment and value added
sbs = sbs_emp.merge(sbs_va, on=['country', 'industry', 'year'], how='outer')
sbs['country'] = sbs['country'].str.upper().str.strip()
sbs['industry'] = sbs['industry'].astype(str).str.strip()

logger.info(f"Eurostat merged: {len(sbs)} observations")

# --- Process wage proxy data ---
logger.info("\n\n\n===== Processing wage proxy data ============================================\n\n\n")

# Filter for compensation of employees in manufacturing
wage_data = wage_raw[
    (wage_raw['na_item'] == 'Compensation of employees') & 
    (wage_raw['nace_r2'] == 'Manufacturing')
].copy()

# Standardize country names
wage_data['country'] = wage_data['geo'].map(country_mapping)
wage_data['year'] = pd.to_numeric(wage_data['TIME_PERIOD'], errors='coerce')
wage_data['wage'] = pd.to_numeric(wage_data['OBS_VALUE'], errors='coerce')

# Clean and aggregate
wage_data = wage_data[['country', 'year', 'wage']].dropna(subset=['country', 'year', 'wage'])
wage_data = wage_data.groupby(['country', 'year'])['wage'].sum().reset_index()
wage_data['country'] = wage_data['country'].str.upper().str.strip()

logger.info(f"Wage proxy: {len(wage_data)} observations after processing")

# --- Process KLEMS data ---
logger.info("\n\n\n===== Processing KLEMS data ============================================\n\n\n")

# Filter for ICT capital and total capital
klem_ict = klem_raw[klem_raw['var'] == 'CAPICT_QI'].copy()
klem_total = klem_raw[klem_raw['var'] == 'CAP_QI'].copy()

# Standardize country codes (handle EL -> GR for Greece)
klem_ict['country'] = klem_ict['geo_code'].str.upper().str.strip().replace('EL', 'GR')
klem_total['country'] = klem_total['geo_code'].str.upper().str.strip().replace('EL', 'GR')

# Standardize industry codes
klem_ict['industry'] = klem_ict['nace_r2_code'].str.strip()
klem_total['industry'] = klem_total['nace_r2_code'].str.strip()

# Process year
klem_ict['year'] = pd.to_numeric(klem_ict['year'], errors='coerce')
klem_total['year'] = pd.to_numeric(klem_total['year'], errors='coerce')

# Get values
klem_ict['ict_cap'] = pd.to_numeric(klem_ict['value'], errors='coerce')
klem_total['total_cap'] = pd.to_numeric(klem_total['value'], errors='coerce')

# Clean and reshape
klem_ict = klem_ict[['country', 'industry', 'year', 'ict_cap']].dropna(subset=['country', 'industry', 'year', 'ict_cap'])
klem_total = klem_total[['country', 'industry', 'year', 'total_cap']].dropna(subset=['country', 'industry', 'year', 'total_cap'])

# Merge ICT and total capital
klem = klem_ict.merge(klem_total, on=['country', 'industry', 'year'], how='inner')

# Calculate ICT share
klem['ict_share'] = klem['ict_cap'] / klem['total_cap']
klem = klem[['country', 'industry', 'year', 'ict_share']].dropna(subset=['ict_share'])

logger.info(f"KLEMS: {len(klem)} observations after processing")

# --- Process ICTWSS data ---
logger.info("\n\n\n===== Processing ICTWSS data ============================================\n\n\n")

# Map country names to ISO2 codes
ictwss_raw['country_iso2'] = ictwss_raw['country'].map(country_mapping)

# Use ISO3 to ISO2 mapping if available, otherwise use direct mapping
# Create reverse mapping from ISO3 to ISO2
iso3_to_iso2 = {
    'ALB': 'AL', 'AUT': 'AT', 'BEL': 'BE', 'BGR': 'BG', 'HRV': 'HR',
    'CYP': 'CY', 'CZE': 'CZ', 'DNK': 'DK', 'EST': 'EE', 'FIN': 'FI',
    'FRA': 'FR', 'DEU': 'DE', 'GRC': 'GR', 'HUN': 'HU', 'IRL': 'IE',
    'ITA': 'IT', 'LVA': 'LV', 'LTU': 'LT', 'LUX': 'LU', 'MLT': 'MT',
    'NLD': 'NL', 'POL': 'PL', 'PRT': 'PT', 'ROU': 'RO', 'SVK': 'SK',
    'SVN': 'SI', 'ESP': 'ES', 'SWE': 'SE', 'GBR': 'GB', 'ISL': 'IS',
    'NOR': 'NO', 'CHE': 'CH', 'TUR': 'TR'
}

# Fill missing ISO2 from ISO3
ictwss_raw.loc[ictwss_raw['country_iso2'].isna(), 'country_iso2'] = \
    ictwss_raw.loc[ictwss_raw['country_iso2'].isna(), 'iso3'].map(iso3_to_iso2)

# Standardize country
ictwss_raw['country'] = ictwss_raw['country_iso2'].str.upper().str.strip()
ictwss_raw['year'] = pd.to_numeric(ictwss_raw['year'], errors='coerce')

# Extract institutional measures: AdjCov (Adjusted Bargaining Coverage) and Coord (Wage Coordination Index)
ictwss = ictwss_raw[['country', 'year', 'AdjCov', 'Coord']].copy()
ictwss['adjcov'] = pd.to_numeric(ictwss['AdjCov'], errors='coerce')
ictwss['coord'] = pd.to_numeric(ictwss['Coord'], errors='coerce')

# Keep only rows with at least one institutional measure
ictwss = ictwss.dropna(subset=['country', 'year'])
ictwss = ictwss[['country', 'year', 'adjcov', 'coord']]

logger.info(f"ICTWSS: {len(ictwss)} observations after processing")
logger.info(f"AdjCov non-null: {ictwss['adjcov'].notna().sum()}")
logger.info(f"Coord non-null: {ictwss['coord'].notna().sum()}")

logger.info(f"===== Data processing complete =====")

#%%

# --- Merge datasets ---
logger.info("\n\n\n===== Merging datasets ============================================\n\n\n")

# Merge SBS with KLEMS
df = sbs.merge(klem, on=['country', 'industry', 'year'], how='inner')
logger.info(f"After SBS-KLEMS merge: {len(df)} observations")

# Merge with wage proxy
df = df.merge(wage_data, on=['country', 'year'], how='inner')
logger.info(f"After wage proxy merge: {len(df)} observations")

# Merge with ICTWSS
df = df.merge(ictwss, on=['country', 'year'], how='inner')
logger.info(f"After ICTWSS merge: {len(df)} observations")

logger.info(f"Final dataset: {len(df)} observations")
logger.info(f"Countries: {df['country'].nunique()}")
logger.info(f"Industries: {df['industry'].nunique()}")
logger.info(f"Years: {df['year'].min():.0f} - {df['year'].max():.0f}")

# --- Final cleaning and variable creation ---
logger.info("\n\n\n===== Creating variables & running regression ============================================\n\n\n")

# Ensure numeric types
df["emp"] = pd.to_numeric(df["emp"], errors='coerce')
df["va"] = pd.to_numeric(df["va"], errors='coerce')
df["ict_share"] = pd.to_numeric(df["ict_share"], errors='coerce')
df["wage"] = pd.to_numeric(df["wage"], errors='coerce')
df["adjcov"] = pd.to_numeric(df["adjcov"], errors='coerce')
df["coord"] = pd.to_numeric(df["coord"], errors='coerce')

# Remove zeros and infinities (avoid log issues)
df = df[(df["emp"] > 0) & (df["va"] > 0) & (df["wage"] > 0)]
df = df.replace([np.inf, -np.inf], np.nan)

logger.info(f"After initial cleaning: {len(df)} observations")

# Create log variables
df["ln_emp"] = np.log(df["emp"])
df["ln_va"] = np.log(df["va"])
df["ln_wage"] = np.log(df["wage"])

# Sort by entity and year for lagging
df = df.sort_values(['country', 'industry', 'year'])

# Create lagged variables (t-1)
# Lagged employment
df["ln_emp_lag1"] = df.groupby(['country', 'industry'])["ln_emp"].shift(1)

# Lagged institutional measures (t-1)
df["adjcov_lag1"] = df.groupby(['country'])["adjcov"].shift(1)
df["coord_lag1"] = df.groupby(['country'])["coord"].shift(1)

# Drop rows where lagged employment is missing (needed for dynamic model)
df = df.dropna(subset=["ln_emp", "ln_emp_lag1", "va", "ict_share", "wage"])

# For institutional measures, we need at least one non-null lagged value
df = df[df["adjcov_lag1"].notna() | df["coord_lag1"].notna()]

logger.info(f"After creating lagged variables: {len(df)} observations")

# Mean-center ict_share and lagged institutional measures
ict_share_mean = df["ict_share"].mean()
adjcov_lag1_mean = df["adjcov_lag1"].mean()
coord_lag1_mean = df["coord_lag1"].mean()

df["ict_share_mc"] = df["ict_share"] - ict_share_mean
df["adjcov_lag1_mc"] = df["adjcov_lag1"] - adjcov_lag1_mean
df["coord_lag1_mc"] = df["coord_lag1"] - coord_lag1_mean

logger.info(f"Mean-centered ict_share (mean: {ict_share_mean:.6f})")
logger.info(f"Mean-centered adjcov_lag1 (mean: {adjcov_lag1_mean:.6f})")
logger.info(f"Mean-centered coord_lag1 (mean: {coord_lag1_mean:.6f})")

# Interaction terms (using mean-centered variables)
# Use only the institutional measures that are available
# We'll create interactions for both, but use them conditionally
df["ict_x_adjcov"] = df["ict_share_mc"] * df["adjcov_lag1_mc"]
df["ict_x_coord"] = df["ict_share_mc"] * df["coord_lag1_mc"]

logger.info(f"Variables created. Final dataset: {len(df)} observations")

# --- Panel index ---
# Create composite entity identifier (country-industry)
df["entity"] = df["country"] + "_" + df["industry"]
df = df.set_index(["entity", "year"])

logger.info(f"Panel structure: {df.index.nlevels} levels")
logger.info(f"Entities: {df.index.get_level_values(0).nunique()}")
logger.info(f"Time periods: {df.index.get_level_values(1).nunique()}")

# --- Regression: Dynamic model with LSDVC (Least Squares Dummy Variable Corrected) ---
# Model: lnEmp_t = α·lnEmp_{t-1} + β₁·ICT + β₂·Institution_{t-1} + β₃·(ICT × Institution_{t-1}) + β₄·lnVA + β₅·lnWage + FE + ε
# LSDVC is appropriate for small panels (small T, moderate N) and corrects the bias in LSDV estimator

# Prepare variables for regression
exog_vars = ["ln_emp_lag1", "ict_share_mc", "adjcov_lag1_mc", "coord_lag1_mc", 
              "ict_x_adjcov", "ict_x_coord", "ln_va", "ln_wage"]

# Prepare data - drop rows with any missing values in required variables
regression_df = df[exog_vars + ["ln_emp"]].copy()
regression_df = regression_df.dropna()

logger.info(f"Regression dataset: {len(regression_df)} observations")
logger.info(f"Entities in regression: {regression_df.index.get_level_values(0).nunique()}")
logger.info(f"Time periods: {regression_df.index.get_level_values(1).nunique()}")

# Get panel dimensions
N = regression_df.index.get_level_values(0).nunique()  # Number of entities
T = regression_df.index.get_level_values(1).nunique()  # Number of time periods
logger.info(f"Panel dimensions: N={N}, T={T}")

# Step 1: Run LSDV (Least Squares Dummy Variables) estimator
# This is PanelOLS with entity fixed effects
logger.info("Running LSDV estimator (first step of LSDVC)...")

mod_lsdv = PanelOLS(
    regression_df["ln_emp"],
    regression_df[exog_vars],
    entity_effects=True,   # Entity fixed effects (LSDV)
    time_effects=True      # Time fixed effects
)

res_lsdv = mod_lsdv.fit(cov_type="clustered", cluster_entity=True)

# Extract coefficients and standard errors
coef_lsdv = res_lsdv.params
se_lsdv = res_lsdv.std_errors

logger.info("LSDV estimation completed")

# Step 2: Calculate bias correction for LSDVC
# The bias correction is based on Kiviet (1995) and Bruno (2005)
# For small T panels, we apply a simplified bias correction
# The bias in the lagged dependent variable coefficient is approximately: bias ≈ -(1+α)/T

# Get the coefficient on lagged dependent variable
alpha_lsdv = coef_lsdv["ln_emp_lag1"]

# Simplified bias correction (for balanced panels with small T)
# More sophisticated corrections exist but require additional assumptions
# For small panels, the bias correction is approximately: bias ≈ -(1+α)/(T-1)
bias_correction = -(1 + alpha_lsdv) / (T - 1)

# Apply bias correction to lagged dependent variable coefficient
alpha_lsdvc = alpha_lsdv - bias_correction

logger.info(f"LSDV coefficient on lagged employment: {alpha_lsdv:.6f}")
logger.info(f"Bias correction: {bias_correction:.6f}")
logger.info(f"LSDVC corrected coefficient: {alpha_lsdvc:.6f}")

# Create corrected coefficient vector
coef_lsdvc = coef_lsdv.copy()
coef_lsdvc["ln_emp_lag1"] = alpha_lsdvc

# For other coefficients, bias is typically smaller and often negligible
# In practice, many applications only correct the lagged DV coefficient
# We'll report both LSDV and LSDVC results

print("\n" + "="*80)
print("LSDV REGRESSION RESULTS (Uncorrected)")
print("="*80)
print(res_lsdv.summary)

print("\n" + "="*80)
print("LSDVC REGRESSION RESULTS (Bias-Corrected)")
print("="*80)
print(f"\nPanel dimensions: N={N} entities, T={T} time periods")
print(f"\nCoefficient on lagged employment:")
print(f"  LSDV (uncorrected):  {alpha_lsdv:8.6f} (SE: {se_lsdv['ln_emp_lag1']:.6f})")
print(f"  Bias correction:     {bias_correction:8.6f}")
print(f"  LSDVC (corrected):   {alpha_lsdvc:8.6f}")
print(f"\nNote: Bias correction applied to lagged dependent variable coefficient.")
print(f"      Other coefficients remain from LSDV estimation.")
print(f"\nFull coefficient table (LSDVC corrected):")
print(coef_lsdvc.to_string())