import streamlit as st
import pandas as pd
import os
import sys

# --- SETUP ---
sys.path.append(os.getcwd())
from app import load_data # Using your central loader
from src.bruh_processor import process_bruh_logic
from src.raw_viewer import render_raw_csv_view 
from src.guide_loader import render_markdown_guide

st.set_page_config(page_title="Bruh-BotCheck", layout="wide")

st.title("🤖 Bot Detection Engine")

# --- 1. THE GUIDE (Dropdown) ---
with st.expander("📖 How to use the BotCheck Engine"):
    render_markdown_guide("botcheck_guide.md")

# --- 2. COMMAND CENTER (Main Page Controls) ---
st.subheader("⚙️ Analysis Configuration")
with st.container(border=True):
    # Row 1: Chain Settings
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        start_bruh = st.number_input("Starting Bruh #", value=0)
    with c2:
        end_bruh = st.number_input("Ending Bruh # (0=End)", value=0)
    with c3:
        jump_limit = st.number_input("Max Jump Allowed", value=100)
    with c4:
        hide_invalid = st.checkbox("Hide 'No Consensus'", value=False)

    # Row 2: Viewer Settings
    v1, v2, v3, v4 = st.columns([1, 1, 1, 1.5])
    df = load_data() # Using central loader
    
    with v1:
        show_raw = st.toggle("Enable Raw Viewer", value=False)
    with v2:
        v_start = st.number_input("View Start Row", value=len(df)-1000 if len(df) > 1000 else 0)
    with v3:
        v_end = st.number_input("View End Row", value=len(df))
    with v4:
        st.write("") # Spacer
        run = st.button("🚀 Run Full Analysis", use_container_width=True, type="primary")

st.divider()

# --- 3. EXECUTION ---
if run:
    with st.spinner("Analyzing the bruh-chain history..."):
        res_m, res_s, found, last_val, unique_count = process_bruh_logic(
            df, start_bruh, end_bruh, jump_limit, hide_invalid
        )
    
    # METRICS
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Final Chain Num", f"{last_val:,}" if found else "N/A")
    m2.metric("Total Mistakes", f"{len(res_m):,}", delta_color="inverse")
    m3.metric("Total Success Log", f"{len(res_s):,}")
    m4.metric("Unique Successful", f"{unique_count:,}")

    st.divider()

    # LAYOUT
    if show_raw:
        col_raw, col_res = st.columns([1, 1.2])
        with col_raw:
            render_raw_csv_view(df, int(v_start), int(v_end))
        container = col_res
    else:
        container = st.container()

    with container:
        st.subheader("📝 Complete Analysis Logs")
        t1, t2 = st.tabs(["❌ Mistakes List", "✅ Success Log"])
        with t1:
            st.dataframe(res_m, use_container_width=True, hide_index=True)
        with t2:
            st.dataframe(res_s, use_container_width=True, hide_index=True)
