"""Vector Space page - 3D schools of thought visualization."""

import streamlit as st

from components.vectorspace import create_3d_vectorspace, get_vectorspace_data

st.header("3D Vector Space: Schools of Thought")
st.markdown("""
This interactive 3D visualization shows how different papers and schools of thought
are positioned across three dimensions:
- **Institutions**: Role of institutional factors (e.g., collective bargaining)
- **Reallocation**: Focus on labor reallocation effects
- **Distribution**: Emphasis on distributional consequences

**Interact with the plot**: Rotate, zoom, and hover over points to see details.
The gold star represents this thesis.
""")

try:
    fig = create_3d_vectorspace()
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Data Table")
    df = get_vectorspace_data()
    st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error loading vector space visualization: {str(e)}")
    st.info("Please ensure the vectorspace.csv file exists in the data folder.")

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>MSc Thesis Dashboard</div>",
    unsafe_allow_html=True,
)
