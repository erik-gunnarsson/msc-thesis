'''
Regression Analysis: Employment vs ICT, Institutions, and Interaction
=======================================================================
Model: lnEmp = β₁·ICT + β₂·Institution + β₃·(ICT × Institution) + β₄·lnVA + FE + ε

Data Sources:
- sbs.csv: country, industry, year, emp, va
- klem_ict.csv: country, industry, year, ict_share
- ictwss.csv: country, year, bargcov
'''

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import time
from loguru import logger
from linearmodels.panel import PanelOLS

# --- Load ---
sbs = pd.read_csv("sbs.csv")              # country, industry, year, emp, va
klem = pd.read_csv("klem_ict.csv")        # country, industry, year, ict_share
ictwss = pd.read_csv("ictwss.csv")        # country, year, bargcov

# --- Basic cleaning ---
for df in (sbs, klem, ictwss):
    df["country"] = df["country"].str.upper().str.strip()

sbs["industry"] = sbs["industry"].astype(str).str.strip()
klem["industry"] = klem["industry"].astype(str).str.strip()

# --- Merge ---
df = sbs.merge(klem, on=["country", "industry", "year"], how="inner")
df = df.merge(ictwss, on=["country", "year"], how="inner")

# --- Logs (avoid zeros) ---
df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=["emp", "va", "ict_share", "bargcov"])

df["ln_emp"] = np.log(df["emp"])
df["ln_va"] = np.log(df["va"])
df["ict_share"] = df["ict_share"].astype(float)
df["bargcov"] = df["bargcov"].astype(float)

# Interaction
df["ict_x_bargcov"] = df["ict_share"] * df["bargcov"]

# --- Panel index ---
df = df.set_index(["country", "industry", "year"])

# --- Regression: lnEmp on ICT, institutions, interaction + lnVA, with FE ---
exog = df[["ict_share", "bargcov", "ict_x_bargcov", "ln_va"]]
mod = PanelOLS(
    df["ln_emp"],
    exog,
    entity_effects=True,   # country-industry FE (because entity = (country, industry))
    time_effects=True      # year FE
)

res = mod.fit(cov_type="clustered", cluster_entity=True)
print(res.summary)