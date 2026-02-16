'''
# version 3 - Robot Adoption (UN Comtrade)
- switched to LSDVC (Least Squares Dummy Variable Corrected) for small panel
- added wage proxy
- added lagged employment (dynamics)
- added lagged institutional measures (AdjCov, Coord at t-1)
- REPLACED ICT (KLEMS) with Robot Adoption (UN Comtrade)
- implemented shift-share robot exposure calculation

Regression Analysis: Employment vs Robot Adoption, Institutions, and Interaction
=================================================================================
Model: lnEmp_t = α·lnEmp_{t-1} + β₁·RobotExp + β₂·Institution_{t-1} + β₃·(RobotExp × Institution_{t-1}) + β₄·lnVA + β₅·lnWage + FE + ε

Data Sources:
- employment: Eurostat => https://ec.europa.eu/eurostat/databrowser/view/sbs_na_ind_r2__custom_19815875/default/table 
- wage proxy: Eurostat => https://ec.europa.eu/eurostat/databrowser/view/nama_10_a64/default/table?lang=en
- robot imports: UN Comtrade => https://comtradeplus.un.org (HS 847950)
- industry automation weights: OECD Task Content of Jobs => https://www.oecd.org/employment/skills-and-work/task-content-of-jobs/
- institutions: ICTWSS => https://www.oecd.org/en/data/datasets/oecdaias-ictwss-database.html

Robot Exposure Calculation (shift-share):
RobotExposure_{c i t} = (RobotImports_{c t} × Weight_i) / Employment_{c i t}
'''

import pandas as pd
import numpy as np
from loguru import logger
from linearmodels.panel import PanelOLS

# --- Load ---

logger.info(f"===== Loading data ============================================\n\n\n")

# Load raw data
sbs_raw = pd.read_csv("data/eurostat_employment.csv")
# Try reading with different encodings (UN Comtrade files may use ISO-8859-1 or Windows-1252)
try:
    comtrade_raw = pd.read_csv("data/test-uncomtradedata.csv", encoding='utf-8')  # UN Comtrade robot imports (HS 847950)
except UnicodeDecodeError:
    try:
        comtrade_raw = pd.read_csv("data/test-uncomtradedata.csv", encoding='iso-8859-1')
        logger.info("Read UN Comtrade file with ISO-8859-1 encoding")
    except UnicodeDecodeError:
        comtrade_raw = pd.read_csv("data/test-uncomtradedata.csv", encoding='windows-1252')
        logger.info("Read UN Comtrade file with Windows-1252 encoding")
weights_raw = pd.read_csv("data/test-oecd_automation_weights.csv")  # Industry automation weights
ictwss_raw = pd.read_csv("data/ictwss_institutions.csv")
wage_raw = pd.read_csv("data/eurostat_wageproxy.csv")

logger.info(f"Loaded {len(sbs_raw)} observations from Eurostat")
logger.info(f"Eurostat headers: {sbs_raw.columns.tolist()}\n")   
logger.info(f"Loaded {len(ictwss_raw)} observations from ICTWSS")
logger.info(f"ICTWSS headers: {ictwss_raw.columns.tolist()}\n")
logger.info(f"Loaded {len(comtrade_raw)} observations from UN Comtrade")
logger.info(f"UN Comtrade headers: {comtrade_raw.columns.tolist()}\n")
logger.info(f"Loaded {len(weights_raw)} observations from OECD automation weights")
logger.info(f"Automation weights headers: {weights_raw.columns.tolist()}\n")
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

# --- Process UN Comtrade robot imports data ---
logger.info("\n\n\n===== Processing UN Comtrade robot imports data ============================================\n\n\n")

# Expected columns: country (or country_code), year, robot_imports_usd (trade value in USD)
# Robot imports are at country × year level (HS 847950 - industrial robots)
# UN Comtrade data structure: reporterCode/reporterISO/reporterDesc for country, period/refYear for year, primaryValue for trade value

# Identify country column - UN Comtrade uses reporterISO, reporterDesc, or reporterCode
country_col = None
if 'country' in comtrade_raw.columns:
    country_col = 'country'
elif 'country_code' in comtrade_raw.columns:
    country_col = 'country_code'
elif 'reporterISO' in comtrade_raw.columns:
    # Prefer ISO codes (2-3 letter codes) - most reliable
    country_col = 'reporterISO'
elif 'reporterDesc' in comtrade_raw.columns:
    # Use country names/descriptions
    country_col = 'reporterDesc'
elif 'reporterCode' in comtrade_raw.columns:
    # Numeric codes - need to map via reporterDesc
    if 'reporterDesc' in comtrade_raw.columns:
        # Create mapping from code to description
        reporter_map = comtrade_raw[['reporterCode', 'reporterDesc']].drop_duplicates()
        reporter_map = reporter_map.set_index('reporterCode')['reporterDesc'].to_dict()
        comtrade_raw['reporter_name'] = comtrade_raw['reporterCode'].map(reporter_map)
        country_col = 'reporter_name'
    else:
        raise ValueError("reporterCode found but reporterDesc missing - cannot map to country names")
elif 'reporter' in comtrade_raw.columns:
    country_col = 'reporter'
else:
    raise ValueError(f"Could not find country column. Available columns: {comtrade_raw.columns.tolist()}")

logger.info(f"Using '{country_col}' column for country identification")
logger.info(f"Sample values: {comtrade_raw[country_col].head(10).tolist()}")

# Check if we have aggregate data only
has_aggregate_only = False
if 'isAggregate' in comtrade_raw.columns:
    comtrade_raw['isAggregate'] = comtrade_raw['isAggregate'].astype(str).str.lower().str.strip()
    aggregate_count = (comtrade_raw['isAggregate'] == 'true').sum()
    total_count = len(comtrade_raw)
    
    if aggregate_count == total_count and total_count > 0:
        # All data is aggregate - we'll distribute it across countries for testing
        has_aggregate_only = True
        logger.warning("⚠️  All UN Comtrade data is aggregate (world totals)")
        logger.warning("⚠️  Will distribute world totals across countries proportionally for testing")
    elif aggregate_count > 0:
        # Mix of aggregate and country-level - filter out aggregates
        initial_count = len(comtrade_raw)
        comtrade_raw = comtrade_raw[comtrade_raw['isAggregate'] != 'true']
        filtered_count = initial_count - len(comtrade_raw)
        logger.info(f"Filtered out {filtered_count} aggregate entries (isAggregate=true)")

# Map country to ISO2 codes (skip if aggregate-only - we'll distribute later)
if not has_aggregate_only:
    # First try mapping via country names (if using reporterDesc)
    comtrade_raw['country'] = comtrade_raw[country_col].map(country_mapping)
    
    # If mapping failed, check if we have ISO3 codes that need conversion
    if comtrade_raw['country'].isna().any() and country_col == 'reporterISO':
        # Create ISO3 to ISO2 mapping (common European countries)
        iso3_to_iso2 = {
            'ALB': 'AL', 'AUT': 'AT', 'BEL': 'BE', 'BGR': 'BG', 'BIH': 'BA',
            'CHE': 'CH', 'CYP': 'CY', 'CZE': 'CZ', 'DEU': 'DE', 'DNK': 'DK',
            'ESP': 'ES', 'EST': 'EE', 'FIN': 'FI', 'FRA': 'FR', 'GBR': 'GB',
            'GRC': 'GR', 'HRV': 'HR', 'HUN': 'HU', 'IRL': 'IE', 'ISL': 'IS',
            'ITA': 'IT', 'LTU': 'LT', 'LUX': 'LU', 'LVA': 'LV', 'MLT': 'MT',
            'NLD': 'NL', 'NOR': 'NO', 'POL': 'PL', 'PRT': 'PT', 'ROU': 'RO',
            'SVK': 'SK', 'SVN': 'SI', 'SWE': 'SE', 'TUR': 'TR'
        }
        
        # Convert ISO3 to ISO2
        mask = comtrade_raw['country'].isna()
        comtrade_raw.loc[mask, 'country'] = comtrade_raw.loc[mask, country_col].map(iso3_to_iso2)
        logger.info(f"Converted {mask.sum()} ISO3 codes to ISO2")
    
    # If still missing, try using codes directly (might already be ISO2)
    if comtrade_raw['country'].isna().any():
        # Check if the source column might already be ISO2 codes
        if country_col in ['reporterISO', 'country_code']:
            # Fill missing with original values (might be ISO2 codes)
            mask = comtrade_raw['country'].isna()
            comtrade_raw.loc[mask, 'country'] = comtrade_raw.loc[mask, country_col].astype(str).str.upper().str.strip()
        
        # Filter out aggregate/unknown countries (codes like "-2", "97", "W00", etc.)
        invalid_countries = ['-2', '-1', '0', '97', 'W00', 'WORLD', 'WORLD TOTAL']
        before_filter = len(comtrade_raw)
        comtrade_raw = comtrade_raw[~comtrade_raw['country'].isin(invalid_countries)]
        filtered_count = before_filter - len(comtrade_raw)
        
        if filtered_count > 0:
            logger.info(f"Filtered out {filtered_count} entries with invalid/aggregate country codes")
            logger.info(f"After filtering aggregates: {len(comtrade_raw)} observations")
        
        if len(comtrade_raw) == 0:
            logger.warning("WARNING: All UN Comtrade data was filtered out!")
            logger.warning("The data appears to contain only aggregate entries.")
            logger.warning("You need country-level robot import data (not aggregate/world totals).")
            logger.warning("Please check your UN Comtrade data file and ensure it contains country-specific entries.")
else:
    # For aggregate data, we don't need country mapping - will distribute later
    logger.info("Skipping country mapping for aggregate data (will distribute during merge)")

# Process year - check multiple possible column names
# Try different columns and use the one that has valid year values (4-digit, 2000-2030)
year_col = None
year_candidates = ['period', 'refYear', 'year']

for col in year_candidates:
    if col in comtrade_raw.columns:
        # Check if this column has values that look like years
        test_values = pd.to_numeric(comtrade_raw[col], errors='coerce').dropna()
        if len(test_values) > 0:
            # Check if values are in reasonable year range (2000-2030)
            valid_years = test_values[(test_values >= 2000) & (test_values <= 2030)]
            if len(valid_years) > len(test_values) * 0.5:  # At least 50% are valid years
                year_col = col
                logger.info(f"Using '{col}' column for year (contains valid year values)")
                break

# If no good column found, try extracting year from refPeriodId (format: YYYYMMDD)
if year_col is None:
    if 'refPeriodId' in comtrade_raw.columns:
        # Extract year from YYYYMMDD format
        comtrade_raw['year'] = pd.to_numeric(comtrade_raw['refPeriodId'].astype(str).str[:4], errors='coerce')
        logger.info("Extracted year from refPeriodId (YYYYMMDD format)")
    else:
        raise ValueError(f"Could not find year column. Available columns: {comtrade_raw.columns.tolist()}")
else:
    comtrade_raw['year'] = pd.to_numeric(comtrade_raw[year_col], errors='coerce')
    logger.info(f"Using '{year_col}' column for year")

logger.info(f"Sample year values: {comtrade_raw['year'].dropna().unique()[:10].tolist()}")

# Get robot imports value (in USD)
# Column name may vary: 'primaryValue', 'trade_value_usd', 'value', 'tradeValue', etc.
robot_value_col = None
for col in ['primaryValue', 'robot_imports_usd', 'trade_value_usd', 'value', 'tradeValue', 'TradeValue', 'fobvalue', 'cifvalue']:
    if col in comtrade_raw.columns:
        robot_value_col = col
        break

if robot_value_col is None:
    raise ValueError(f"Could not find robot imports value column. Available columns: {comtrade_raw.columns.tolist()}")

logger.info(f"Using '{robot_value_col}' column for robot imports value")
comtrade_raw['robot_imports'] = pd.to_numeric(comtrade_raw[robot_value_col], errors='coerce')

# Handle aggregate data: distribute world totals across countries proportionally
world_totals_by_year = None
if has_aggregate_only:
    # Get world totals by year
    world_totals_by_year = comtrade_raw.groupby('year')['robot_imports'].sum().reset_index()
    world_totals_by_year.columns = ['year', 'world_total']
    
    logger.info(f"World totals by year: {len(world_totals_by_year)} years")
    logger.info(f"Year range: {world_totals_by_year['year'].min():.0f} - {world_totals_by_year['year'].max():.0f}")
    
    # We'll distribute these in the merge step based on country employment shares
    # For now, create a placeholder that will be filled during merge
    comtrade = pd.DataFrame()  # Empty - will be created during merge
    logger.info("Aggregate data detected - will distribute during merge based on employment shares")
else:
    # Normal processing: aggregate at country × year level
    logger.info(f"Before filtering: {len(comtrade_raw)} observations")
    logger.info(f"Countries before filtering: {comtrade_raw['country'].nunique() if 'country' in comtrade_raw.columns else 'N/A'}")
    logger.info(f"Years before filtering: {comtrade_raw['year'].nunique() if 'year' in comtrade_raw.columns else 'N/A'}")
    if 'country' in comtrade_raw.columns:
        logger.info(f"Sample countries before filtering: {comtrade_raw['country'].dropna().unique()[:10].tolist()}")
    
    comtrade = comtrade_raw[['country', 'year', 'robot_imports']].dropna(subset=['country', 'year', 'robot_imports'])
    logger.info(f"After dropna: {len(comtrade)} observations")
    
    comtrade = comtrade.groupby(['country', 'year'])['robot_imports'].sum().reset_index()
    comtrade['country'] = comtrade['country'].astype(str).str.upper().str.strip()
    
    logger.info(f"UN Comtrade robot imports: {len(comtrade)} country-year observations after processing")
    if len(comtrade) > 0:
        logger.info(f"Countries: {comtrade['country'].nunique()}, Years: {comtrade['year'].min():.0f}-{comtrade['year'].max():.0f}")
        logger.info(f"Unique years: {sorted(comtrade['year'].unique().tolist())}")
        logger.info(f"Sample countries: {comtrade['country'].unique()[:10].tolist()}")
    else:
        logger.warning("WARNING: No country-year observations after processing UN Comtrade data!")
        logger.warning("This will cause the merge to fail. Please check your UN Comtrade data file.")
        logger.warning(f"Debug: comtrade_raw shape: {comtrade_raw.shape}")
        logger.warning(f"Debug: comtrade_raw columns: {comtrade_raw.columns.tolist()}")
        if 'country' in comtrade_raw.columns:
            logger.warning(f"Debug: country null count: {comtrade_raw['country'].isna().sum()}")
        if 'year' in comtrade_raw.columns:
            logger.warning(f"Debug: year null count: {comtrade_raw['year'].isna().sum()}")
        if 'robot_imports' in comtrade_raw.columns:
            logger.warning(f"Debug: robot_imports null count: {comtrade_raw['robot_imports'].isna().sum()}")

# --- Process industry automation weights data ---
logger.info("\n\n\n===== Processing OECD automation weights data ============================================\n\n\n")

# Expected columns: industry (NACE Rev.2 code), weight (automation/robot suitability weight)
# Standardize industry codes
weights_raw['industry'] = weights_raw['industry'].str.strip()

# Get weight column (may be named 'weight', 'automation_weight', 'robot_weight', etc.)
weight_col = None
for col in ['weight', 'automation_weight', 'robot_weight', 'Weight', 'AutomationWeight']:
    if col in weights_raw.columns:
        weight_col = col
        break

if weight_col is None:
    raise ValueError("Could not find weight column. Expected one of: weight, automation_weight, robot_weight, Weight, AutomationWeight")

weights_raw['weight'] = pd.to_numeric(weights_raw[weight_col], errors='coerce')

# Clean weights data
weights = weights_raw[['industry', 'weight']].dropna(subset=['industry', 'weight'])
weights['industry'] = weights['industry'].astype(str).str.strip()

logger.info(f"Automation weights: {len(weights)} industries")
logger.info(f"Weight range: {weights['weight'].min():.6f} - {weights['weight'].max():.6f}")

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

# --- Diagnostic: Show data availability before merging ---
logger.info("\n\n\n===== Data availability diagnostics ============================================\n\n")

# Eurostat (SBS) - country × industry × year
logger.info("Eurostat (SBS) data:")
logger.info(f"  Observations: {len(sbs)}")
if len(sbs) > 0:
    logger.info(f"  Countries: {sorted(sbs['country'].unique().tolist())}")
    logger.info(f"  Countries count: {sbs['country'].nunique()}")
    logger.info(f"  Years: {int(sbs['year'].min())} - {int(sbs['year'].max())}")
    logger.info(f"  Years count: {sbs['year'].nunique()}")
    logger.info(f"  Industries: {sbs['industry'].nunique()}")

# UN Comtrade - country × year
logger.info("\nUN Comtrade robot imports:")
logger.info(f"  Observations: {len(comtrade)}")
if len(comtrade) > 0:
    logger.info(f"  Countries: {sorted(comtrade['country'].unique().tolist())}")
    logger.info(f"  Countries count: {comtrade['country'].nunique()}")
    logger.info(f"  Years: {int(comtrade['year'].min())} - {int(comtrade['year'].max())}")
    logger.info(f"  Years count: {comtrade['year'].nunique()}")
else:
    logger.warning("  ⚠️  NO DATA - All entries filtered as aggregates")

# Wage proxy - country × year
logger.info("\nWage proxy (Eurostat):")
logger.info(f"  Observations: {len(wage_data)}")
if len(wage_data) > 0:
    logger.info(f"  Countries: {sorted(wage_data['country'].unique().tolist())}")
    logger.info(f"  Countries count: {wage_data['country'].nunique()}")
    logger.info(f"  Years: {int(wage_data['year'].min())} - {int(wage_data['year'].max())}")
    logger.info(f"  Years count: {wage_data['year'].nunique()}")

# ICTWSS - country × year
logger.info("\nICTWSS institutions:")
logger.info(f"  Observations: {len(ictwss)}")
if len(ictwss) > 0:
    logger.info(f"  Countries: {sorted(ictwss['country'].unique().tolist())}")
    logger.info(f"  Countries count: {ictwss['country'].nunique()}")
    logger.info(f"  Years: {int(ictwss['year'].min())} - {int(ictwss['year'].max())}")
    logger.info(f"  Years count: {ictwss['year'].nunique()}")

# Automation weights - industry
logger.info("\nAutomation weights:")
logger.info(f"  Industries: {len(weights)}")
logger.info(f"  Industry codes: {sorted(weights['industry'].unique().tolist())}")

# Calculate overlaps
logger.info("\n\n===== Overlap analysis ============================================\n")

if len(sbs) > 0 and len(comtrade) > 0:
    sbs_countries = set(sbs['country'].unique())
    sbs_years = set(sbs['year'].unique())
    comtrade_countries = set(comtrade['country'].unique())
    comtrade_years = set(comtrade['year'].unique())
    
    country_overlap = sbs_countries & comtrade_countries
    year_overlap = sbs_years & comtrade_years
    
    logger.info(f"Eurostat ↔ UN Comtrade overlap:")
    logger.info(f"  Common countries: {len(country_overlap)} ({sorted(country_overlap) if country_overlap else 'NONE'})")
    logger.info(f"  Common years: {len(year_overlap)} ({sorted([int(y) for y in year_overlap]) if year_overlap else 'NONE'})")
    if not country_overlap or not year_overlap:
        logger.warning("  ⚠️  NO OVERLAP - Merge will result in 0 observations")
else:
    logger.warning("Cannot calculate overlap - UN Comtrade has no data")

if len(sbs) > 0 and len(wage_data) > 0:
    sbs_countries = set(sbs['country'].unique())
    sbs_years = set(sbs['year'].unique())
    wage_countries = set(wage_data['country'].unique())
    wage_years = set(wage_data['year'].unique())
    
    country_overlap = sbs_countries & wage_countries
    year_overlap = sbs_years & wage_years
    
    logger.info(f"\nEurostat ↔ Wage proxy overlap:")
    logger.info(f"  Common countries: {len(country_overlap)} ({sorted(country_overlap) if country_overlap else 'NONE'})")
    logger.info(f"  Common years: {len(year_overlap)} ({sorted([int(y) for y in year_overlap]) if year_overlap else 'NONE'})")

if len(sbs) > 0 and len(ictwss) > 0:
    sbs_countries = set(sbs['country'].unique())
    sbs_years = set(sbs['year'].unique())
    ictwss_countries = set(ictwss['country'].unique())
    ictwss_years = set(ictwss['year'].unique())
    
    country_overlap = sbs_countries & ictwss_countries
    year_overlap = sbs_years & ictwss_years
    
    logger.info(f"\nEurostat ↔ ICTWSS overlap:")
    logger.info(f"  Common countries: {len(country_overlap)} ({sorted(country_overlap) if country_overlap else 'NONE'})")
    logger.info(f"  Common years: {len(year_overlap)} ({sorted([int(y) for y in year_overlap]) if year_overlap else 'NONE'})")

# Summary of missing years
logger.info("\n\n===== Missing years summary ============================================\n")
if len(sbs) > 0:
    sbs_years = set(sbs['year'].unique())
    all_years = sbs_years.copy()
    
    if len(comtrade) > 0:
        comtrade_years = set(comtrade['year'].unique())
        all_years.update(comtrade_years)
        missing_in_comtrade = sorted([int(y) for y in sbs_years - comtrade_years])
        if missing_in_comtrade:
            logger.info(f"Years in Eurostat but MISSING in UN Comtrade: {missing_in_comtrade}")
    
    if len(wage_data) > 0:
        wage_years = set(wage_data['year'].unique())
        all_years.update(wage_years)
        missing_in_wage = sorted([int(y) for y in sbs_years - wage_years])
        if missing_in_wage:
            logger.info(f"Years in Eurostat but MISSING in Wage proxy: {missing_in_wage}")
    
    if len(ictwss) > 0:
        ictwss_years = set(ictwss['year'].unique())
        all_years.update(ictwss_years)
        missing_in_ictwss = sorted([int(y) for y in sbs_years - ictwss_years])
        if missing_in_ictwss:
            logger.info(f"Years in Eurostat but MISSING in ICTWSS: {missing_in_ictwss}")
    
    logger.info(f"\nOverall year range across all datasets: {int(min(all_years))} - {int(max(all_years))}")
    logger.info(f"Total unique years: {len(all_years)}")

logger.info("\n" + "="*70 + "\n")

# --- Merge datasets ---
logger.info("\n\n\n===== Merging datasets ============================================\n\n\n")

# Merge SBS with automation weights (to get weights for each industry)
df = sbs.merge(weights, on=['industry'], how='inner')
logger.info(f"After SBS-weights merge: {len(df)} observations")

# Merge with robot imports (country × year level)
# Handle three cases: 1) normal country-level data, 2) aggregate data (distribute), 3) no data (zeros)
if world_totals_by_year is not None:
    # Case 2: Aggregate data - distribute world totals proportionally by country employment share
    logger.warning("⚠️  Distributing aggregate world totals across countries based on employment shares")
    
    # Calculate total employment by country-year (sum across industries)
    country_year_emp = df.groupby(['country', 'year'])['emp'].sum().reset_index()
    country_year_emp.columns = ['country', 'year', 'total_emp']
    
    # Calculate world employment by year (sum across all countries)
    world_emp_by_year = country_year_emp.groupby('year')['total_emp'].sum().reset_index()
    world_emp_by_year.columns = ['year', 'world_emp']
    
    # Merge to get employment shares
    country_year_emp = country_year_emp.merge(world_emp_by_year, on='year', how='left')
    country_year_emp['emp_share'] = country_year_emp['total_emp'] / country_year_emp['world_emp']
    
    # Merge world totals and distribute
    country_year_emp = country_year_emp.merge(world_totals_by_year, on='year', how='left')
    country_year_emp['robot_imports'] = country_year_emp['world_total'] * country_year_emp['emp_share']
    country_year_emp = country_year_emp[['country', 'year', 'robot_imports']]
    
    # Merge back to main dataframe
    df = df.merge(country_year_emp, on=['country', 'year'], how='left')
    df['robot_imports'] = df['robot_imports'].fillna(0)
    logger.info(f"After robot imports merge (distributed from aggregates): {len(df)} observations")
    logger.info(f"Robot imports range: {df['robot_imports'].min():.2f} - {df['robot_imports'].max():.2f}")
    
elif len(comtrade) == 0:
    # Case 3: No data - set to zero for testing
    logger.warning("⚠️  UN Comtrade has no data - setting robot_imports=0 for testing")
    df['robot_imports'] = 0
    logger.info(f"After robot imports merge (with zeros): {len(df)} observations")
else:
    # Case 1: Normal country-level data
    df = df.merge(comtrade, on=['country', 'year'], how='inner')
    logger.info(f"After robot imports merge: {len(df)} observations")

# Merge with wage proxy
df = df.merge(wage_data, on=['country', 'year'], how='inner')
logger.info(f"After wage proxy merge: {len(df)} observations")

# Merge with ICTWSS
df = df.merge(ictwss, on=['country', 'year'], how='inner')
logger.info(f"After ICTWSS merge: {len(df)} observations")

logger.info(f"Final dataset: {len(df)} observations")
logger.info(f"Countries: {df['country'].nunique()}")
logger.info(f"Industries: {df['industry'].nunique()}")
if len(df) > 0:
    logger.info(f"Years: {df['year'].min():.0f} - {df['year'].max():.0f}")
    if len(comtrade) == 0:
        logger.warning("⚠️  Running TEST regression with robot_imports=0 (UN Comtrade data missing)")
        logger.warning("⚠️  Robot exposure will be zero - this is for testing the pipeline only")
else:
    logger.warning("WARNING: Final dataset has 0 observations after merging!")
    logger.warning("This likely means:")
    logger.warning("  1. UN Comtrade data contains only aggregate entries (need country-level data)")
    logger.warning("  2. Data sources don't have overlapping countries/years")
    logger.warning("  3. Country codes don't match across datasets")
    logger.error("Cannot proceed with regression - no data available.")
    raise ValueError("Final dataset has 0 observations. Check data sources and country mappings.")

# --- Final cleaning and variable creation ---
logger.info("\n\n\n===== Creating variables & running regression ============================================\n\n\n")

# Ensure numeric types
df["emp"] = pd.to_numeric(df["emp"], errors='coerce')
df["va"] = pd.to_numeric(df["va"], errors='coerce')
# robot_imports may be missing (filled with 0) - that's OK for testing
if "robot_imports" not in df.columns:
    df["robot_imports"] = 0
df["robot_imports"] = pd.to_numeric(df["robot_imports"], errors='coerce').fillna(0)
df["weight"] = pd.to_numeric(df["weight"], errors='coerce')
df["wage"] = pd.to_numeric(df["wage"], errors='coerce')
df["adjcov"] = pd.to_numeric(df["adjcov"], errors='coerce')
df["coord"] = pd.to_numeric(df["coord"], errors='coerce')

# Remove zeros and infinities (avoid log issues)
# Note: robot_imports can be 0 (for testing when UN Comtrade data is missing)
df = df[(df["emp"] > 0) & (df["va"] > 0) & (df["wage"] > 0) & (df["robot_imports"] >= 0) & (df["weight"] > 0)]
df = df.replace([np.inf, -np.inf], np.nan)

logger.info(f"After initial cleaning: {len(df)} observations")

# Calculate Robot Exposure using shift-share logic
# RobotExposure_{c i t} = (RobotImports_{c t} × Weight_i) / Employment_{c i t}
df["robot_exposure"] = (df["robot_imports"] * df["weight"]) / df["emp"]

logger.info(f"Robot exposure calculated. Range: {df['robot_exposure'].min():.6f} - {df['robot_exposure'].max():.6f}")

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
df = df.dropna(subset=["ln_emp", "ln_emp_lag1", "va", "robot_exposure", "wage"])

# For institutional measures, we need at least one non-null lagged value
df = df[df["adjcov_lag1"].notna() | df["coord_lag1"].notna()]

logger.info(f"After creating lagged variables: {len(df)} observations")

# Mean-center robot_exposure and lagged institutional measures
robot_exposure_mean = df["robot_exposure"].mean()
adjcov_lag1_mean = df["adjcov_lag1"].mean()
coord_lag1_mean = df["coord_lag1"].mean()

df["robot_exposure_mc"] = df["robot_exposure"] - robot_exposure_mean
df["adjcov_lag1_mc"] = df["adjcov_lag1"] - adjcov_lag1_mean
df["coord_lag1_mc"] = df["coord_lag1"] - coord_lag1_mean

logger.info(f"Mean-centered robot_exposure (mean: {robot_exposure_mean:.6f})")
logger.info(f"Mean-centered adjcov_lag1 (mean: {adjcov_lag1_mean:.6f})")
logger.info(f"Mean-centered coord_lag1 (mean: {coord_lag1_mean:.6f})")

# Interaction terms (using mean-centered variables)
# Use only the institutional measures that are available
# We'll create interactions for both, but use them conditionally
df["robot_x_adjcov"] = df["robot_exposure_mc"] * df["adjcov_lag1_mc"]
df["robot_x_coord"] = df["robot_exposure_mc"] * df["coord_lag1_mc"]

logger.info(f"Variables created. Final dataset: {len(df)} observations")

if len(df) == 0:
    logger.error("ERROR: Dataset has 0 observations after variable creation.")
    logger.error("Cannot proceed with regression - no data available.")
    raise ValueError("Dataset has 0 observations after variable creation. Check data quality and filters.")

# --- Panel index ---
# Create composite entity identifier (country-industry)
df["entity"] = df["country"] + "_" + df["industry"]
df = df.set_index(["entity", "year"])

logger.info(f"Panel structure: {df.index.nlevels} levels")
logger.info(f"Entities: {df.index.get_level_values(0).nunique()}")
logger.info(f"Time periods: {df.index.get_level_values(1).nunique()}")

# --- Regression: Dynamic model with LSDVC (Least Squares Dummy Variable Corrected) ---
# Model: lnEmp_t = α·lnEmp_{t-1} + β₁·RobotExp + β₂·Institution_{t-1} + β₃·(RobotExp × Institution_{t-1}) + β₄·lnVA + β₅·lnWage + FE + ε
# LSDVC is appropriate for small panels (small T, moderate N) and corrects the bias in LSDV estimator

# Prepare variables for regression
exog_vars = ["ln_emp_lag1", "robot_exposure_mc", "adjcov_lag1_mc", "coord_lag1_mc", 
              "robot_x_adjcov", "robot_x_coord", "ln_va", "ln_wage"]

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

if len(regression_df) == 0:
    logger.error("ERROR: Regression dataset has 0 observations after dropping missing values.")
    logger.error("Cannot proceed with regression - no data available.")
    raise ValueError("Regression dataset has 0 observations. Check for missing values in required variables.")

if N == 0 or T == 0:
    logger.error(f"ERROR: Invalid panel dimensions (N={N}, T={T}). Need at least 1 entity and 1 time period.")
    raise ValueError(f"Invalid panel dimensions: N={N}, T={T}")

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