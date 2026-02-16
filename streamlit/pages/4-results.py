"""Results page - regression outputs and tables."""

import pandas as pd
import streamlit as st

from components.utils import PROJECT_ROOT

OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Map friendly labels to (txt_file, csv_file or None)
RESULT_SETS = {
    "1. Baseline regression": ("equation1_baseline_regression.txt", None),
    "2. Coordination moderation": ("equation2_coordination_moderation.txt", None),
    "3. Coverage moderation": ("equation3_coverage_moderation.txt", None),
    "4. Industry coordination (by industry)": (
        "equation4_industry_coordination_summary.txt",
        "industry_by_industry_coordination.csv",
    ),
    "5. Industry coverage (by industry)": (
        "equation5_industry_coverage_summary.txt",
        "industry_by_industry_coverage.csv",
    ),
}

st.header("Results")
st.markdown("Select a result to view the regression output and (where available) the underlying data.")

selected = st.selectbox("Select a result", options=list(RESULT_SETS.keys()), key="results_select")
txt_file, csv_file = RESULT_SETS[selected]

# Text output
txt_path = OUTPUTS_DIR / txt_file
if txt_path.exists():
    with st.expander("Regression output", expanded=True):
        with open(txt_path, "r") as f:
            st.code(f.read(), language=None)
else:
    st.warning(f"File not found: {txt_file}")

# CSV table (when available)
if csv_file:
    csv_path = OUTPUTS_DIR / csv_file
    if csv_path.exists():
        st.subheader("Data")
        df = pd.read_csv(csv_path)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(f"CSV not found: {csv_file}")

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>MSc Thesis Dashboard</div>",
    unsafe_allow_html=True,
)
