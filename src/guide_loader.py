import streamlit as st
import os

def render_markdown_guide(file_name):
    """
    Reads a markdown file from the guides folder and renders it in Streamlit.
    """
    clean_name = os.path.basename(file_name)
    
    guide_path = os.path.join("guides", clean_name)
    
    if os.path.exists(guide_path):
        with open(guide_path, "r", encoding="utf-8") as f:
            content = f.read()
        st.markdown(content)
    else:
        # 3. Help the user find where it's actually looking
        abs_path = os.path.abspath(guide_path)
        st.warning(f"⚠️ Guide not found at {guide_path}")
        st.info(f"Full path searched: `{abs_path}`")
