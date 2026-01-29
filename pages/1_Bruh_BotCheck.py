import streamlit as st
from src.engine import run_botcheck_logic

st.set_page_config(page_title="Bruh-BotCheck Validator", page_icon="🔍", layout="wide")

if 'df' not in st.session_state:
    st.error("⚠️ No data found. Please return to the Home page to sync.")
    st.stop()

df = st.session_state['df']

# SIDEBAR CONTROLS
with st.sidebar:
    st.header("⚙️ BotCheck Config")
    anchor_num = st.number_input("Starting Bruh #", value=311925)
    
    st.subheader("Viewport")
    show_raw = st.checkbox("Show Raw Data", value=True)
    v_range = st.slider("Select Row Range", 0, len(df), (0, min(10000, len(df))))
    
    run = st.button("🚀 Run Full BotCheck", use_container_width=True)

# RESULTS
if run:
    with st.spinner("🧠 Scanning global sequence for anomalies..."):
        res_m, res_s, found, last_val = run_botcheck_logic(df, anchor_num)
    
    if found:
        st.success(f"**Verification Complete.** Sequence currently ends at: **{last_val}**")
    else:
        st.error(f"**Anchor Rejected.** Sequence {anchor_num-10} to {anchor_num-1} not found in history.")

    # Apply Viewport Filter
    m_view = res_m[(res_m['Line'] >= v_range[0]) & (res_m['Line'] <= v_range[1])]
    s_view = res_s[(res_s['Line'] >= v_range[0]) & (res_s['Line'] <= v_range[1])]

    col1, col2 = st.columns([1, 1]) if show_raw else (st.container(), None)
    
    with col1:
        if show_raw: st.subheader("📄 Raw Log")
        st.dataframe(df.iloc[v_range[0]:v_range[1], [1, 3]], use_container_width=True, height=500)
    
    if col2:
        with col2:
            st.subheader("📊 BotCheck Results")
            tab1, tab2 = st.tabs(["❌ Mistakes", "✅ Valid Log"])
            tab1.dataframe(m_view, use_container_width=True)
            tab2.dataframe(s_view, use_container_width=True)
