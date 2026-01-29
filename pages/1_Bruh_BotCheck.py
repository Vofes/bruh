import streamlit as st
import os
import sys

# Ensure the app can find the 'src' folder
sys.path.append(os.getcwd())

try:
    from src.bruh_processor import process_bruh_logic
    # Corrected filename to match what we built (rawviewer)
    from src.rawviewer import render_raw_csv_view 
    from src.guide_loader import render_markdown_guide
except ModuleNotFoundError as e:
    st.error(f"🚨 Logic modules not found: {e}")
    st.stop()

st.set_page_config(page_title="Bruh-BotCheck", layout="wide")

# Check if data exists in session state (passed from Home page)
if 'df' not in st.session_state:
    st.warning("📋 Data not found in memory.")
    st.info("Please go to the **Home** page first to download the latest chat logs.")
    st.stop()

df = st.session_state['df']

with st.sidebar:
    st.header("⚙️ Global BotCheck")
    # Defaulting to your specified starting point
    start_bruh = st.number_input("Starting Bruh #", value=311925)
    end_bruh = st.number_input("Ending Bruh # (0=End)", value=0)
    jump_limit = st.number_input("Max Jump Allowed", value=1500)
    hide_invalid = st.checkbox("Hide 'No Consensus' Bruhs", value=False)
    
    st.divider()
    st.subheader("Raw Viewer Settings")
    show_raw = st.checkbox("Enable Raw Viewer", value=False)
    # Adjusted defaults to likely row ranges for a 450k+ dataset
    v_start = st.number_input("View Start Row", value=len(df)-1000 if len(df) > 1000 else 0)
    v_end = st.number_input("View End Row", value=len(df))
    
    run = st.button("🚀 Run Analysis", use_container_width=True)

# --- SHOW GUIDE WHEN NOT RUNNING ---
if not run:
    # Ensure botcheck_guide.md exists in your /guides folder!
    render_markdown_guide("botcheck_guide.md")

if run:
    # 1. BRAIN: Global Analysis
    with st.spinner("Analyzing the bruh-chain..."):
        res_m, res_s, found, last_val, unique_count = process_bruh_logic(df, start_bruh, end_bruh, jump_limit, hide_invalid)
    
    # 2. METRICS
    st.header("📊 Global Analysis")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Final Chain Num", f"{last_val:,}" if found else "N/A")
    m2.metric("Total Mistakes", f"{len(res_m):,}")
    m3.metric("Total Success Log", f"{len(res_s):,}")
    m4.metric("Unique Successful", f"{unique_count:,}")

    st.divider()

    # 3. VIEW: UI Layout
    if show_raw:
        col_raw, col_res = st.columns([1, 1.2])
        with col_raw:
            # Displays the Author and Content columns specifically
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
