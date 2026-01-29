import streamlit as st
import os
from src.engine import run_botcheck_logic

st.set_page_config(page_title="Bruh-BotCheck Validator", page_icon="🤖", layout="wide")

def load_guide(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "⚠️ Guide file not found."

if 'df' not in st.session_state:
    st.error("⚠️ No data found. Please return to the Home page to sync.")
    st.stop()

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
    guide_path = "guides/botcheck_guide.md" 
    st.markdown(load_guide(guide_path))

if run:
    with st.spinner("🧠 Scanning sequence..."):
        # The engine runs on the WHOLE dataframe
        res_m, res_s, found, last_val = run_botcheck_logic(df, start_bruh, end_bruh, jump_limit, hide_invalid)
    
    # --- GLOBAL STATS (Unfiltered) ---
    st.header("📊 Global Analysis Results")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if found:
            st.success(f"**Chain Validated To:** {last_val}")
        else:
            st.error("Anchor Not Found")
    with col_b:
        st.metric("Total Mistakes Found", len(res_m))
    with col_c:
        st.metric("Total Successful Bruhs", len(res_s))

    st.divider()

    # --- VIEWPORT FILTERING (Display Only) ---
    # We filter the results ONLY for the dataframe display
    m_view = res_m[(res_m['Line'] >= v_start) & (res_m['Line'] <= v_end)]
    s_view = res_s[(res_s['Line'] >= v_start) & (res_s['Line'] <= v_end)]

    if show_raw:
        col_raw, col_res = st.columns([1, 1])
        with col_raw:
            st.subheader(f"📄 Raw Log (Rows {v_start}-{v_end})")
            st.dataframe(df.iloc[v_start:v_end, [1, 3]], use_container_width=True, height=600)
        res_container = col_res
    else:
        res_container = st.container()

    with res_container:
        st.subheader(f"🔎 Viewport Results (Rows {v_start}-{v_end})")
        t1, t2 = st.tabs(["❌ Mistakes In View", "✅ Valid In View"])
        with t1:
            st.dataframe(m_view, use_container_width=True)
        with t2:
            st.dataframe(s_view, use_container_width=True)
