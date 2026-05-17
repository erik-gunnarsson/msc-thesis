'''
Scatter plot of coordination index vs adjusted collective bargaining coverage

This scatter plot shows the relationship between the coordination index and the adjusted
collective bargaining coverage, demonstrating the empirical orthogonality of these two
institutional dimensions.

AdjCov = Adjusted collective bargaining coverage (ICTWSS)
Coord = Wage coordination index from ICTWSS (1=fragmented, 5=centralized/coordinated)

Classification thresholds:
  Coverage: High ≥60%, Medium 30-59%, Low <30%
  Coordination: High ≥4, Medium 2-3.5, Low <2

Means are computed over all available years per country (no fixed year range).
'''

import pandas as pd
import matplotlib.pyplot as plt
from loguru import logger

# Set style for publication-quality figure
plt.style.use('seaborn-v0_8-paper')

# ISO2 (2-letter) country code -> full name (matches cleaned_data which uses EU_ISO2)
COUNTRY_NAMES = {
    "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "CY": "Cyprus",
    "CZ": "Czechia", "DE": "Germany", "DK": "Denmark", "EE": "Estonia",
    "EL": "Greece", "ES": "Spain", "FI": "Finland", "FR": "France",
    "GR": "Greece", "HR": "Croatia", "HU": "Hungary", "IE": "Ireland",
    "IT": "Italy", "LT": "Lithuania", "LU": "Luxembourg", "LV": "Latvia",
    "MT": "Malta", "NL": "Netherlands", "PL": "Poland", "PT": "Portugal",
    "RO": "Romania", "SE": "Sweden", "SI": "Slovenia", "SK": "Slovakia",
    "UK": "UK",
}

# Load the data
df = pd.read_csv("../data/cleaned_data.csv")
logger.info(f"Loaded {len(df)} rows from data/cleaned_data.csv")

# Collapse to country-year (adjcov and coord are country-level, same across industries)
df_cy = df.groupby(["country_code", "year"]).agg(
    coord=("coord", "first"),
    adjcov=("adjcov", "first"),
).reset_index()

# For each country: compute mean over available years (any combination of years)
def agg_country(g):
    valid = g.dropna(subset=["coord", "adjcov"])
    n_years = len(valid)
    if n_years == 0:
        return pd.Series({"coord": None, "adjcov": None, "n_years": 0, "years": ""})
    return pd.Series({
        "coord": valid["coord"].mean(),
        "adjcov": valid["adjcov"].mean(),
        "n_years": n_years,
        "years": ",".join(map(str, sorted(valid["year"].astype(int)))) if n_years <= 15
                else f"{valid['year'].min():.0f}-{valid['year'].max():.0f}",
    })

country_stats = df_cy.groupby("country_code").apply(agg_country).reset_index()

# Log years of data per country
logger.info("Years of data used for mean calculation per country:")
for _, row in country_stats.iterrows():
    if row["n_years"] > 0:
        logger.info(f"  {row['country_code']}: {row['n_years']} year(s) → {row['years']}")

# Identify countries to drop
all_countries = set(df_cy["country_code"].unique())
plotted = set(country_stats[country_stats["n_years"] > 0]["country_code"])
dropped = all_countries - plotted

# Build detailed drop reasons
df_plot = country_stats[country_stats["n_years"] > 0].copy()
df_plot = df_plot.dropna(subset=["coord", "adjcov"])
actually_dropped = set(country_stats["country_code"]) - set(df_plot["country_code"])

# Log dropped countries and reasons
if actually_dropped:
    logger.warning("Countries DROPPED from plot:")
    for cc in sorted(actually_dropped):
        row = country_stats[country_stats["country_code"] == cc].iloc[0]
        reasons = []
        if row["n_years"] == 0:
            reasons.append("no country-year rows with both coord and adjcov")
        elif pd.isna(row["coord"]):
            reasons.append("missing coord")
        elif pd.isna(row["adjcov"]):
            reasons.append("missing adjcov")
        logger.warning(f"  {cc} ({COUNTRY_NAMES.get(cc, cc)}): {'; '.join(reasons)}")
else:
    logger.info("No countries dropped; all countries with data are plotted.")

df_plot = df_plot[["country_code", "coord", "adjcov", "n_years"]].copy().astype({"n_years": int})
df_plot["country_name"] = df_plot["country_code"].map(COUNTRY_NAMES).fillna(df_plot["country_code"])

logger.info(f"Final dataset: {len(df_plot)} countries plotted")

# Save the data
df_plot.to_csv("table1-coordvsAdjCov.csv", index=False)  
logger.info(f"Saved {len(df_plot)} rows to table1-coordvsAdjCov.csv")

# Pretty print the table
print("\nInstitutional Configuration by Country (mean over available years)")
print("="*70)
print(df_plot.sort_values('adjcov', ascending=False).to_string(index=False))
print("="*70)

# Create the scatter plot
fig, ax = plt.subplots(figsize=(10, 8))

# Classification thresholds (ICTWSS):
# Coverage: High ≥60%, Medium 30-59%, Low <30%
# Coordination: High ≥4, Medium 2-3.5, Low <2
coverage_threshold = 60
coord_threshold = 4

# Add reference lines (gray only)
ax.axvline(coverage_threshold, color='gray', linestyle='--', linewidth=1, alpha=0.6)
ax.axhline(coord_threshold, color='gray', linestyle='--', linewidth=1, alpha=0.6)

# Plot scatter points (single neutral color, no colormap)
ax.scatter(df_plot['adjcov'], df_plot['coord'],
          s=120, color='#333333', alpha=0.85, edgecolors='black', linewidth=1, zorder=3)

# Add country labels with slight offset to avoid overlap
for idx, row in df_plot.iterrows():
    ax.annotate(row['country_name'],
                xy=(row['adjcov'], row['coord']),
                xytext=(5, 5), textcoords='offset points',
                fontsize=9, fontweight='normal',
                bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                         edgecolor='lightgray', alpha=0.9))

# Labels and title
ax.set_xlabel('Adjusted Collective Bargaining Coverage (%)', fontsize=12, fontweight='bold')
ax.set_ylabel('Wage Coordination Index (1–5)', fontsize=12, fontweight='bold')
ax.set_title('Institutional Heterogeneity in Collective Bargaining Systems',
             fontsize=14, fontweight='bold', pad=20)

# Set axis limits
ax.set_xlim(0, 105)
ax.set_ylim(0.5, 5.5)

# Add quadrant labels (subtle)
ax.text(30, 4.7, 'Low Coverage\nHigh Coordination',
       fontsize=9, style='italic', alpha=0.5, ha='center', color='gray')
ax.text(80, 4.7, 'High Coverage\nHigh Coordination',
       fontsize=9, style='italic', alpha=0.5, ha='center', color='gray')
ax.text(30, 1.5, 'Low Coverage\nLow Coordination',
       fontsize=9, style='italic', alpha=0.5, ha='center', color='gray')
ax.text(80, 1.5, 'High Coverage\nLow Coordination',
       fontsize=9, style='italic', alpha=0.5, ha='center', color='gray')

# Grid
ax.grid(True, alpha=0.25, linestyle=':', linewidth=0.5)

# Tight layout
plt.tight_layout()

# Save figure
plt.savefig('figure1-coordvsAdjCov.png', dpi=300, bbox_inches='tight')
plt.savefig('figure1-coordvsAdjCov.pdf', bbox_inches='tight')
logger.info("Saved scatter plot to figure1-coordvsAdjCov.png and .pdf")

plt.show()

# Print summary statistics
print("\n" + "="*70)
print("SUMMARY STATISTICS")
print("="*70)
print(f"Coverage - Mean: {df_plot['adjcov'].mean():.1f}%, Std: {df_plot['adjcov'].std():.1f}%, Range: [{df_plot['adjcov'].min():.1f}, {df_plot['adjcov'].max():.1f}]")
print(f"Coordination - Mean: {df_plot['coord'].mean():.2f}, Std: {df_plot['coord'].std():.2f}, Range: [{df_plot['coord'].min():.1f}, {df_plot['coord'].max():.1f}]")
print(f"Correlation (Coverage, Coordination): {df_plot['adjcov'].corr(df_plot['coord']):.3f}")
print("="*70)

# Count countries in each quadrant
high_cov_high_coord = len(df_plot[(df_plot['adjcov'] >= coverage_threshold) & (df_plot['coord'] >= coord_threshold)])
high_cov_low_coord = len(df_plot[(df_plot['adjcov'] >= coverage_threshold) & (df_plot['coord'] < coord_threshold)])
low_cov_high_coord = len(df_plot[(df_plot['adjcov'] < coverage_threshold) & (df_plot['coord'] >= coord_threshold)])
low_cov_low_coord = len(df_plot[(df_plot['adjcov'] < coverage_threshold) & (df_plot['coord'] < coord_threshold)])

print("\nINSTITUTIONAL TYPOLOGY DISTRIBUTION")
print("="*70)
print(f"Type A (High Coverage / High Coordination): {high_cov_high_coord} countries")
print(f"Type B (High Coverage / Low Coordination): {high_cov_low_coord} countries")
print(f"Type C (Low Coverage / High Coordination): {low_cov_high_coord} countries")
print(f"Type D (Low Coverage / Low Coordination): {low_cov_low_coord} countries")
print("="*70)