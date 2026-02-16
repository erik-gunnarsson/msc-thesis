"""
Shared utilities for Streamlit dashboard pages.
"""

import re
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def render_markdown_with_images(markdown_text: str, base_path: Path) -> None:
    """Render markdown, replacing image refs with st.image() so local images load correctly."""
    pattern = r"!\[([^\]]*)\]\(([^)]+)\)"
    parts = re.split(pattern, markdown_text)

    if len(parts) == 1:
        st.markdown(markdown_text)
        return

    for i in range(0, len(parts), 3):
        if parts[i].strip():
            st.markdown(parts[i])
        if i + 2 < len(parts):
            alt_text, img_path = parts[i + 1], parts[i + 2]
            resolved = (base_path / img_path).resolve()
            if resolved.exists():
                st.image(str(resolved), caption=alt_text or None)
            else:
                st.markdown(f"*[Image not found: {img_path}]*")
