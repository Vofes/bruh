import streamlit as st
import os

def render_markdown_guide(file_name):
    """
    Reads a markdown file from the guides folder and renders it in Streamlit.
    """
    # Construct path: guides/filename.md
    guide_path = os.path.join("guides", file_name)
    
    if os.path.exists(guide_path):
        with open(guide_path, "r", encoding="utf-8") as f:
            content = f.read()
        st.markdown(content)
    else:
        st.warning(f"⚠️ Guide not found at {guide_path}. Please ensure the file exists in the 'guides' folder.")
