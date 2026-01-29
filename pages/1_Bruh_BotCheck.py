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
    # THE FIX: Checkbox now controls the visibility of the RAW table
    show_raw = st.checkbox("Show Raw Data Log", value=False)
    v_start = st.number_input("View Start Row", value=400000)
    v_end = st.number_input("View End Row", value=500000)
    
    run = st.button("🚀 Run Full BotCheck", use_container_width=True)

if not run:
    st.title("📖 Bruh-BotCheck Guide")
    st.info("Set your parameters in the sidebar and click 'Run' to see results.")

if run:
    with st.spinner("🧠 Scanning sequence..."):
        res_m, res_s, found, last_val = run_botcheck_logic(df, start_bruh, end_bruh)
    
    if found:
        st.success(f"**Validated up to:** {last_val}")
    else:
        st.error(f"**Anchor rejected.** Previous 10 bruhs not found for #{start_bruh}. Check your 'Starting Bruh #' value.")

    # Filter results by viewport
    m_view = res_m[(res_m['Line'] >= v_start) & (res_m['Line'] <= v_end)] if not res_m.empty else res_m
    s_view = res_s[(res_s['Line'] >= v_start) & (res_s['Line'] <= v_end)] if not res_s.empty else res_s

    # UI LAYOUT: If show_raw is True, we split 50/50. If False, Results take 100%.
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
