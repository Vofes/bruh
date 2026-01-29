import streamlit as st
from src.engine import run_botcheck_logic

st.set_page_config(page_title="Bruh-BotCheck Validator", page_icon="🤖", layout="wide")

if 'df' not in st.session_state:
    st.error("⚠️ No data found. Please return to the Home page to sync.")
    st.stop()

df = st.session_state['df']

# SIDEBAR CONTROLS
with st.sidebar:
    st.header("⚙️ BotCheck Config")
    start_bruh = st.number_input("Starting Bruh #", value=311925)
    end_bruh = st.number_input("Ending Bruh # (0 for End of File)", value=0)
    
    st.divider()
    st.subheader("Viewport Control")
    show_raw = st.checkbox("Show Raw Data", value=True)
    
    # NEW: Using boxes instead of a slider
    v_start = st.number_input("View Start Row", value=0, min_value=0, max_value=len(df))
    v_end = st.number_input("View End Row", value=min(10000, len(df)), min_value=0, max_value=len(df))
    
    run = st.button("🚀 Run Full BotCheck", use_container_width=True)

# --- NEW: GUIDE (Only shows if 'run' hasn't been clicked) ---
if not run:
    st.title("📖 How to use Bruh-BotCheck")
    
    with st.expander("🚀 Quick Start Guide", expanded=True):
        st.markdown("""
        1. **Set your Anchor:** Enter the **Starting Bruh #** in the sidebar. The bot will verify the 10 numbers before it to ensure it's not a troll.
        2. **Set your Goal:** Enter an **Ending Bruh #**. If you leave it at `0`, the bot scans everything until the most recent message.
        3. **Adjust Viewport:** Use the **Start/End Row** boxes to focus on a specific part of the CSV (e.g., if you know a mistake happened around row 50,000).
        4. **Run:** Click the 'Run' button. 
        """)
    
    st.info("💡 Pro Tip: The 'View Start/End' boxes only change what you SEE. The BotCheck always scans the WHOLE file logic-wise.")

# RESULTS
if run:
    with st.spinner("🧠 Scanning global sequence for anomalies..."):
        # Update call to engine to include end_bruh
        res_m, res_s, found, last_val = run_botcheck_logic(df, start_bruh, end_bruh)
    
    if found:
        st.success(f"**Verification Complete.** Sequence currently ends at: **{last_val}**")
    else:
        st.error(f"**Anchor Rejected.** Sequence {start_bruh-10} to {start_bruh-1} not found in history.")

    # Apply Viewport Filter
    m_view = res_m[(res_m['Line'] >= v_start) & (res_m['Line'] <= v_end)] if not res_m.empty else res_m
    s_view = res_s[(res_s['Line'] >= v_start) & (res_s['Line'] <= v_end)] if not res_s.empty else res_s

    col1, col2 = st.columns([1, 1]) if show_raw else (st.container(), None)
    
    with col1:
        if show_raw: st.subheader("📄 Raw Log")
        st.dataframe(df.iloc[v_start:v_end, [1, 3]], use_container_width=True, height=500)
    
    if col2:
        with col2:
            st.subheader("📊 BotCheck Results")
            tab1, tab2 = st.tabs(["❌ Mistakes", "✅ Valid Log"])
            tab1.dataframe(m_view, use_container_width=True)
            tab2.dataframe(s_view, use_container_width=True)
