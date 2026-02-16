"""Decision Tree page - data source routes flow diagram."""

import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.layouts import TreeLayout

from components.decisiontree import create_decision_tree_state

st.header("Decision Tree: Data Source Routes Tested")
st.markdown("""
This interactive flow diagram shows all the routes and data sources we tested during the project,
including successful paths, dead ends, and exploratory tests.

**Interact with the diagram**: You can drag nodes, zoom, pan, and click on nodes/edges for more details.
""")

if "decision_tree_state" not in st.session_state:
    st.session_state.decision_tree_state = create_decision_tree_state()

st.session_state.decision_tree_state = streamlit_flow(
    "decision_tree_flow",
    st.session_state.decision_tree_state,
    layout=TreeLayout(direction="right"),
    fit_view=True,
    height=700,
    enable_node_menu=True,
    enable_edge_menu=True,
    enable_pane_menu=True,
    get_edge_on_click=True,
    get_node_on_click=True,
    show_minimap=True,
    hide_watermark=True,
    allow_new_edges=False,
    min_zoom=0.1,
)

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    ### Legend:
    - 🔵 **Blue**: Project Start
    - 🟢 **Green**: Successful Route
    - 🔴 **Red**: Dead End
    - 🟡 **Yellow**: Exploratory Test
    - 🟣 **Purple**: Final Solution
    """)
with col2:
    st.markdown("""
    ### Notes:
    - **swedenv1**: Quick test on Swedish data (exploratory)
    - **europev1**: Broader test on EU data (used in final model)
    - **uncomtradev1**: Abandoned when IFR data became available
    - **PIAAC**: US-focused, incompatible with EU analysis
    - **JCR & ONET**: Exploratory tests on task content data
    """)

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>MSc Thesis Dashboard</div>",
    unsafe_allow_html=True,
)
