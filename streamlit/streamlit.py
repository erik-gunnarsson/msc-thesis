"""
Main Streamlit Dashboard
MSc Thesis - Robot Adoption & Employment Analysis

Entry point. Uses Streamlit multipage: each page lives in pages/ as its own component.
"""

import streamlit as st

st.set_page_config(
    page_title="MSc Thesis Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Redirect to Home so landing is the README view
st.switch_page("pages/1-home.py")
