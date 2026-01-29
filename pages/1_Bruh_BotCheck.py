import streamlit as st
from src.bruh_processor import process_bruh_logic
from src.raw_viewer import render_raw_csv_view

st.set_page_config(page_title="Bruh-BotCheck", layout="wide")

if 'df' not in st.session_state:
    st.error("⚠️ Please load data on the Home page first."); st.stop()

df = st.session_state['df']

with st.sidebar:
    st.header("⚙️ Global BotCheck")
    start_bruh = st.number_input("Starting Bruh #", value=311925)
    end_bruh = st.number_input("Ending Bruh # (0=End)", value=0)
    jump_limit = st.number_input("Max Jump Allowed", value=1500)
    hide_invalid = st.checkbox("Hide 'No Consensus' Bruhs", value=False)
    
    st.divider()
    st.subheader("Raw Viewer Settings")
    show_raw = st.checkbox("Enable Raw Viewer", value=False)
    v_start = st.number_input("View Start Row", value=400000)
    v_end = st.number_input("View End Row", value=500000)
    
    run = st.button("🚀 Run Analysis", use_container_width=True)

if run:
    # 1. BRAIN: Global analysis of the sequence
    res_m, res_s, found, last_val, unique_count = process_bruh_logic(df, start_bruh, end_bruh, jump_limit, hide_invalid)
    
    # 2. METRICS: Total stats for the whole range
    st.header("📊 Global Analysis")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Final Chain Num", last_val if found else "N/A")
    m2.metric("Total Mistakes", len(res_m))
    m3.metric("Total Success Log", len(res_s))
    m4.metric("Unique Successful", unique_count)

    st.divider()

    # 3. VIEW: UI Layout
    if show_raw:
        col_raw, col_res = st.columns([1, 1.2])
        with col_raw:
            # Calling the Viewer service
            render_raw_csv_view(df, v_start, v_end)
        container = col_res
    else:
        container = st.container()

    with container:
        st.subheader("📝 Complete Analysis Logs")
        t1, t2 = st.tabs(["❌ Mistakes List", "✅ Success Log"])
        # Displaying the FULL global results (Independent of viewport)
        t1.dataframe(res_m, use_container_width=True)
        t2.dataframe(res_s, use_container_width=True)
