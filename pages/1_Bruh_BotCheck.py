import streamlit as st
import os
import sys
import pandas as pd

sys.path.append(os.getcwd())
from src.bruh_processor import process_bruh_logic
from src.raw_viewer import render_raw_csv_view

st.set_page_config(page_title="Bruh-BotCheck", layout="wide")

if 'df' not in st.session_state:
    st.error("⚠️ Load data on Home page."); st.stop()

df = st.session_state['df']

with st.sidebar:
    st.header("⚙️ Config")
    start_num = st.number_input("Starting Bruh #", value=311925)
    end_num = st.number_input("Ending Bruh #", value=0)
    jump_limit = st.number_input("Max Jump", value=1500)
    st.divider()
    show_raw = st.checkbox("Show Raw Viewer")
    v_start = st.number_input("View Start", value=400000)
    v_end = st.number_input("View End", value=500000)
    run = st.button("🚀 Run Analysis", use_container_width=True)

if run:
    with st.spinner("Processing..."):
        df_winners, df_lost, df_mistakes, last_val = process_bruh_logic(df, start_num, end_num, jump_limit)
    
    st.header("📊 Sequence Results")
    c1, c2, c3 = st.columns(3)
    c1.metric("Unique Winners", len(df_winners))
    c2.metric("Missing/Lost Bruhs", len(df_lost))
    c3.metric("Final Valid Num", last_val)

    st.divider()

    if show_raw:
        col_raw, col_res = st.columns([1, 1.2])
        with col_raw: render_raw_csv_view(df, v_start, v_end)
        container = col_res
    else: container = st.container()

    with container:
        t1, t2, t3 = st.tabs(["✅ Winners (Unique)", "🔍 Lost (Non-Unique)", "❌ Mistakes Log"])
        
        with t1:
            st.dataframe(df_winners, use_container_width=True)
            
        with t2:
            if not df_lost.empty:
                st.dataframe(df_lost, use_container_width=True)
            else:
                st.success("No missing bruhs found in this range!")
            
        with t3:
            st.dataframe(df_mistakes, use_container_width=True)
