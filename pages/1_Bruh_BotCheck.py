import streamlit as st
import os
import sys
import pandas as pd

sys.path.append(os.getcwd())
from src.bruh_processor import process_bruh_logic
from src.raw_viewer import render_raw_csv_view

st.set_page_config(page_title="Bruh-BotCheck", layout="wide")

if 'df' not in st.session_state:
    st.error("⚠️ Data not loaded."); st.stop()

df = st.session_state['df']

with st.sidebar:
    st.header("⚙️ Settings")
    start_num = st.number_input("Start Bruh #", value=311925)
    end_num = st.number_input("End Bruh # (0=End)", value=0)
    jump_limit = st.number_input("Jump Limit", value=1500)
    st.divider()
    show_raw = st.checkbox("Show Raw CSV View")
    v_start = st.number_input("View Start", value=400000)
    v_end = st.number_input("View End", value=500000)
    run = st.button("🚀 Run Analysis", use_container_width=True)

if run:
    with st.spinner("Analyzing..."):
        # We catch the output directly as DataFrames
        df_win, df_lost, df_err, last_val = process_bruh_logic(df, start_num, end_num, jump_limit)
    
    st.header("📊 Results")
    m1, m2, m3 = st.columns(3)
    m1.metric("Unique Winners", len(df_win))
    m2.metric("Lost Bruhs", len(df_lost))
    m3.metric("End Number", last_val)

    st.divider()

    if show_raw:
        c1, c2 = st.columns([1, 1.2])
        with c1: render_raw_csv_view(df, v_start, v_end)
        display_area = c2
    else: display_area = st.container()

    with display_area:
        t1, t2, t3 = st.tabs(["✅ Winners", "🔍 Lost", "❌ Mistakes"])
        
        with t1:
            st.dataframe(df_win, use_container_width=True)
        with t2:
            if not df_lost.empty:
                # We force convert everything to string right before display 
                # to prevent ANY Arrow/Overflow errors
                st.dataframe(df_lost.astype(str), use_container_width=True)
            else:
                st.info("No lost bruhs.")
        with t3:
            st.dataframe(df_err.astype(str), use_container_width=True)
