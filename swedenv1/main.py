"""
Regression Analysis: Mean Income vs Automation Probability
===========================================================
Model: mean_income_i = β * automation_probability_i + ε_i

Data Sources:
- Income: EU-SILC microdata for Sweden (2004-2013)
- Automation: Frey & Osborne style automation probabilities

NOTE: The EU-SILC public use files only contain 1-digit ISCO occupation codes.
      You need to either:
      1. Aggregate your detailed automation probabilities to 1-digit ISCO, OR
      2. Obtain EU-SILC data with more detailed occupation codes
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
BASE_DIR = Path(__file__).parent
EUSILC_DIR = BASE_DIR / "data" / "wage" / "SE_PUF_EUSILC"
AUTOMATION_FILE = BASE_DIR / "data" / "automation_probability" / "automation_probability.csv"
OUTPUT_DIR = BASE_DIR / "outputs"

# Create outputs directory if it doesn't exist
OUTPUT_DIR.mkdir(exist_ok=True)

# Set plot style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# ISCO occupation labels
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

# =============================================================================
# Step 1: Load and Process EU-SILC Data
# =============================================================================
def load_eusilc_data():
    """
    Load all EU-SILC person-level files and extract occupation & income.
    
    Key variables:
    - PL050/PL051: ISCO occupation code (1-digit in public use files)
    - PY010G: Gross employee cash income
    - PB040: Personal cross-sectional weight
    """
    all_data = []
    
    # Find all person-level files (ending with 'p_EUSILC.csv')
    person_files = sorted(EUSILC_DIR.glob("SE_*p_EUSILC.csv"))
    
    logger.info(f"\n📂 Found {len(person_files)} EU-SILC person files")
    
    # Load files with progress bar
    for file in tqdm(person_files, desc="Loading EU-SILC files", unit="file"):
        year = file.name.split("_")[1][:4]
        df = pd.read_csv(file)
        
        # Determine occupation column (PL050 in older files, PL051 in newer)
        occ_col = "PL051" if "PL051" in df.columns else "PL050"
        
        # Select relevant columns
        cols_to_keep = {
            occ_col: "isco_1digit",
            "PY010G": "gross_income",
            "PB040": "weight"
        }
        
        available_cols = {k: v for k, v in cols_to_keep.items() if k in df.columns}
        df_subset = df[list(available_cols.keys())].rename(columns=available_cols)
        df_subset["year"] = int(year)
        
        all_data.append(df_subset)
    
    # Combine all data with progress indication
    logger.info("📊 Combining datasets...")
    combined = pd.concat(all_data, ignore_index=True)
    
    # Clean data with progress bar
    logger.info("🧹 Cleaning data...")
    with tqdm(total=4, desc="Data cleaning steps", unit="step") as pbar:
        # Step 1: Clean occupation codes
        combined["isco_1digit"] = combined["isco_1digit"].astype(str).str.strip()
        pbar.update(1)
        
        # Step 2: Replace special values
        combined["isco_1digit"] = combined["isco_1digit"].replace({"0 - 1": "1", "nan": np.nan})
        pbar.update(1)
        
        # Step 3: Filter valid occupation codes
        combined = combined[combined["isco_1digit"].isin(["1", "2", "3", "4", "5", "6", "7", "8", "9"])]
        combined["isco_1digit"] = combined["isco_1digit"].astype(int)
        pbar.update(1)
        
        # Step 4: Clean income
        combined["gross_income"] = pd.to_numeric(combined["gross_income"], errors="coerce")
        combined = combined[combined["gross_income"] > 0]
        pbar.update(1)
    
    return combined


def calculate_mean_income_by_occupation(df):
    """Calculate weighted mean income by 1-digit ISCO occupation."""
    
    logger.info("📈 Calculating mean income by occupation...")
    
    results = []
    for isco in tqdm(sorted(df["isco_1digit"].unique()), desc="Processing occupations", unit="occ"):
        group = df[df["isco_1digit"] == isco]
        
        # Weighted mean
        if "weight" in group.columns and group["weight"].notna().any():
            weights = group["weight"].fillna(1)
            mean_inc = np.average(group["gross_income"], weights=weights)
        else:
            mean_inc = group["gross_income"].mean()
        
        results.append({
            "isco_1digit": isco,
            "mean_income": mean_inc,
            "n_obs": len(group),
            "std_income": group["gross_income"].std(),
            "median_income": group["gross_income"].median()
        })
    
    return pd.DataFrame(results)


# =============================================================================
# Step 2: Load and Aggregate Automation Probabilities
# =============================================================================
def load_automation_probabilities():
    """
    Load automation probabilities and aggregate to 1-digit ISCO level.
    
    IMPORTANT: Your automation_probability.csv has codes 1-291 which appear to be
    detailed SOC codes. You need to provide a mapping to ISCO-08 1-digit codes.
    """
    auto_df = pd.read_csv(AUTOMATION_FILE)
    logger.info(f"\n📊 Automation data: {len(auto_df)} occupation codes")
    logger.info(f"   Code range: {auto_df['occupation_code'].min()} - {auto_df['occupation_code'].max()}")
    logger.info(f"   Probability range: {auto_df['automation_probability'].min():.3f} - {auto_df['automation_probability'].max():.3f}")
    
    # PLACEHOLDER MAPPING - REPLACE WITH ACTUAL SOC-TO-ISCO CROSSWALK
    isco_automation = pd.DataFrame({
        "isco_1digit": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "automation_probability": [
            0.015,  # 1 - Managers (low automation risk)
            0.040,  # 2 - Professionals (low risk)
            0.250,  # 3 - Technicians (moderate risk)
            0.700,  # 4 - Clerical workers (high risk)
            0.400,  # 5 - Service/sales (moderate risk)
            0.500,  # 6 - Agricultural workers (moderate-high risk)
            0.600,  # 7 - Craft workers (high risk)
            0.700,  # 8 - Machine operators (high risk)
            0.800,  # 9 - Elementary occupations (very high risk)
        ]
    })
    
    logger.warning("\n⚠️  WARNING: Using PLACEHOLDER automation probabilities!")
    logger.warning("   Please provide a proper SOC-to-ISCO crosswalk to aggregate your detailed data.")
    
    return isco_automation


# =============================================================================
# Step 3: Run Regression
# =============================================================================
def run_regression(merged_data):
    """
    Run OLS regression: mean_income = β₀ + β₁ * automation_probability + ε
    """
    # Prepare data
    X = merged_data["automation_probability"]
    X = sm.add_constant(X)
    y = merged_data["mean_income"]
    
    # Run OLS
    model = sm.OLS(y, X)
    results = model.fit()
    
    return results


# =============================================================================
# Step 4: Create Visualizations
# =============================================================================
def create_visualizations(merged_data, results):
    """Create and save all visualizations."""
    
    logger.info("\n🎨 Creating visualizations...")
    
    merged_data = merged_data.copy()
    merged_data["occupation_name"] = merged_data["isco_1digit"].map(ISCO_LABELS)
    
    with tqdm(total=4, desc="Generating charts", unit="chart") as pbar:
        
        # =====================================================================
        # Chart 1: Scatter plot with regression line
        # =====================================================================
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Scatter points
        scatter = ax.scatter(
            merged_data["automation_probability"], 
            merged_data["mean_income"],
            s=merged_data["n_obs"] / 50,  # Size by observation count
            c=merged_data["isco_1digit"],
            cmap="viridis",
            alpha=0.7,
            edgecolors="white",
            linewidth=2
        )
        
        # Regression line
        x_line = np.linspace(0, 1, 100)
        y_line = results.params["const"] + results.params["automation_probability"] * x_line
        ax.plot(x_line, y_line, 'r--', linewidth=2, label=f'Regression line (R² = {results.rsquared:.3f})')
        
        # Labels for each point
        for _, row in merged_data.iterrows():
            ax.annotate(
                row["occupation_name"],
                (row["automation_probability"], row["mean_income"]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=9,
                alpha=0.8
            )
        
        ax.set_xlabel("Automation Probability", fontsize=12)
        ax.set_ylabel("Mean Annual Income (€)", fontsize=12)
        ax.set_title("Automation Probability vs Mean Income by Occupation\nSweden EU-SILC Data (2004-2013)", fontsize=14)
        ax.legend(loc="upper right")
        ax.set_xlim(-0.05, 1.05)
        
        # Add equation annotation
        beta = results.params["automation_probability"]
        const = results.params["const"]
        pval = results.pvalues["automation_probability"]
        eq_text = f"Income = {const:,.0f} + ({beta:,.0f}) × AutoProb\np-value = {pval:.4f}"
        ax.text(0.02, 0.02, eq_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "regression_scatter.png", dpi=300, bbox_inches="tight")
        plt.close()
        pbar.update(1)
        
        # =====================================================================
        # Chart 2: Bar chart of income by occupation
        # =====================================================================
        fig, ax = plt.subplots(figsize=(12, 6))
        
        sorted_data = merged_data.sort_values("mean_income", ascending=True)
        colors = plt.cm.RdYlGn(1 - sorted_data["automation_probability"])
        
        bars = ax.barh(sorted_data["occupation_name"], sorted_data["mean_income"], color=colors, edgecolor="white")
        
        # Add value labels
        for bar, auto_prob in zip(bars, sorted_data["automation_probability"]):
            width = bar.get_width()
            ax.text(width + 500, bar.get_y() + bar.get_height()/2,
                   f'€{width:,.0f}', va='center', fontsize=10)
            ax.text(1000, bar.get_y() + bar.get_height()/2,
                   f'Auto: {auto_prob:.0%}', va='center', fontsize=9, color='white', fontweight='bold')
        
        ax.set_xlabel("Mean Annual Income (€)", fontsize=12)
        ax.set_title("Mean Income by Occupation (colored by automation risk)\nGreen = Low Risk, Red = High Risk", fontsize=14)
        ax.set_xlim(0, max(sorted_data["mean_income"]) * 1.15)
        
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "income_by_occupation.png", dpi=300, bbox_inches="tight")
        plt.close()
        pbar.update(1)
        
        # =====================================================================
        # Chart 3: Automation probability distribution
        # =====================================================================
        fig, ax = plt.subplots(figsize=(10, 6))
        
        sorted_data = merged_data.sort_values("automation_probability", ascending=True)
        colors = plt.cm.RdYlGn_r(sorted_data["automation_probability"])
        
        bars = ax.barh(sorted_data["occupation_name"], sorted_data["automation_probability"], 
                      color=colors, edgecolor="white")
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.02, bar.get_y() + bar.get_height()/2,
                   f'{width:.0%}', va='center', fontsize=10)
        
        ax.set_xlabel("Automation Probability", fontsize=12)
        ax.set_title("Automation Probability by Occupation\n(Placeholder Data)", fontsize=14)
        ax.set_xlim(0, 1.1)
        ax.axvline(x=0.5, color='gray', linestyle='--', alpha=0.5, label='50% threshold')
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "automation_by_occupation.png", dpi=300, bbox_inches="tight")
        plt.close()
        pbar.update(1)
        
        # =====================================================================
        # Chart 4: Combined summary figure
        # =====================================================================
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        
        # Subplot 1: Scatter with regression
        ax1 = axes[0, 0]
        ax1.scatter(merged_data["automation_probability"], merged_data["mean_income"],
                   s=100, c=merged_data["isco_1digit"], cmap="viridis", alpha=0.7, edgecolors="white")
        x_line = np.linspace(0, 1, 100)
        y_line = results.params["const"] + results.params["automation_probability"] * x_line
        ax1.plot(x_line, y_line, 'r--', linewidth=2)
        ax1.set_xlabel("Automation Probability")
        ax1.set_ylabel("Mean Income (€)")
        ax1.set_title(f"Regression (R² = {results.rsquared:.3f})")
        
        # Subplot 2: Income bar chart
        ax2 = axes[0, 1]
        sorted_by_income = merged_data.sort_values("mean_income", ascending=True)
        ax2.barh(sorted_by_income["occupation_name"], sorted_by_income["mean_income"], 
                color=plt.cm.Blues(np.linspace(0.3, 0.9, len(sorted_by_income))))
        ax2.set_xlabel("Mean Income (€)")
        ax2.set_title("Income by Occupation")
        
        # Subplot 3: Automation bar chart
        ax3 = axes[1, 0]
        sorted_by_auto = merged_data.sort_values("automation_probability", ascending=True)
        colors = plt.cm.RdYlGn_r(sorted_by_auto["automation_probability"])
        ax3.barh(sorted_by_auto["occupation_name"], sorted_by_auto["automation_probability"], color=colors)
        ax3.set_xlabel("Automation Probability")
        ax3.set_title("Automation Risk by Occupation")
        ax3.set_xlim(0, 1)
        
        # Subplot 4: Sample sizes
        ax4 = axes[1, 1]
        sorted_by_n = merged_data.sort_values("n_obs", ascending=True)
        ax4.barh(sorted_by_n["occupation_name"], sorted_by_n["n_obs"], 
                color=plt.cm.Greens(np.linspace(0.3, 0.9, len(sorted_by_n))))
        ax4.set_xlabel("Number of Observations")
        ax4.set_title("Sample Size by Occupation")
        
        plt.suptitle("Automation Probability vs Income Analysis\nSweden EU-SILC Data", fontsize=16, y=1.02)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "summary_figure.png", dpi=300, bbox_inches="tight")
        plt.close()
        pbar.update(1)
    
    logger.success(f"✅ Charts saved to: {OUTPUT_DIR}")


# =============================================================================
# Step 5: Create Output Tables
# =============================================================================
def create_output_tables(merged_data, results, eusilc_data):
    """Create and save summary tables."""
    
    logger.info("\n📋 Creating output tables...")
    
    merged_data = merged_data.copy()
    merged_data["occupation_name"] = merged_data["isco_1digit"].map(ISCO_LABELS)
    
    with tqdm(total=3, desc="Generating tables", unit="table") as pbar:
        
        # Table 1: Summary statistics by occupation
        summary_table = merged_data[[
            "isco_1digit", "occupation_name", "mean_income", "median_income",
            "std_income", "automation_probability", "n_obs"
        ]].copy()
        summary_table["mean_income"] = summary_table["mean_income"].round(0).astype(int)
        summary_table["median_income"] = summary_table["median_income"].round(0).astype(int)
        summary_table["std_income"] = summary_table["std_income"].round(0).astype(int)
        summary_table = summary_table.sort_values("isco_1digit")
        summary_table.to_csv(OUTPUT_DIR / "summary_by_occupation.csv", index=False)
        pbar.update(1)
        
        # Table 2: Regression results
        reg_summary = pd.DataFrame({
            "Variable": ["Constant (β₀)", "Automation Probability (β₁)"],
            "Coefficient": [results.params["const"], results.params["automation_probability"]],
            "Std Error": [results.bse["const"], results.bse["automation_probability"]],
            "t-statistic": [results.tvalues["const"], results.tvalues["automation_probability"]],
            "p-value": [results.pvalues["const"], results.pvalues["automation_probability"]],
            "95% CI Lower": [results.conf_int().loc["const", 0], results.conf_int().loc["automation_probability", 0]],
            "95% CI Upper": [results.conf_int().loc["const", 1], results.conf_int().loc["automation_probability", 1]]
        })
        
        # Add model statistics
        model_stats = pd.DataFrame({
            "Statistic": ["R-squared", "Adj. R-squared", "F-statistic", "Prob(F-statistic)", 
                         "N observations", "Degrees of freedom"],
            "Value": [results.rsquared, results.rsquared_adj, results.fvalue, results.f_pvalue,
                     results.nobs, results.df_resid]
        })
        
        reg_summary.to_csv(OUTPUT_DIR / "regression_coefficients.csv", index=False)
        model_stats.to_csv(OUTPUT_DIR / "regression_statistics.csv", index=False)
        pbar.update(1)
        
        # Table 3: Year-by-year statistics
        yearly_stats = eusilc_data.groupby("year").agg({
            "gross_income": ["mean", "median", "std", "count"]
        }).round(0)
        yearly_stats.columns = ["mean_income", "median_income", "std_income", "n_obs"]
        yearly_stats = yearly_stats.reset_index()
        yearly_stats.to_csv(OUTPUT_DIR / "yearly_statistics.csv", index=False)
        pbar.update(1)
    
    logger.success(f"✅ Tables saved to: {OUTPUT_DIR}")
    
    return summary_table, reg_summary, model_stats


def print_results_summary(merged_data, results, summary_table):
    """Print formatted results to console."""
    
    logger.info("\n" + "="*70)
    logger.info("📊 DATA SUMMARY BY OCCUPATION")
    logger.info("="*70)
    logger.info(summary_table.to_string(index=False))
    
    logger.info("\n" + "="*70)
    logger.info("📈 REGRESSION RESULTS")
    logger.info("="*70)
    logger.info(f"\nModel: mean_income_i = β₀ + β₁ × automation_probability_i + ε_i")
    logger.info(f"Observations: {len(merged_data)} occupation groups")
    logger.info("\n" + str(results.summary()))
    
    logger.info("\n" + "="*70)
    logger.info("💡 INTERPRETATION")
    logger.info("="*70)
    
    beta = results.params["automation_probability"]
    const = results.params["const"]
    pval = results.pvalues["automation_probability"]
    r2 = results.rsquared
    
    logger.info(f"\n• Intercept (β₀): €{const:,.0f}")
    logger.info(f"  → Expected income when automation probability = 0")
    
    logger.info(f"\n• Coefficient (β₁): €{beta:,.0f}")
    logger.info(f"  → A 10 percentage point increase in automation probability")
    logger.info(f"    is associated with a €{beta*0.1:,.0f} change in mean income")
    
    logger.info(f"\n• P-value: {pval:.4f}")
    if pval < 0.01:
        logger.info("  → Statistically significant at 1% level ✓✓✓")
    elif pval < 0.05:
        logger.info("  → Statistically significant at 5% level ✓✓")
    elif pval < 0.10:
        logger.info("  → Statistically significant at 10% level ✓")
    else:
        logger.info("  → NOT statistically significant at 10% level ✗")
    
    logger.info(f"\n• R-squared: {r2:.3f}")
    logger.info(f"  → Automation probability explains {r2*100:.1f}% of income variation")
    
    logger.info("\n" + "="*70)
    logger.warning("⚠️  IMPORTANT CAVEATS")
    logger.info("="*70)
    logger.info("""
1. This analysis uses PLACEHOLDER automation probabilities.
   You need to provide actual SOC-to-ISCO mapping for your data.

2. Only 9 data points (1-digit ISCO groups) - very limited statistical power.
   Consider obtaining EU-SILC data with 2-4 digit occupation codes.

3. Cross-sectional analysis - cannot establish causality.

4. Income is gross employee cash income only (excludes self-employment, benefits).
""")


# =============================================================================
# Main Execution
# =============================================================================
if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("🤖 AUTOMATION PROBABILITY VS INCOME REGRESSION")
    logger.info("   Sweden EU-SILC Data (2004-2013)")
    logger.info("="*70)
    
    start_time = time.time()
    
    # Step 1: Load EU-SILC data
    logger.info("\n" + "-"*70)
    logger.info("STEP 1: Loading EU-SILC microdata")
    logger.info("-"*70)
    eusilc_data = load_eusilc_data()
    logger.success(f"\n✅ Total observations after cleaning: {len(eusilc_data):,}")
    
    # Step 2: Calculate mean income by occupation
    logger.info("\n" + "-"*70)
    logger.info("STEP 2: Calculating mean income by occupation")
    logger.info("-"*70)
    mean_income_df = calculate_mean_income_by_occupation(eusilc_data)
    
    # Step 3: Load automation probabilities
    logger.info("\n" + "-"*70)
    logger.info("STEP 3: Loading automation probabilities")
    logger.info("-"*70)
    automation_df = load_automation_probabilities()
    
    # Step 4: Merge datasets
    logger.info("\n" + "-"*70)
    logger.info("STEP 4: Merging datasets")
    logger.info("-"*70)
    merged = mean_income_df.merge(automation_df, on="isco_1digit", how="inner")
    logger.success(f"✅ Merged dataset: {len(merged)} occupation groups")
    
    # Step 5: Run regression
    logger.info("\n" + "-"*70)
    logger.info("STEP 5: Running regression")
    logger.info("-"*70)
    results = run_regression(merged)
    logger.success("✅ Regression complete")
    
    # Step 6: Create visualizations
    logger.info("\n" + "-"*70)
    logger.info("STEP 6: Creating visualizations")
    logger.info("-"*70)
    create_visualizations(merged, results)
    
    # Step 7: Create output tables
    logger.info("\n" + "-"*70)
    logger.info("STEP 7: Creating output tables")
    logger.info("-"*70)
    summary_table, reg_summary, model_stats = create_output_tables(merged, results, eusilc_data)
    
    # Print summary
    print_results_summary(merged, results, summary_table)
    
    # Execution time
    elapsed = time.time() - start_time
    logger.info(f"\n⏱️  Total execution time: {elapsed:.2f} seconds")
    
    logger.info("\n" + "="*70)
    logger.info("📁 OUTPUT FILES")
    logger.info("="*70)
    logger.info(f"""
Charts:
  • {OUTPUT_DIR}/regression_scatter.png
  • {OUTPUT_DIR}/income_by_occupation.png
  • {OUTPUT_DIR}/automation_by_occupation.png
  • {OUTPUT_DIR}/summary_figure.png

Tables:
  • {OUTPUT_DIR}/summary_by_occupation.csv
  • {OUTPUT_DIR}/regression_coefficients.csv
  • {OUTPUT_DIR}/regression_statistics.csv
  • {OUTPUT_DIR}/yearly_statistics.csv
""")
    logger.info("="*70)
    logger.success("✅ ANALYSIS COMPLETE")
    logger.info("="*70)
