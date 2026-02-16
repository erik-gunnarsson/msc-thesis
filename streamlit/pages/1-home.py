"""Home page - README content with embedded images."""

import streamlit as st

from components.utils import PROJECT_ROOT, render_markdown_with_images

st.header("MSc Thesis: Robotization, Employment, & Collective Bargaining")
st.markdown("---")

st.info(
    'Click here to read the full [README.md](https://github.com/erik-gunnarsson/msc-thesis/blob/main/README.md)',
    icon="ℹ️",
)

readme_path = PROJECT_ROOT / "README.md"
with open(readme_path, "r") as f:
    readme = f.read()
render_markdown_with_images(readme, base_path=PROJECT_ROOT)

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>MSc Thesis Dashboard</div>",
    unsafe_allow_html=True,
)
