import streamlit as st
import os
import sys

# Ensure the app can find the 'src' folder
sys.path.append(os.getcwd())

try:
    from src.bruh_processor import process_bruh_logic
    from src.raw_viewer import render_raw_csv_view
    from src.guide_loader import render_markdown_guide # New Import
except ModuleNotFoundError:
    st.error("🚨 Logic modules not found. Check your 'src' folder.")
    st.stop()

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

# --- SHOW GUIDE WHEN NOT RUNNING ---
if not run:
    render_markdown_guide("botcheck_guide.md")
# ... [sidebar and run logic] ...

if run:
    res_m, res_s, found, last_val, unique_count = process_bruh_logic(df, start_bruh, end_bruh, jump_limit, hide_invalid)
    
    # CALCULATE THE DISQUALIFIED BRUHS
    # These are messages that were jumps but accepted by consensus
    disqualified_jumps = res_m[res_m["Reason"].str.contains("Jump", na=False)]

    st.header("📊 Global Analysis")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Final Chain Num", last_val if found else "N/A")
    m2.metric("Total Successes", unique_count)
    m3.metric("Disqualified Jumps", len(disqualified_jumps))
    m4.metric("Total Errors", len(res_m) - len(disqualified_jumps))

    st.divider()

    t1, t2, t3, t4 = st.tabs(["✅ Unique Bruhs", "🚫 Disqualified Jumps", "🛠️ Rollback History", "❌ Other Errors"])
    
    with t1:
        st.dataframe(res_s[res_s["Status"] == "CORRECT"], use_container_width=True)
    with t2:
        st.warning(f"These {len(disqualified_jumps)} bruhs were accepted as the new counter but the authors received NO CREDIT because they jumped.")
        st.dataframe(disqualified_jumps, use_container_width=True)
    with t3:
        st.dataframe(res_s[res_s["Status"] == "CORRECT-FIX"], use_container_width=True)
    with t4:
        # Show errors that AREN'T jumps (2-person rule, no consensus, etc.)
        other_errors = res_m[~res_m["Reason"].str.contains("Jump", na=False)]
        st.dataframe(other_errors, use_container_width=True)
