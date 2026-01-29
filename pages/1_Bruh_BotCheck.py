import streamlit as st
import os
from src.engine import run_botcheck_logic

st.set_page_config(page_title="Bruh-BotCheck Validator", page_icon="🤖", layout="wide")

def load_guide(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f: return f.read()
    return "⚠️ Guide file not found."

if 'df' not in st.session_state:
    st.error("⚠️ No data found. Please return to the Home page to sync."); st.stop()

df = st.session_state['df']

with st.sidebar:
    st.header("⚙️ BotCheck Config")
    start_bruh = st.number_input("Starting Bruh #", value=311925)
    end_bruh = st.number_input("Ending Bruh # (0 for End)", value=0)
    jump_limit = st.number_input("Max Jump Allowed", value=1500)
    hide_invalid = st.checkbox("Hide 'No Consensus' Bruhs", value=False)
    st.divider()
    st.subheader("Viewport Control")
    show_raw = st.checkbox("Show Raw Data Log", value=False)
    v_start = st.number_input("View Start Row", value=400000)
    v_end = st.number_input("View End Row", value=500000)
    run = st.button("🚀 Run Full BotCheck", use_container_width=True)

if not run:
    st.markdown(load_guide("guides/botcheck_guide.md"))

if run:
    with st.spinner("🧠 Analyzing global sequence..."):
        # The line below now matches the 5 return values from engine.py
        res_m, res_s, found, last_val, unique_count = run_botcheck_logic(df, start_bruh, end_bruh, jump_limit, hide_invalid)
    
    st.header("📊 Global Metrics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Chain End", last_val if found else "N/A")
    m2.metric("Total Mistakes", len(res_m))
    m3.metric("Total Success Log", len(res_s))
    m4.metric("Unique Successful", unique_count)

    st.divider()

    # Filtering for table display ONLY
    m_view = res_m[(res_m['Line'] >= v_start) & (res_m['Line'] <= v_end)]
    s_view = res_s[(res_s['Line'] >= v_start) & (res_s['Line'] <= v_end)]

    if show_raw:
        col_raw, col_res = st.columns([1, 1])
        with col_raw:
            st.subheader(f"📄 Raw Log ({v_start}-{v_end})")
            st.dataframe(df.iloc[v_start:v_end, [1, 3]], use_container_width=True, height=600)
        res_container = col_res
    else:
        res_container = st.container()

    with res_container:
        st.subheader(f"🔎 Filtered View ({v_start}-{v_end})")
        t1, t2 = st.tabs(["❌ Mistakes", "✅ Success Log"])
        t1.dataframe(m_view, use_container_width=True)
        t2.dataframe(s_view, use_container_width=True)
