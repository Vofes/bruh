import streamlit as st
from src.engine import run_botcheck_logic

st.set_page_config(page_title="Bruh-BotCheck Validator", page_icon="🤖", layout="wide")

if 'df' not in st.session_state:
    st.error("⚠️ No data found. Please return to the Home page to sync.")
    st.stop()

df = st.session_state['df']

with st.sidebar:
    st.header("⚙️ BotCheck Config")
    start_bruh = st.number_input("Starting Bruh #", value=311925)
    end_bruh = st.number_input("Ending Bruh # (0 for End)", value=0)
    
    st.divider()
    st.subheader("Viewport Control")
    show_raw = st.checkbox("Show Raw Data", value=True)
    v_start = st.number_input("View Start Row", value=0, min_value=0)
    v_end = st.number_input("View End Row", value=min(10000, len(df)), min_value=0)
    
    run = st.button("🚀 Run Full BotCheck", use_container_width=True)

if not run:
    st.title("📖 Bruh-BotCheck Guide")
    with st.expander("How to use this tool", expanded=True):
        st.markdown("""
        1. **Start Bruh:** The number where you want to begin checking.
        2. **End Bruh:** Set a target number to stop at, or `0` to scan everything.
        3. **View Rows:** These boxes control which part of the file you see in the tables below.
        4. **Run:** Click the button in the sidebar to process the sequence.
        """)

if run:
    with st.spinner("🧠 Scanning sequence..."):
        res_m, res_s, found, last_val = run_botcheck_logic(df, start_bruh, end_bruh)
    
    if found:
        st.success(f"**Validated up to:** {last_val}")
    else:
        st.error(f"**Anchor rejected.** Previous 10 bruhs not found for #{start_bruh}")

    m_view = res_m[(res_m['Line'] >= v_start) & (res_m['Line'] <= v_end)] if not res_m.empty else res_m
    s_view = res_s[(res_s['Line'] >= v_start) & (res_s['Line'] <= v_end)] if not res_s.empty else res_s

    col1, col2 = st.columns([1, 1]) if show_raw else (st.container(), None)
    with col1:
        if show_raw: st.subheader("📄 Raw Log")
        st.dataframe(df.iloc[v_start:v_end, [1, 3]], use_container_width=True)
    if col2:
        with col2:
            st.subheader("📊 Results")
            t1, t2 = st.tabs(["❌ Mistakes", "✅ Valid"])
            t1.dataframe(m_view, use_container_width=True)
            t2.dataframe(s_view, use_container_width=True)
