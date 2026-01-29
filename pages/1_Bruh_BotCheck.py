import streamlit as st
import os
from src.engine import run_botcheck_logic

st.set_page_config(page_title="Bruh-BotCheck Validator", page_icon="🤖", layout="wide")

# Helper function to read the markdown guide
def load_guide(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "⚠️ Guide file not found. Please check the 'guides' folder."

if 'df' not in st.session_state:
    st.error("⚠️ No data found. Please return to the Home page to sync.")
    st.stop()

df = st.session_state['df']

with st.sidebar:
    st.header("⚙️ BotCheck Config")
    start_bruh = st.number_input("Starting Bruh #", value=311925)
    end_bruh = st.number_input("Ending Bruh # (0 for End)", value=0)
    jump_limit = st.number_input("Max Jump Allowed", value=1500)
    
    st.divider()
    st.subheader("Viewport Control")
    show_raw = st.checkbox("Show Raw Data Log", value=False)
    v_start = st.number_input("View Start Row", value=400000)
    v_end = st.number_input("View End Row", value=500000)
    
    run = st.button("🚀 Run Full BotCheck", use_container_width=True)

# --- DISPLAY THE EXTERNAL GUIDE ---
if not run:
    # FILE LOCATION: Update the string below if you rename your folder or file
    guide_path = "guides/botcheck_guide.md" 
    
    guide_content = load_guide(guide_path)
    st.markdown(guide_content)

if run:
    with st.spinner("🧠 Scanning sequence..."):
        res_m, res_s, found, last_val = run_botcheck_logic(df, start_bruh, end_bruh, jump_limit)
    
    if found:
        st.success(f"**Validated up to:** {last_val}")
    else:
        st.error(f"**Anchor rejected.** Previous 10 bruhs not found for #{start_bruh}.")

    m_view = res_m[(res_m['Line'] >= v_start) & (res_m['Line'] <= v_end)] if not res_m.empty else res_m
    s_view = res_s[(res_s['Line'] >= v_start) & (res_s['Line'] <= v_end)] if not res_s.empty else res_s

    if show_raw:
        col_raw, col_res = st.columns([1, 1])
        with col_raw:
            st.subheader("📄 Raw Log")
            st.dataframe(df.iloc[v_start:v_end, [1, 3]], use_container_width=True, height=600)
        res_container = col_res
    else:
        res_container = st.container()

    with res_container:
        st.subheader("📊 BotCheck Results")
        t1, t2 = st.tabs(["❌ Mistakes", "✅ Valid"])
        with t1:
            st.metric("Mistakes in View", len(m_view))
            st.dataframe(m_view, use_container_width=True)
        with t2:
            st.metric("Valid Bruhs in View", len(s_view))
            st.dataframe(s_view, use_container_width=True)
