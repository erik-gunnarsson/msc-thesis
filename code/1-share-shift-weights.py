'''
# share-shift-weights

loads your countryxyear IFR robot stock Excel (wide → long),
loads your industry automation weights CSV,
creates a countryxindustryxyear panel by a Cartesian product, and
computes the shift-share exposure: robot_stock * auto_weight (plus log variant),
saves a CSV you can merge later with Eurostat SBS.
'''


import pandas as pd
import numpy as np

# -----------------------------
# 0) File paths (EDIT THESE)
# -----------------------------
WEIGHTS_CSV = "/Users/AmatusCapital/Documents/Coding/github_eg/msc-thesis/data/GM_industry_automation_weights_1980.csv"
IFR_XLSX    = "/Users/AmatusCapital/Documents/Coding/github_eg/msc-thesis/data/IFR_operational_stock_2004_to_2023.xlsx"

OUT_CSV     = "/Users/AmatusCapital/Documents/Coding/github_eg/msc-thesis/data/IFR_industry_exposure_shift_share_2004_2023.csv"

# -----------------------------
# 1) Load weights (industry-level, time-invariant)
# -----------------------------
w = pd.read_csv(WEIGHTS_CSV)
w.columns = [c.strip() for c in w.columns]

# Expect: ind1990, replaceability_ind, (maybe) w_ind
required = {"ind1990", "replaceability_ind"}
missing = required - set(w.columns)
if missing:
    raise ValueError(f"Missing columns in weights CSV: {missing}. Found columns: {list(w.columns)}")

weights = (
    w[["ind1990", "replaceability_ind"]]
    .rename(columns={"ind1990": "industry_id", "replaceability_ind": "auto_weight"})
    .dropna(subset=["industry_id", "auto_weight"])
)

# Drop non-industry rows if present
weights = weights[~weights["industry_id"].astype(str).str.lower().str.contains("n/a")].copy()

# -----------------------------
# 2) Load IFR robot stock (country x year, likely wide format)
# -----------------------------
# Year headers are in row 2 (0-indexed), so use header=2
ifr_raw = pd.read_excel(IFR_XLSX, sheet_name=0, header=2)

# Skip the first row if it's empty/NaN
ifr_raw = ifr_raw.iloc[1:].reset_index(drop=True)

# Detect year columns (either ints like 2004 or strings like "2004")
year_cols = [c for c in ifr_raw.columns if isinstance(c, (int, np.integer)) and 1900 <= int(c) <= 2100]
if not year_cols:
    year_cols = [c for c in ifr_raw.columns if str(c).strip().isdigit() and 1900 <= int(str(c).strip()) <= 2100]

if not year_cols:
    raise ValueError("Could not detect year columns in IFR Excel. Check the file format.")

# Country/region label column assumed to be the first non-year column
non_year_cols = [c for c in ifr_raw.columns if c not in year_cols]
country_col = non_year_cols[0]

ifr_long = ifr_raw[[country_col] + year_cols].melt(
    id_vars=[country_col],
    value_vars=year_cols,
    var_name="year",
    value_name="robot_stock"
)

ifr_long["year"] = ifr_long["year"].astype(int)
ifr_long["robot_stock"] = pd.to_numeric(ifr_long["robot_stock"], errors="coerce")
ifr_long = ifr_long.dropna(subset=["robot_stock"]).copy()

# Optional: extract ISO2 if format like "ZA-South Africa"
label = ifr_long[country_col].astype(str).str.strip()
iso2 = label.str.extract(r"^([A-Z]{2})-")[0]
ifr_long["country"] = np.where(iso2.notna(), iso2, label)

# Optional: drop obvious aggregates (tweak as needed)
# Keep rows with ISO2 OR those that look like "XX-Name"
ifr_long = ifr_long[(iso2.notna()) | (label.str.contains("-", regex=False))].copy()

ifr_long = ifr_long[["country", "year", "robot_stock"]].drop_duplicates()

# -----------------------------
# 3) Construct industry exposure via cross join (cartesian product)
# -----------------------------
# This creates country x year x industry
panel = ifr_long.merge(weights, how="cross")

# Level exposure
panel["robot_exposure"] = panel["robot_stock"] * panel["auto_weight"]

# Common transform for robustness / interpretation (handles zeros)
panel["ln1p_robot_stock"] = np.log1p(panel["robot_stock"])
panel["robot_exposure_log"] = panel["ln1p_robot_stock"] * panel["auto_weight"]

panel = panel.sort_values(["country", "industry_id", "year"]).reset_index(drop=True)

# -----------------------------
# 4) Save
# -----------------------------
panel.to_csv(OUT_CSV, index=False)
print(f"Saved: {OUT_CSV}  |  rows={len(panel):,}  cols={panel.shape[1]}")
