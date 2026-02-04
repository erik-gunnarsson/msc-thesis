'''
Visualization script for ICTWSS regression analysis outputs
Creates graphs and charts of regression results and data patterns
'''

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import os
from loguru import logger

# Try to import seaborn, but make it optional
try:
    import seaborn as sns
    sns.set_style("whitegrid")
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False
    logger.warning("seaborn not available, using matplotlib defaults")

# Set style
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

# Create outputs directory if it doesn't exist
output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)

logger.info("Starting visualization generation...")


def load_and_prepare_data():
    """Load and prepare data (similar to mainv2.py)"""
    logger.info("Loading data files...")
    
    # Load raw data
    sbs_raw = pd.read_csv("data/eurostat_employment.csv")
    klem_raw = pd.read_csv("data/klems_growth_accounts_basic.csv")
    ictwss_raw = pd.read_csv("data/ictwss_institutions.csv")
    wage_raw = pd.read_csv("data/eurostat_wageproxy.csv")
    
    # Country mapping
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
    
    # Industry mapping
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
    sbs_emp = sbs_raw[sbs_raw['indic_sb'] == 'Persons employed - number'].copy()
    sbs_emp['country'] = sbs_emp['geo'].map(country_mapping)
    sbs_emp['industry'] = sbs_emp['nace_r2'].str.strip().map(industry_mapping)
    sbs_emp['year'] = pd.to_numeric(sbs_emp['TIME_PERIOD'], errors='coerce')
    sbs_emp['emp'] = pd.to_numeric(sbs_emp['OBS_VALUE'], errors='coerce')
    sbs_emp = sbs_emp[['country', 'industry', 'year', 'emp']].dropna(subset=['country', 'industry', 'year', 'emp'])
    sbs_emp = sbs_emp.groupby(['country', 'industry', 'year'])['emp'].sum().reset_index()
    
    # Process value added data
    sbs_va = sbs_raw[sbs_raw['indic_sb'] == 'Value added at factor cost - million euro'].copy()
    sbs_va['country'] = sbs_va['geo'].map(country_mapping)
    sbs_va['industry'] = sbs_va['nace_r2'].str.strip().map(industry_mapping)
    sbs_va['year'] = pd.to_numeric(sbs_va['TIME_PERIOD'], errors='coerce')
    sbs_va['va'] = pd.to_numeric(sbs_va['OBS_VALUE'], errors='coerce')
    sbs_va = sbs_va[['country', 'industry', 'year', 'va']].dropna(subset=['country', 'industry', 'year', 'va'])
    sbs_va = sbs_va.groupby(['country', 'industry', 'year'])['va'].sum().reset_index()
    
    # Merge employment and value added
    sbs = sbs_emp.merge(sbs_va, on=['country', 'industry', 'year'], how='outer')
    sbs['country'] = sbs['country'].str.upper().str.strip()
    sbs['industry'] = sbs['industry'].astype(str).str.strip()
    
    # Process wage proxy data
    wage_data = wage_raw[
        (wage_raw['na_item'] == 'Compensation of employees') & 
        (wage_raw['nace_r2'] == 'Manufacturing')
    ].copy()
    wage_data['country'] = wage_data['geo'].map(country_mapping)
    wage_data['year'] = pd.to_numeric(wage_data['TIME_PERIOD'], errors='coerce')
    wage_data['wage'] = pd.to_numeric(wage_data['OBS_VALUE'], errors='coerce')
    wage_data = wage_data[['country', 'year', 'wage']].dropna(subset=['country', 'year', 'wage'])
    wage_data = wage_data.groupby(['country', 'year'])['wage'].sum().reset_index()
    wage_data['country'] = wage_data['country'].str.upper().str.strip()
    
    # Process KLEMS data
    klem_ict = klem_raw[klem_raw['var'] == 'CAPICT_QI'].copy()
    klem_total = klem_raw[klem_raw['var'] == 'CAP_QI'].copy()
    klem_ict['country'] = klem_ict['geo_code'].str.upper().str.strip().replace('EL', 'GR')
    klem_total['country'] = klem_total['geo_code'].str.upper().str.strip().replace('EL', 'GR')
    klem_ict['industry'] = klem_ict['nace_r2_code'].str.strip()
    klem_total['industry'] = klem_total['nace_r2_code'].str.strip()
    klem_ict['year'] = pd.to_numeric(klem_ict['year'], errors='coerce')
    klem_total['year'] = pd.to_numeric(klem_total['year'], errors='coerce')
    klem_ict['ict_cap'] = pd.to_numeric(klem_ict['value'], errors='coerce')
    klem_total['total_cap'] = pd.to_numeric(klem_total['value'], errors='coerce')
    klem_ict = klem_ict[['country', 'industry', 'year', 'ict_cap']].dropna(subset=['country', 'industry', 'year', 'ict_cap'])
    klem_total = klem_total[['country', 'industry', 'year', 'total_cap']].dropna(subset=['country', 'industry', 'year', 'total_cap'])
    klem = klem_ict.merge(klem_total, on=['country', 'industry', 'year'], how='inner')
    klem['ict_share'] = klem['ict_cap'] / klem['total_cap']
    klem = klem[['country', 'industry', 'year', 'ict_share']].dropna(subset=['ict_share'])
    
    # Process ICTWSS data
    ictwss_raw['country_iso2'] = ictwss_raw['country'].map(country_mapping)
    iso3_to_iso2 = {
        'ALB': 'AL', 'AUT': 'AT', 'BEL': 'BE', 'BGR': 'BG', 'HRV': 'HR',
        'CYP': 'CY', 'CZE': 'CZ', 'DNK': 'DK', 'EST': 'EE', 'FIN': 'FI',
        'FRA': 'FR', 'DEU': 'DE', 'GRC': 'GR', 'HUN': 'HU', 'IRL': 'IE',
        'ITA': 'IT', 'LVA': 'LV', 'LTU': 'LT', 'LUX': 'LU', 'MLT': 'MT',
        'NLD': 'NL', 'POL': 'PL', 'PRT': 'PT', 'ROU': 'RO', 'SVK': 'SK',
        'SVN': 'SI', 'ESP': 'ES', 'SWE': 'SE', 'GBR': 'GB', 'ISL': 'IS',
        'NOR': 'NO', 'CHE': 'CH', 'TUR': 'TR'
    }
    ictwss_raw.loc[ictwss_raw['country_iso2'].isna(), 'country_iso2'] = \
        ictwss_raw.loc[ictwss_raw['country_iso2'].isna(), 'iso3'].map(iso3_to_iso2)
    ictwss_raw['country'] = ictwss_raw['country_iso2'].str.upper().str.strip()
    ictwss_raw['year'] = pd.to_numeric(ictwss_raw['year'], errors='coerce')
    ictwss = ictwss_raw[['country', 'year', 'AdjCov', 'Coord']].copy()
    ictwss['adjcov'] = pd.to_numeric(ictwss['AdjCov'], errors='coerce')
    ictwss['coord'] = pd.to_numeric(ictwss['Coord'], errors='coerce')
    ictwss = ictwss.dropna(subset=['country', 'year'])
    ictwss = ictwss[['country', 'year', 'adjcov', 'coord']]
    
    # Merge datasets
    df = sbs.merge(klem, on=['country', 'industry', 'year'], how='inner')
    df = df.merge(wage_data, on=['country', 'year'], how='inner')
    df = df.merge(ictwss, on=['country', 'year'], how='inner')
    
    # Clean and create variables
    df["emp"] = pd.to_numeric(df["emp"], errors='coerce')
    df["va"] = pd.to_numeric(df["va"], errors='coerce')
    df["ict_share"] = pd.to_numeric(df["ict_share"], errors='coerce')
    df["wage"] = pd.to_numeric(df["wage"], errors='coerce')
    df["adjcov"] = pd.to_numeric(df["adjcov"], errors='coerce')
    df["coord"] = pd.to_numeric(df["coord"], errors='coerce')
    
    df = df[(df["emp"] > 0) & (df["va"] > 0) & (df["wage"] > 0)]
    df = df.replace([np.inf, -np.inf], np.nan)
    
    df["ln_emp"] = np.log(df["emp"])
    df["ln_va"] = np.log(df["va"])
    df["ln_wage"] = np.log(df["wage"])
    
    df = df.sort_values(['country', 'industry', 'year'])
    df["ln_emp_lag1"] = df.groupby(['country', 'industry'])["ln_emp"].shift(1)
    df["adjcov_lag1"] = df.groupby(['country'])["adjcov"].shift(1)
    df["coord_lag1"] = df.groupby(['country'])["coord"].shift(1)
    
    df = df.dropna(subset=["ln_emp", "ln_emp_lag1", "va", "ict_share", "wage"])
    df = df[df["adjcov_lag1"].notna() | df["coord_lag1"].notna()]
    
    # Mean-center variables
    ict_share_mean = df["ict_share"].mean()
    adjcov_lag1_mean = df["adjcov_lag1"].mean()
    coord_lag1_mean = df["coord_lag1"].mean()
    
    df["ict_share_mc"] = df["ict_share"] - ict_share_mean
    df["adjcov_lag1_mc"] = df["adjcov_lag1"] - adjcov_lag1_mean
    df["coord_lag1_mc"] = df["coord_lag1"] - coord_lag1_mean
    
    df["ict_x_adjcov"] = df["ict_share_mc"] * df["adjcov_lag1_mc"]
    df["ict_x_coord"] = df["ict_share_mc"] * df["coord_lag1_mc"]
    
    return df


def plot_regression_coefficients(res_lsdv, coef_lsdvc, se_lsdv, output_dir):
    """Plot regression coefficients with confidence intervals"""
    logger.info("Creating regression coefficients plot...")
    
    # Prepare data for plotting
    coef_names = coef_lsdvc.index.tolist()
    coef_values = coef_lsdvc.values
    se_values = se_lsdv.values
    
    # Create confidence intervals (95%)
    ci_lower = coef_values - 1.96 * se_values
    ci_upper = coef_values + 1.96 * se_values
    
    # Create DataFrame for easier plotting
    plot_df = pd.DataFrame({
        'coefficient': coef_names,
        'value': coef_values,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper
    })
    
    # Sort by absolute value for better visualization
    plot_df['abs_value'] = np.abs(plot_df['value'])
    plot_df = plot_df.sort_values('abs_value', ascending=True)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    y_pos = np.arange(len(plot_df))
    colors = ['red' if v < 0 else 'blue' for v in plot_df['value']]
    
    # Plot bars
    bars = ax.barh(y_pos, plot_df['value'], color=colors, alpha=0.7, edgecolor='black')
    
    # Add error bars (confidence intervals)
    ax.errorbar(plot_df['value'], y_pos, 
                xerr=[plot_df['value'] - plot_df['ci_lower'], plot_df['ci_upper'] - plot_df['value']],
                fmt='none', color='black', capsize=5, capthick=1.5)
    
    # Add vertical line at zero
    ax.axvline(x=0, color='black', linestyle='--', linewidth=1)
    
    # Labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(plot_df['coefficient'])
    ax.set_xlabel('Coefficient Estimate', fontsize=12, fontweight='bold')
    ax.set_title('LSDVC Regression Coefficients with 95% Confidence Intervals', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Add value labels on bars
    for i, (val, ci_l, ci_u) in enumerate(zip(plot_df['value'], plot_df['ci_lower'], plot_df['ci_upper'])):
        ax.text(val, i, f' {val:.4f}', va='center', 
                ha='left' if val > 0 else 'right', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_dir / '01_regression_coefficients.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info("Saved: 01_regression_coefficients.png")


def plot_data_overview(df, output_dir):
    """Plot overview of the dataset"""
    logger.info("Creating data overview plots...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Distribution of employment (log)
    axes[0, 0].hist(df['ln_emp'].dropna(), bins=50, edgecolor='black', alpha=0.7, color='steelblue')
    axes[0, 0].set_xlabel('Log Employment', fontweight='bold')
    axes[0, 0].set_ylabel('Frequency', fontweight='bold')
    axes[0, 0].set_title('Distribution of Log Employment', fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Distribution of ICT share
    axes[0, 1].hist(df['ict_share'].dropna(), bins=50, edgecolor='black', alpha=0.7, color='green')
    axes[0, 1].set_xlabel('ICT Share', fontweight='bold')
    axes[0, 1].set_ylabel('Frequency', fontweight='bold')
    axes[0, 1].set_title('Distribution of ICT Capital Share', fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Distribution of institutional measures
    axes[1, 0].hist(df['adjcov_lag1'].dropna(), bins=30, alpha=0.6, label='AdjCov', color='orange', edgecolor='black')
    axes[1, 0].hist(df['coord_lag1'].dropna(), bins=30, alpha=0.6, label='Coord', color='purple', edgecolor='black')
    axes[1, 0].set_xlabel('Institutional Measure Value', fontweight='bold')
    axes[1, 0].set_ylabel('Frequency', fontweight='bold')
    axes[1, 0].set_title('Distribution of Institutional Measures (Lagged)', fontweight='bold')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Time coverage
    year_counts = df.groupby('year').size()
    axes[1, 1].plot(year_counts.index, year_counts.values, marker='o', linewidth=2, markersize=6, color='darkred')
    axes[1, 1].set_xlabel('Year', fontweight='bold')
    axes[1, 1].set_ylabel('Number of Observations', fontweight='bold')
    axes[1, 1].set_title('Observations by Year', fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_dir / '02_data_overview.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info("Saved: 02_data_overview.png")


def plot_time_series(df, output_dir):
    """Plot time series of key variables"""
    logger.info("Creating time series plots...")
    
    # Aggregate by year for overall trends
    yearly = df.groupby('year').agg({
        'ln_emp': 'mean',
        'ict_share': 'mean',
        'adjcov_lag1': 'mean',
        'coord_lag1': 'mean',
        'ln_va': 'mean',
        'ln_wage': 'mean'
    }).reset_index()
    
    fig, axes = plt.subplots(3, 2, figsize=(16, 14))
    
    # Employment trend
    axes[0, 0].plot(yearly['year'], yearly['ln_emp'], marker='o', linewidth=2, markersize=6, color='steelblue')
    axes[0, 0].set_xlabel('Year', fontweight='bold')
    axes[0, 0].set_ylabel('Mean Log Employment', fontweight='bold')
    axes[0, 0].set_title('Average Employment Over Time', fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3)
    
    # ICT share trend
    axes[0, 1].plot(yearly['year'], yearly['ict_share'], marker='o', linewidth=2, markersize=6, color='green')
    axes[0, 1].set_xlabel('Year', fontweight='bold')
    axes[0, 1].set_ylabel('Mean ICT Share', fontweight='bold')
    axes[0, 1].set_title('Average ICT Capital Share Over Time', fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Institutional measures
    axes[1, 0].plot(yearly['year'], yearly['adjcov_lag1'], marker='o', linewidth=2, markersize=6, 
                     label='AdjCov', color='orange')
    axes[1, 0].set_xlabel('Year', fontweight='bold')
    axes[1, 0].set_ylabel('Mean Adjusted Coverage', fontweight='bold')
    axes[1, 0].set_title('Average Adjusted Bargaining Coverage Over Time', fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend()
    
    axes[1, 1].plot(yearly['year'], yearly['coord_lag1'], marker='o', linewidth=2, markersize=6, 
                    label='Coord', color='purple')
    axes[1, 1].set_xlabel('Year', fontweight='bold')
    axes[1, 1].set_ylabel('Mean Coordination Index', fontweight='bold')
    axes[1, 1].set_title('Average Wage Coordination Over Time', fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].legend()
    
    # Value added
    axes[2, 0].plot(yearly['year'], yearly['ln_va'], marker='o', linewidth=2, markersize=6, color='darkred')
    axes[2, 0].set_xlabel('Year', fontweight='bold')
    axes[2, 0].set_ylabel('Mean Log Value Added', fontweight='bold')
    axes[2, 0].set_title('Average Value Added Over Time', fontweight='bold')
    axes[2, 0].grid(True, alpha=0.3)
    
    # Wages
    axes[2, 1].plot(yearly['year'], yearly['ln_wage'], marker='o', linewidth=2, markersize=6, color='teal')
    axes[2, 1].set_xlabel('Year', fontweight='bold')
    axes[2, 1].set_ylabel('Mean Log Wage', fontweight='bold')
    axes[2, 1].set_title('Average Wage Proxy Over Time', fontweight='bold')
    axes[2, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / '03_time_series.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info("Saved: 03_time_series.png")


def plot_country_comparison(df, output_dir):
    """Plot country-level comparisons"""
    logger.info("Creating country comparison plots...")
    
    # Aggregate by country
    country_stats = df.groupby('country').agg({
        'ln_emp': 'mean',
        'ict_share': 'mean',
        'adjcov_lag1': 'mean',
        'coord_lag1': 'mean'
    }).reset_index()
    
    # Sort by ICT share for better visualization
    country_stats = country_stats.sort_values('ict_share', ascending=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    
    # Top 15 countries by ICT share
    top_countries = country_stats.tail(15)
    
    # ICT share by country
    axes[0, 0].barh(range(len(top_countries)), top_countries['ict_share'], color='green', alpha=0.7, edgecolor='black')
    axes[0, 0].set_yticks(range(len(top_countries)))
    axes[0, 0].set_yticklabels(top_countries['country'])
    axes[0, 0].set_xlabel('Mean ICT Share', fontweight='bold')
    axes[0, 0].set_title('Top 15 Countries by ICT Capital Share', fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3, axis='x')
    
    # Employment by country
    axes[0, 1].barh(range(len(top_countries)), top_countries['ln_emp'], color='steelblue', alpha=0.7, edgecolor='black')
    axes[0, 1].set_yticks(range(len(top_countries)))
    axes[0, 1].set_yticklabels(top_countries['country'])
    axes[0, 1].set_xlabel('Mean Log Employment', fontweight='bold')
    axes[0, 1].set_title('Mean Employment by Country (Top 15 ICT)', fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3, axis='x')
    
    # Institutional measures by country
    country_stats_inst = country_stats.sort_values('adjcov_lag1', ascending=True)
    top_inst = country_stats_inst.tail(15)
    
    x = np.arange(len(top_inst))
    width = 0.35
    axes[1, 0].barh(x - width/2, top_inst['adjcov_lag1'], width, label='AdjCov', color='orange', alpha=0.7, edgecolor='black')
    axes[1, 0].barh(x + width/2, top_inst['coord_lag1'], width, label='Coord', color='purple', alpha=0.7, edgecolor='black')
    axes[1, 0].set_yticks(x)
    axes[1, 0].set_yticklabels(top_inst['country'])
    axes[1, 0].set_xlabel('Institutional Measure Value', fontweight='bold')
    axes[1, 0].set_title('Top 15 Countries by Adjusted Coverage', fontweight='bold')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3, axis='x')
    
    # Scatter: ICT vs Employment
    axes[1, 1].scatter(country_stats['ict_share'], country_stats['ln_emp'], 
                       s=100, alpha=0.6, color='darkblue', edgecolors='black')
    axes[1, 1].set_xlabel('Mean ICT Share', fontweight='bold')
    axes[1, 1].set_ylabel('Mean Log Employment', fontweight='bold')
    axes[1, 1].set_title('ICT Share vs Employment by Country', fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3)
    
    # Add country labels for outliers
    for idx, row in country_stats.iterrows():
        if row['ict_share'] > country_stats['ict_share'].quantile(0.9) or \
           row['ln_emp'] > country_stats['ln_emp'].quantile(0.9):
            axes[1, 1].annotate(row['country'], (row['ict_share'], row['ln_emp']), 
                               fontsize=8, alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_dir / '04_country_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info("Saved: 04_country_comparison.png")


def plot_industry_comparison(df, output_dir):
    """Plot industry-level comparisons"""
    logger.info("Creating industry comparison plots...")
    
    # Aggregate by industry
    industry_stats = df.groupby('industry').agg({
        'ln_emp': 'mean',
        'ict_share': 'mean',
        'ln_va': 'mean'
    }).reset_index()
    
    # Sort by ICT share
    industry_stats = industry_stats.sort_values('ict_share', ascending=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    
    # Top industries by ICT share
    top_industries = industry_stats.tail(15)
    
    # ICT share by industry
    axes[0, 0].barh(range(len(top_industries)), top_industries['ict_share'], 
                    color='green', alpha=0.7, edgecolor='black')
    axes[0, 0].set_yticks(range(len(top_industries)))
    axes[0, 0].set_yticklabels(top_industries['industry'], fontsize=9)
    axes[0, 0].set_xlabel('Mean ICT Share', fontweight='bold')
    axes[0, 0].set_title('Top 15 Industries by ICT Capital Share', fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3, axis='x')
    
    # Employment by industry
    axes[0, 1].barh(range(len(top_industries)), top_industries['ln_emp'], 
                    color='steelblue', alpha=0.7, edgecolor='black')
    axes[0, 1].set_yticks(range(len(top_industries)))
    axes[0, 1].set_yticklabels(top_industries['industry'], fontsize=9)
    axes[0, 1].set_xlabel('Mean Log Employment', fontweight='bold')
    axes[0, 1].set_title('Mean Employment by Industry (Top 15 ICT)', fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3, axis='x')
    
    # Value added by industry
    industry_stats_va = industry_stats.sort_values('ln_va', ascending=True)
    top_va = industry_stats_va.tail(15)
    
    axes[1, 0].barh(range(len(top_va)), top_va['ln_va'], color='darkred', alpha=0.7, edgecolor='black')
    axes[1, 0].set_yticks(range(len(top_va)))
    axes[1, 0].set_yticklabels(top_va['industry'], fontsize=9)
    axes[1, 0].set_xlabel('Mean Log Value Added', fontweight='bold')
    axes[1, 0].set_title('Top 15 Industries by Value Added', fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3, axis='x')
    
    # Scatter: ICT vs Employment by industry
    axes[1, 1].scatter(industry_stats['ict_share'], industry_stats['ln_emp'], 
                       s=100, alpha=0.6, color='darkblue', edgecolors='black')
    axes[1, 1].set_xlabel('Mean ICT Share', fontweight='bold')
    axes[1, 1].set_ylabel('Mean Log Employment', fontweight='bold')
    axes[1, 1].set_title('ICT Share vs Employment by Industry', fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3)
    
    # Add industry labels for high ICT industries
    for idx, row in industry_stats.iterrows():
        if row['ict_share'] > industry_stats['ict_share'].quantile(0.85):
            axes[1, 1].annotate(row['industry'], (row['ict_share'], row['ln_emp']), 
                               fontsize=7, alpha=0.7, rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_dir / '05_industry_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info("Saved: 05_industry_comparison.png")


def plot_relationships(df, output_dir):
    """Plot relationships between key variables"""
    logger.info("Creating relationship plots...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Sample data for scatter plots (to avoid overcrowding)
    sample_df = df.sample(min(5000, len(df)), random_state=42)
    
    # ICT vs Employment
    axes[0, 0].scatter(sample_df['ict_share'], sample_df['ln_emp'], 
                      alpha=0.3, s=20, color='steelblue', edgecolors='none')
    axes[0, 0].set_xlabel('ICT Share', fontweight='bold')
    axes[0, 0].set_ylabel('Log Employment', fontweight='bold')
    axes[0, 0].set_title('ICT Share vs Employment', fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Add trend line
    z = np.polyfit(sample_df['ict_share'].dropna(), sample_df['ln_emp'].dropna(), 1)
    p = np.poly1d(z)
    axes[0, 0].plot(sample_df['ict_share'].sort_values(), 
                    p(sample_df['ict_share'].sort_values()), 
                    "r--", alpha=0.8, linewidth=2, label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')
    axes[0, 0].legend()
    
    # Institutional measures vs Employment
    inst_data = sample_df[['adjcov_lag1', 'coord_lag1', 'ln_emp']].dropna()
    axes[0, 1].scatter(inst_data['adjcov_lag1'], inst_data['ln_emp'], 
                      alpha=0.3, s=20, color='orange', label='AdjCov', edgecolors='none')
    axes[0, 1].scatter(inst_data['coord_lag1'], inst_data['ln_emp'], 
                      alpha=0.3, s=20, color='purple', label='Coord', edgecolors='none')
    axes[0, 1].set_xlabel('Institutional Measure (Lagged)', fontweight='bold')
    axes[0, 1].set_ylabel('Log Employment', fontweight='bold')
    axes[0, 1].set_title('Institutional Measures vs Employment', fontweight='bold')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Value Added vs Employment
    axes[1, 0].scatter(sample_df['ln_va'], sample_df['ln_emp'], 
                      alpha=0.3, s=20, color='darkred', edgecolors='none')
    axes[1, 0].set_xlabel('Log Value Added', fontweight='bold')
    axes[1, 0].set_ylabel('Log Employment', fontweight='bold')
    axes[1, 0].set_title('Value Added vs Employment', fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Add trend line
    z2 = np.polyfit(sample_df['ln_va'].dropna(), sample_df['ln_emp'].dropna(), 1)
    p2 = np.poly1d(z2)
    axes[1, 0].plot(sample_df['ln_va'].sort_values(), 
                    p2(sample_df['ln_va'].sort_values()), 
                    "r--", alpha=0.8, linewidth=2, label=f'Trend: y={z2[0]:.2f}x+{z2[1]:.2f}')
    axes[1, 0].legend()
    
    # Correlation heatmap
    corr_vars = ['ln_emp', 'ict_share', 'adjcov_lag1', 'coord_lag1', 'ln_va', 'ln_wage']
    corr_data = df[corr_vars].corr()
    
    im = axes[1, 1].imshow(corr_data, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
    axes[1, 1].set_xticks(range(len(corr_vars)))
    axes[1, 1].set_yticks(range(len(corr_vars)))
    axes[1, 1].set_xticklabels(corr_vars, rotation=45, ha='right')
    axes[1, 1].set_yticklabels(corr_vars)
    axes[1, 1].set_title('Correlation Matrix', fontweight='bold')
    
    # Add correlation values
    for i in range(len(corr_vars)):
        for j in range(len(corr_vars)):
            text = axes[1, 1].text(j, i, f'{corr_data.iloc[i, j]:.2f}',
                                 ha="center", va="center", color="black", fontweight='bold')
    
    plt.colorbar(im, ax=axes[1, 1])
    
    plt.tight_layout()
    plt.savefig(output_dir / '06_relationships.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info("Saved: 06_relationships.png")


def plot_panel_structure(df, output_dir):
    """Visualize panel data structure"""
    logger.info("Creating panel structure visualization...")
    
    # Reset index to get country, industry, year back
    df_reset = df.reset_index()
    df_reset['entity'] = df_reset['country'] + '_' + df_reset['industry']
    
    # Count observations per entity
    entity_counts = df_reset.groupby('entity').size().sort_values(ascending=False)
    
    # Count entities per country
    country_entities = df_reset.groupby('country')['entity'].nunique().sort_values(ascending=False)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Distribution of observations per entity
    axes[0, 0].hist(entity_counts.values, bins=30, edgecolor='black', alpha=0.7, color='steelblue')
    axes[0, 0].set_xlabel('Number of Observations per Entity', fontweight='bold')
    axes[0, 0].set_ylabel('Frequency', fontweight='bold')
    axes[0, 0].set_title('Distribution of Observations per Entity (Country-Industry)', fontweight='bold')
    axes[0, 0].axvline(entity_counts.mean(), color='red', linestyle='--', linewidth=2, 
                       label=f'Mean: {entity_counts.mean():.1f}')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Top entities by number of observations
    top_entities = entity_counts.head(20)
    axes[0, 1].barh(range(len(top_entities)), top_entities.values, color='green', alpha=0.7, edgecolor='black')
    axes[0, 1].set_yticks(range(len(top_entities)))
    axes[0, 1].set_yticklabels(top_entities.index, fontsize=8)
    axes[0, 1].set_xlabel('Number of Observations', fontweight='bold')
    axes[0, 1].set_title('Top 20 Entities by Number of Observations', fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3, axis='x')
    
    # Entities per country
    top_countries = country_entities.head(15)
    axes[1, 0].barh(range(len(top_countries)), top_countries.values, color='orange', alpha=0.7, edgecolor='black')
    axes[1, 0].set_yticks(range(len(top_countries)))
    axes[1, 0].set_yticklabels(top_countries.index)
    axes[1, 0].set_xlabel('Number of Entities (Industries)', fontweight='bold')
    axes[1, 0].set_title('Number of Entities per Country', fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3, axis='x')
    
    # Year coverage by entity (heatmap sample)
    # Sample entities for visualization
    sample_entities = entity_counts.head(30).index
    sample_data = df_reset[df_reset['entity'].isin(sample_entities)]
    
    # Create pivot table
    pivot_data = sample_data.pivot_table(
        index='entity', 
        columns='year', 
        values='ln_emp', 
        aggfunc='count'
    ).fillna(0)
    
    # Create heatmap
    im = axes[1, 1].imshow(pivot_data.values, cmap='YlOrRd', aspect='auto')
    axes[1, 1].set_xticks(range(len(pivot_data.columns)))
    axes[1, 1].set_xticklabels(pivot_data.columns, rotation=45, ha='right')
    axes[1, 1].set_yticks(range(len(pivot_data.index)))
    axes[1, 1].set_yticklabels([e[:15] + '...' if len(e) > 15 else e for e in pivot_data.index], fontsize=7)
    axes[1, 1].set_xlabel('Year', fontweight='bold')
    axes[1, 1].set_ylabel('Entity', fontweight='bold')
    axes[1, 1].set_title('Data Availability Heatmap (Top 30 Entities)', fontweight='bold')
    plt.colorbar(im, ax=axes[1, 1], label='Observations')
    
    plt.tight_layout()
    plt.savefig(output_dir / '07_panel_structure.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info("Saved: 07_panel_structure.png")


def main():
    """Main function to generate all visualizations"""
    logger.info("="*80)
    logger.info("Starting visualization generation")
    logger.info("="*80)
    
    # Load data
    df = load_and_prepare_data()
    logger.info(f"Loaded dataset with {len(df)} observations")
    
    # Run regression to get results (similar to mainv2.py)
    logger.info("Running regression to get coefficients...")
    from linearmodels.panel import PanelOLS
    
    # Prepare for regression
    df_reg = df.copy()
    df_reg["entity"] = df_reg["country"] + "_" + df_reg["industry"]
    df_reg = df_reg.set_index(["entity", "year"])
    
    exog_vars = ["ln_emp_lag1", "ict_share_mc", "adjcov_lag1_mc", "coord_lag1_mc", 
                 "ict_x_adjcov", "ict_x_coord", "ln_va", "ln_wage"]
    
    regression_df = df_reg[exog_vars + ["ln_emp"]].copy()
    regression_df = regression_df.dropna()
    
    # Run LSDV regression
    mod_lsdv = PanelOLS(
        regression_df["ln_emp"],
        regression_df[exog_vars],
        entity_effects=True,
        time_effects=True
    )
    
    res_lsdv = mod_lsdv.fit(cov_type="clustered", cluster_entity=True)
    
    # Calculate LSDVC coefficients
    coef_lsdv = res_lsdv.params
    se_lsdv = res_lsdv.std_errors
    T = regression_df.index.get_level_values(1).nunique()
    alpha_lsdv = coef_lsdv["ln_emp_lag1"]
    bias_correction = -(1 + alpha_lsdv) / (T - 1)
    alpha_lsdvc = alpha_lsdv - bias_correction
    
    coef_lsdvc = coef_lsdv.copy()
    coef_lsdvc["ln_emp_lag1"] = alpha_lsdvc
    
    logger.info("Regression completed")
    
    # Reset index for plotting
    df_plot = df.copy()
    
    # Generate all visualizations
    plot_regression_coefficients(res_lsdv, coef_lsdvc, se_lsdv, output_dir)
    plot_data_overview(df_plot, output_dir)
    plot_time_series(df_plot, output_dir)
    plot_country_comparison(df_plot, output_dir)
    plot_industry_comparison(df_plot, output_dir)
    plot_relationships(df_plot, output_dir)
    plot_panel_structure(df_plot, output_dir)
    
    logger.info("="*80)
    logger.info("All visualizations generated successfully!")
    logger.info(f"Output directory: {output_dir.absolute()}")
    logger.info("="*80)


if __name__ == "__main__":
    main()
