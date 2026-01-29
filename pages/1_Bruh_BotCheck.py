import streamlit as st
import os
import sys
import pandas as pd
import re

# Fix pathing for Streamlit Cloud
sys.path.append(os.getcwd())

try:
    from src.bruh_processor import process_bruh_logic
    from src.raw_viewer import render_raw_csv_view
except ImportError:
    st.error("🚨 Could not load modules from 'src'. Ensure '__init__.py' exists.")
    st.stop()

st.set_page_config(page_title="Bruh-BotCheck Pro", layout="wide")

if 'df' not in st.session_state:
    st.error("⚠️ Data not loaded. Go to Home."); st.stop()

df = st.session_state['df']

with st.sidebar:
    st.header("⚙️ Analysis Config")
    start_num = st.number_input("Starting Bruh #", value=311925)
    end_num = st.number_input("Ending Bruh # (0=End)", value=0)
    jump_limit = st.number_input("Max Jump", value=1500)
    hide_invalid = st.checkbox("Hide 'No Consensus' Noise", value=False)
    
    st.divider()
    st.subheader("Raw Viewer")
    show_raw = st.checkbox("Enable Raw Viewer")
    v_start = st.number_input("View Start Row", value=400000)
    v_end = st.number_input("View End Row", value=500000)
    
    run = st.button("🚀 Run Analysis", use_container_width=True)

if run:
    res_m, res_s, found, last_val, unique_count = process_bruh_logic(df, start_num, end_num, jump_limit, hide_invalid)
    
    # --- AUDIT LOGIC FOR EXCLUDED BRUHS ---
    # 1. Get Corrected (Rollback) Bruhs
    fixes = res_s[res_s["Status"] == "CORRECT-FIX"].copy()
    fixes["Exclusion Reason"] = "Overwritten by Rollback"

    # 2. Get Disqualified Jumps
    jumps = res_m[res_m["Reason"].str.contains("Jump", na=False)].copy()
    jumps["Exclusion Reason"] = "Disqualified Jump Entry"

    excluded_all = pd.concat([fixes, jumps], ignore_index=True)

    def get_num(msg):
        m = re.search(r'bruh\s+(\d+)', str(msg), re.IGNORECASE)
        return int(m.group(1)) if m else 0

    if not excluded_all.empty:
        excluded_all["Bruh #"] = excluded_all["Msg"].apply(get_num)
        excluded_all = excluded_all[["Line", "Author", "Bruh #", "Exclusion Reason"]].sort_values("Line")

    # --- METRICS ---
    st.header("📊 Global Results")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Unique Credited", unique_count)
    m2.metric("Excluded/Lost", len(excluded_all))
    m3.metric("Total Errors", len(res_m))
    m4.metric("Chain Ends At", last_val if found else "N/A")

    st.divider()

    # --- TABS ---
    if show_raw:
        c1, c2 = st.columns([1, 1.2])
        with c1: render_raw_csv_view(df, v_start, v_end)
        container = c2
    else:
        container = st.container()

    with container:
        t1, t2, t3 = st.tabs(["✅ Unique (Points)", "🔍 Excluded (No Points)", "❌ All Mistakes"])
        with t1:
            st.dataframe(res_s[res_s["Status"] == "CORRECT"], use_container_width=True)
        with t2:
            st.info("These bruh numbers were detected but didn't count toward the 'Unique Successful' metric.")
            st.dataframe(excluded_all, use_container_width=True)
        with t3:
            st.dataframe(res_m, use_container_width=True)
