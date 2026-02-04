import pandas as pd
import numpy as np

# 0) File paths (EDIT THESE)
# -----------------------------
WEIGHTS_CSV = "/Users/AmatusCapital/Documents/Coding/github_eg/msc-thesis/data/GM_industry_automation_weights_1980.csv"

IFR_EXPOSURE_CSV    = "/Users/AmatusCapital/Documents/Coding/github_eg/msc-thesis/data/IFR_industry_exposure_shift_share_2004_2023.csv"
CROSSWALK = "/Users/AmatusCapital/Documents/Coding/github_eg/msc-thesis/data/ind1990_to_nace2.csv"

w = pd.read_csv(WEIGHTS_CSV)
cw = pd.read_csv(CROSSWALK)

# Clean strings
w["ind1990"] = w["ind1990"].astype(str).str.strip()
cw["ind1990"] = cw["ind1990"].astype(str).str.strip()

# Drop the N/A row if present
w = w[~w["ind1990"].str.lower().str.contains("n/a")].copy()

# Merge weights -> NACE2
wm = w.merge(cw, on="ind1990", how="inner")

# Keep manufacturing only (optional guard)
# NACE2 codes are already numeric in the crosswalk file
wm["nace2_num"] = pd.to_numeric(wm["nace2"], errors="coerce")
wm = wm[(wm["nace2_num"] >= 10) & (wm["nace2_num"] <= 33)].copy()

# Aggregate to NACE2 weights (weighted avg using w_ind)
# If you prefer simple average, replace the weighted avg line.
def wavg(group):
    x = group["replaceability_ind"].astype(float)
    wgt = group["w_ind"].astype(float)
    if wgt.sum() == 0:
        return x.mean()
    return (x * wgt).sum() / wgt.sum()

weights_nace2 = (
    wm.groupby("nace2_num", as_index=False)
      .apply(lambda g: pd.Series({
          "auto_weight_nace2": wavg(g),
          "n_sources": g["ind1990"].nunique(),
          "w_ind_sum": g["w_ind"].astype(float).sum()
      }))
      .reset_index(drop=True)
      .rename(columns={"nace2_num":"nace2"})
)

# Save NACE2 weights in data (you’ll merge these with country-year robot stocks)

weights_nace2.to_csv("/Users/AmatusCapital/Documents/Coding/github_eg/msc-thesis/data/auto_weights_nace2.csv", index=False)
print(weights_nace2.head())


print("======= sanity checks =======")
print("w_ind_sum total (across NACE divisions):", weights_nace2["w_ind_sum"].sum())
print("min/max auto_weight_nace2:", weights_nace2["auto_weight_nace2"].min(), weights_nace2["auto_weight_nace2"].max())
print("n NACE divisions:", weights_nace2["nace2"].nunique())
