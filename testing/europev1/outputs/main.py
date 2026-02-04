"""
ICT, Labour Market Institutions, and Job Polarization in Europe
================================================================

Research Question:
Do coordinated wage-bargaining institutions mitigate job polarization and 
routine-task displacement induced by ICT-driven technological change?

Model:
Outcome_{i,o,c,t} = β₁·ICT_{s,c,t-1} + β₂·Institution_{c,t} + β₃·(ICT × Institution) + FE + Controls + ε

Data Sources:
- EU-LFS: Labour-market outcomes (micro) - occupation, education, industry, country, year
- ICTWSS: Institutional moderators - bargaining coverage, coordination, union density
- EU KLEMS: ICT capital services / investment share by country × industry × year

Outcome Variables:
- Routine employment share
- Middle-skill employment share  
- Job polarization index (high-skill + low-skill − middle-skill)
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import time
from loguru import logger

# Configure loguru
logger.remove()  # Remove default handler
logger.add(
    lambda msg: print(msg, end=""),
    format="<level>{message}</level>",
    colorize=True,
    level="INFO"
)

# =============================================================================
# Configuration
# =============================================================================
BASE_DIR = Path(__file__).parent.parent  # europev1/
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = Path(__file__).parent  # europev1/outputs/

# Data subdirectories (create structure for data loading)
EULFS_DIR = DATA_DIR / "eu_lfs"          # EU Labour Force Survey
ICTWSS_DIR = DATA_DIR / "ictwss"         # Institutional data
EUKLEMS_DIR = DATA_DIR / "eu_klems"      # ICT capital data

# Create directories if they don't exist
for dir_path in [DATA_DIR, EULFS_DIR, ICTWSS_DIR, EUKLEMS_DIR, OUTPUT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Set plot style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# =============================================================================
# Constants & Mappings
# =============================================================================

# ISCO-08 1-digit occupation labels
ISCO_LABELS = {
    1: "Managers",
    2: "Professionals", 
    3: "Technicians",
    4: "Clerical workers",
    5: "Service/sales",
    6: "Agricultural",
    7: "Craft workers",
    8: "Machine operators",
    9: "Elementary"
}

# Routine Task Intensity (RTI) classification by ISCO-08 1-digit
# Based on Autor & Dorn (2013) task framework
ROUTINE_CLASSIFICATION = {
    1: "non_routine_cognitive",   # Managers
    2: "non_routine_cognitive",   # Professionals
    3: "non_routine_cognitive",   # Technicians
    4: "routine_cognitive",       # Clerical workers
    5: "non_routine_manual",      # Service/sales
    6: "routine_manual",          # Agricultural
    7: "routine_manual",          # Craft workers
    8: "routine_manual",          # Machine operators
    9: "non_routine_manual"       # Elementary
}

# Skill level classification by ISCO-08 1-digit
SKILL_CLASSIFICATION = {
    1: "high",    # Managers
    2: "high",    # Professionals
    3: "high",    # Technicians (sometimes middle)
    4: "middle",  # Clerical workers
    5: "middle",  # Service/sales (sometimes low)
    6: "middle",  # Agricultural
    7: "middle",  # Craft workers
    8: "middle",  # Machine operators
    9: "low"      # Elementary
}

# European countries typically covered in EU-LFS
EU_COUNTRIES = [
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES",
    "FI", "FR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
    "NL", "PL", "PT", "RO", "SE", "SI", "SK", "UK"
]

# =============================================================================
# Step 1: Load EU-LFS Data
# =============================================================================
def load_eulfs_data():
    """
    Load EU Labour Force Survey data.
    
    Expected format: Person-level microdata with columns:
    - country: ISO 2-letter country code
    - year: Survey year
    - isco: ISCO-08 occupation code (1-4 digit)
    - nace: NACE industry code
    - isced: Education level (ISCED)
    - weight: Survey weight
    - employed: Employment indicator
    
    NOTE: You need to obtain EU-LFS microdata from Eurostat.
    Place files in: europev1/data/eu_lfs/
    """
    logger.info("\n📂 Loading EU-LFS data...")
    
    # Check if data directory has files
    lfs_files = list(EULFS_DIR.glob("*.csv")) + list(EULFS_DIR.glob("*.dta"))
    
    if not lfs_files:
        logger.warning(f"\n⚠️  No EU-LFS files found in {EULFS_DIR}")
        logger.info("   Please add EU-LFS microdata files to this directory.")
        logger.info("   Expected format: CSV or Stata files with person-level data.")
        return _create_placeholder_eulfs()
    
    # Load all files
    all_data = []
    for file in tqdm(lfs_files, desc="Loading EU-LFS files", unit="file"):
        if file.suffix == ".csv":
            df = pd.read_csv(file)
        elif file.suffix == ".dta":
            df = pd.read_stata(file)
        all_data.append(df)
    
    combined = pd.concat(all_data, ignore_index=True)
    logger.success(f"✅ Loaded {len(combined):,} observations from EU-LFS")
    
    return combined


def _create_placeholder_eulfs():
    """Create placeholder EU-LFS data structure for testing."""
    logger.info("   Creating placeholder data structure...")
    
    # Generate sample structure
    placeholder = pd.DataFrame({
        "country": [],
        "year": [],
        "isco_1digit": [],
        "nace_section": [],
        "isced": [],
        "weight": [],
        "employed": []
    })
    
    return placeholder


# =============================================================================
# Step 2: Load ICTWSS Institutional Data
# =============================================================================
def load_ictwss_data():
    """
    Load OECD/AIAS ICTWSS institutional database.
    
    Key variables:
    - country: ISO country code
    - year: Year
    - coord: Bargaining coordination (1-5 scale)
    - covau: Adjusted collective bargaining coverage (%)
    - level: Predominant bargaining level (1=company, 2=sector, 3=national)
    - ud: Union density (%)
    
    NOTE: Download ICTWSS from https://www.ictwss.org/
    Place files in: europev1/data/ictwss/
    """
    logger.info("\n📂 Loading ICTWSS institutional data...")
    
    ictwss_files = list(ICTWSS_DIR.glob("*.csv")) + list(ICTWSS_DIR.glob("*.xlsx"))
    
    if not ictwss_files:
        logger.warning(f"\n⚠️  No ICTWSS files found in {ICTWSS_DIR}")
        logger.info("   Please download ICTWSS database from https://www.ictwss.org/")
        return _create_placeholder_ictwss()
    
    # Load first file found
    file = ictwss_files[0]
    if file.suffix == ".csv":
        df = pd.read_csv(file)
    elif file.suffix == ".xlsx":
        df = pd.read_excel(file)
    
    logger.success(f"✅ Loaded ICTWSS data: {len(df):,} country-year observations")
    
    return df


def _create_placeholder_ictwss():
    """Create placeholder ICTWSS data structure."""
    logger.info("   Creating placeholder data structure...")
    
    placeholder = pd.DataFrame({
        "country": [],
        "year": [],
        "coord": [],          # Bargaining coordination
        "covau": [],          # Collective bargaining coverage
        "level": [],          # Bargaining level
        "ud": []              # Union density
    })
    
    return placeholder


# =============================================================================
# Step 3: Load EU KLEMS ICT Data
# =============================================================================
def load_euklems_data():
    """
    Load EU KLEMS capital and productivity data.
    
    Key variables:
    - country: ISO country code
    - year: Year
    - industry: NACE industry code
    - ict_capital: ICT capital services index
    - ict_investment_share: ICT investment as % of total investment
    - ict_capital_share: ICT capital as % of total capital
    
    NOTE: Download EU KLEMS from https://euklems.eu/
    Place files in: europev1/data/eu_klems/
    """
    logger.info("\n📂 Loading EU KLEMS ICT data...")
    
    klems_files = list(EUKLEMS_DIR.glob("*.csv")) + list(EUKLEMS_DIR.glob("*.xlsx"))
    
    if not klems_files:
        logger.warning(f"\n⚠️  No EU KLEMS files found in {EUKLEMS_DIR}")
        logger.info("   Please download EU KLEMS from https://euklems.eu/")
        return _create_placeholder_euklems()
    
    # Load first file found
    file = klems_files[0]
    if file.suffix == ".csv":
        df = pd.read_csv(file)
    elif file.suffix == ".xlsx":
        df = pd.read_excel(file)
    
    logger.success(f"✅ Loaded EU KLEMS data: {len(df):,} industry-country-year observations")
    
    return df


def _create_placeholder_euklems():
    """Create placeholder EU KLEMS data structure."""
    logger.info("   Creating placeholder data structure...")
    
    placeholder = pd.DataFrame({
        "country": [],
        "year": [],
        "nace_section": [],
        "ict_capital_services": [],
        "ict_investment_share": [],
        "total_hours": []
    })
    
    return placeholder


# =============================================================================
# Step 4: Construct Analysis Variables
# =============================================================================
def construct_employment_shares(eulfs_df):
    """
    Construct outcome variables from EU-LFS data:
    - Routine employment share
    - Middle-skill employment share
    - Job polarization index
    
    Aggregated at country × year level (or country × industry × year).
    """
    logger.info("\n📊 Constructing employment shares...")
    
    if eulfs_df.empty:
        logger.warning("   EU-LFS data is empty. Skipping construction.")
        return pd.DataFrame()
    
    df = eulfs_df.copy()
    
    # Add routine/skill classifications
    df["routine_type"] = df["isco_1digit"].map(ROUTINE_CLASSIFICATION)
    df["skill_level"] = df["isco_1digit"].map(SKILL_CLASSIFICATION)
    
    # Create routine indicator
    df["is_routine"] = df["routine_type"].isin(["routine_cognitive", "routine_manual"]).astype(int)
    
    # Aggregate by country-year
    # TODO: Consider country × industry × year aggregation
    agg_df = df.groupby(["country", "year"]).apply(
        lambda x: pd.Series({
            "routine_share": np.average(x["is_routine"], weights=x["weight"]) if "weight" in x.columns else x["is_routine"].mean(),
            "high_skill_share": np.average(x["skill_level"] == "high", weights=x.get("weight", 1)),
            "middle_skill_share": np.average(x["skill_level"] == "middle", weights=x.get("weight", 1)),
            "low_skill_share": np.average(x["skill_level"] == "low", weights=x.get("weight", 1)),
            "n_obs": len(x)
        })
    ).reset_index()
    
    # Job polarization index: high + low - middle
    agg_df["polarization_index"] = agg_df["high_skill_share"] + agg_df["low_skill_share"] - agg_df["middle_skill_share"]
    
    logger.success(f"✅ Constructed employment shares for {len(agg_df)} country-year cells")
    
    return agg_df


def construct_ict_exposure(klems_df, eulfs_df):
    """
    Construct ICT exposure variable.
    
    Options:
    1. Country-level: Average ICT intensity across industries
    2. Industry-weighted: ICT intensity weighted by industry employment shares
    3. Worker-level: Assign industry's ICT intensity to each worker
    """
    logger.info("\n📊 Constructing ICT exposure variable...")
    
    if klems_df.empty:
        logger.warning("   EU KLEMS data is empty. Skipping construction.")
        return pd.DataFrame()
    
    # Option 1: Simple country-year average
    ict_by_country = klems_df.groupby(["country", "year"]).agg({
        "ict_capital_services": "mean",
        "ict_investment_share": "mean"
    }).reset_index()
    
    # Lag ICT by 1 year (ICT_{t-1})
    ict_by_country["year"] = ict_by_country["year"] + 1
    ict_by_country = ict_by_country.rename(columns={
        "ict_capital_services": "ict_capital_lag",
        "ict_investment_share": "ict_invest_lag"
    })
    
    logger.success(f"✅ Constructed ICT exposure for {len(ict_by_country)} country-year cells")
    
    return ict_by_country


# =============================================================================
# Step 5: Merge All Data Sources
# =============================================================================
def merge_datasets(employment_df, ictwss_df, ict_df):
    """
    Merge all datasets on country × year.
    """
    logger.info("\n🔗 Merging datasets...")
    
    if employment_df.empty:
        logger.warning("   Employment data is empty. Cannot merge.")
        return pd.DataFrame()
    
    merged = employment_df.copy()
    
    # Merge institutions
    if not ictwss_df.empty:
        merged = merged.merge(
            ictwss_df[["country", "year", "coord", "covau", "level", "ud"]],
            on=["country", "year"],
            how="left"
        )
        logger.info(f"   Merged ICTWSS: {merged['coord'].notna().sum()} matched observations")
    
    # Merge ICT exposure
    if not ict_df.empty:
        merged = merged.merge(
            ict_df,
            on=["country", "year"],
            how="left"
        )
        logger.info(f"   Merged EU KLEMS: {merged['ict_capital_lag'].notna().sum()} matched observations")
    
    logger.success(f"✅ Final merged dataset: {len(merged)} observations")
    
    return merged


# =============================================================================
# Step 6: Run Regression Analysis
# =============================================================================
def run_baseline_regression(df, outcome_var="routine_share"):
    """
    Run baseline regression:
    Outcome = β₁·ICT + β₂·Institution + β₃·(ICT × Institution) + FE + ε
    """
    logger.info(f"\n📈 Running regression for: {outcome_var}")
    
    if df.empty:
        logger.warning("   Data is empty. Cannot run regression.")
        return None
    
    # Prepare variables
    required_cols = [outcome_var, "ict_capital_lag", "coord"]
    if not all(col in df.columns for col in required_cols):
        logger.warning(f"   Missing columns. Required: {required_cols}")
        return None
    
    # Drop missing values
    reg_df = df.dropna(subset=required_cols)
    
    if len(reg_df) < 10:
        logger.warning(f"   Insufficient observations: {len(reg_df)}")
        return None
    
    # Create interaction term
    reg_df["ict_x_coord"] = reg_df["ict_capital_lag"] * reg_df["coord"]
    
    # Prepare regression
    X = reg_df[["ict_capital_lag", "coord", "ict_x_coord"]]
    X = sm.add_constant(X)
    y = reg_df[outcome_var]
    
    # Add country fixed effects (dummies)
    # country_dummies = pd.get_dummies(reg_df["country"], prefix="fe", drop_first=True)
    # X = pd.concat([X, country_dummies], axis=1)
    
    # Run OLS
    model = sm.OLS(y, X)
    results = model.fit(cov_type='HC1')  # Heteroskedasticity-robust SEs
    
    logger.success("✅ Regression complete")
    
    return results


# =============================================================================
# Step 7: Create Visualizations
# =============================================================================
def create_visualizations(df, results=None):
    """Create exploratory and results visualizations."""
    
    logger.info("\n🎨 Creating visualizations...")
    
    if df.empty:
        logger.warning("   Data is empty. Skipping visualizations.")
        return
    
    with tqdm(total=3, desc="Generating charts", unit="chart") as pbar:
        
        # Chart 1: Employment shares over time by country
        if "routine_share" in df.columns and "year" in df.columns:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            for country in df["country"].unique()[:10]:  # Limit to 10 countries
                country_data = df[df["country"] == country]
                ax.plot(country_data["year"], country_data["routine_share"], 
                       marker="o", label=country, alpha=0.7)
            
            ax.set_xlabel("Year", fontsize=12)
            ax.set_ylabel("Routine Employment Share", fontsize=12)
            ax.set_title("Routine Employment Share Over Time by Country", fontsize=14)
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            plt.tight_layout()
            plt.savefig(OUTPUT_DIR / "routine_share_trends.png", dpi=300, bbox_inches="tight")
            plt.close()
        pbar.update(1)
        
        # Chart 2: ICT vs Routine Share scatter
        if all(col in df.columns for col in ["ict_capital_lag", "routine_share"]):
            fig, ax = plt.subplots(figsize=(10, 8))
            
            scatter = ax.scatter(
                df["ict_capital_lag"], 
                df["routine_share"],
                c=df["coord"] if "coord" in df.columns else "blue",
                cmap="viridis",
                alpha=0.6,
                s=50
            )
            
            if "coord" in df.columns:
                plt.colorbar(scatter, label="Bargaining Coordination")
            
            ax.set_xlabel("ICT Capital (lagged)", fontsize=12)
            ax.set_ylabel("Routine Employment Share", fontsize=12)
            ax.set_title("ICT Exposure vs Routine Employment", fontsize=14)
            
            plt.tight_layout()
            plt.savefig(OUTPUT_DIR / "ict_vs_routine.png", dpi=300, bbox_inches="tight")
            plt.close()
        pbar.update(1)
        
        # Chart 3: Polarization index by coordination level
        if all(col in df.columns for col in ["coord", "polarization_index"]):
            fig, ax = plt.subplots(figsize=(10, 6))
            
            coord_means = df.groupby("coord")["polarization_index"].mean()
            coord_means.plot(kind="bar", ax=ax, color=plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(coord_means))))
            
            ax.set_xlabel("Bargaining Coordination Level", fontsize=12)
            ax.set_ylabel("Mean Polarization Index", fontsize=12)
            ax.set_title("Job Polarization by Institutional Coordination", fontsize=14)
            ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
            
            plt.tight_layout()
            plt.savefig(OUTPUT_DIR / "polarization_by_coord.png", dpi=300, bbox_inches="tight")
            plt.close()
        pbar.update(1)
    
    logger.success(f"✅ Charts saved to: {OUTPUT_DIR}")


# =============================================================================
# Step 8: Create Output Tables
# =============================================================================
def create_output_tables(df, results=None):
    """Create and save summary tables."""
    
    logger.info("\n📋 Creating output tables...")
    
    if df.empty:
        logger.warning("   Data is empty. Skipping tables.")
        return
    
    # Table 1: Summary statistics
    if len(df.columns) > 2:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        summary_stats = df[numeric_cols].describe().T
        summary_stats.to_csv(OUTPUT_DIR / "summary_statistics.csv")
        logger.info(f"   Saved: summary_statistics.csv")
    
    # Table 2: Country-level means
    if "country" in df.columns:
        country_means = df.groupby("country").mean(numeric_only=True)
        country_means.to_csv(OUTPUT_DIR / "country_means.csv")
        logger.info(f"   Saved: country_means.csv")
    
    # Table 3: Regression results
    if results is not None:
        reg_summary = pd.DataFrame({
            "Variable": results.params.index,
            "Coefficient": results.params.values,
            "Std Error": results.bse.values,
            "t-statistic": results.tvalues.values,
            "p-value": results.pvalues.values
        })
        reg_summary.to_csv(OUTPUT_DIR / "regression_results.csv", index=False)
        logger.info(f"   Saved: regression_results.csv")
    
    logger.success(f"✅ Tables saved to: {OUTPUT_DIR}")


# =============================================================================
# Main Execution
# =============================================================================
def main():
    """Main analysis pipeline."""
    
    logger.info("\n" + "="*70)
    logger.info("🇪🇺 ICT, INSTITUTIONS & JOB POLARIZATION IN EUROPE")
    logger.info("="*70)
    
    start_time = time.time()
    
    # Step 1: Load data sources
    logger.info("\n" + "-"*70)
    logger.info("STEP 1: Loading data sources")
    logger.info("-"*70)
    
    eulfs_df = load_eulfs_data()
    ictwss_df = load_ictwss_data()
    klems_df = load_euklems_data()
    
    # Step 2: Construct variables
    logger.info("\n" + "-"*70)
    logger.info("STEP 2: Constructing analysis variables")
    logger.info("-"*70)
    
    employment_df = construct_employment_shares(eulfs_df)
    ict_df = construct_ict_exposure(klems_df, eulfs_df)
    
    # Step 3: Merge datasets
    logger.info("\n" + "-"*70)
    logger.info("STEP 3: Merging datasets")
    logger.info("-"*70)
    
    merged_df = merge_datasets(employment_df, ictwss_df, ict_df)
    
    # Step 4: Run regressions
    logger.info("\n" + "-"*70)
    logger.info("STEP 4: Running regressions")
    logger.info("-"*70)
    
    results_routine = run_baseline_regression(merged_df, "routine_share")
    results_middle = run_baseline_regression(merged_df, "middle_skill_share")
    results_polar = run_baseline_regression(merged_df, "polarization_index")
    
    # Step 5: Create outputs
    logger.info("\n" + "-"*70)
    logger.info("STEP 5: Creating outputs")
    logger.info("-"*70)
    
    create_visualizations(merged_df, results_routine)
    create_output_tables(merged_df, results_routine)
    
    # Print results summary
    if results_routine is not None:
        logger.info("\n" + "="*70)
        logger.info("📈 REGRESSION RESULTS: Routine Employment Share")
        logger.info("="*70)
        logger.info(f"\n{results_routine.summary()}")
    
    # Execution time
    elapsed = time.time() - start_time
    logger.info(f"\n⏱️  Total execution time: {elapsed:.2f} seconds")
    
    logger.info("\n" + "="*70)
    logger.info("📁 NEXT STEPS")
    logger.info("="*70)
    logger.info("""
    1. Add EU-LFS microdata to: europev1/data/eu_lfs/
    2. Add ICTWSS data to: europev1/data/ictwss/
    3. Add EU KLEMS data to: europev1/data/eu_klems/
    4. Re-run this script once data is loaded
    """)
    
    logger.info("="*70)
    logger.success("✅ BOILERPLATE SETUP COMPLETE")
    logger.info("="*70)
    
    return merged_df, results_routine


if __name__ == "__main__":
    merged_df, results = main()
