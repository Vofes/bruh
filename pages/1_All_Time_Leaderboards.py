import streamlit as st
import sys
from pathlib import Path

# Setup Pathing
root = Path(__file__).parents[1]
sys.path.append(str(root))

from app import load_data
from src.raw_leaderboard_logic import get_static_raw_leaderboard, run_debug_audit

st.set_page_config(page_title="The Archive of Honor", page_icon="🏆", layout="wide")

# 1. Load Data
df = load_data()

# --- PUBLIC SECTION ---
st.title("🏆 All-Time Leaderboards")
st.markdown("---")

t1, t2 = st.tabs(["🥇 Raw Leaderboard", "⚖️ Valid Bruh Count"])

with t1:
    st.header("The Raw Archive")
    # This leaderboard is unaffected by debug filters
    lb = get_static_raw_leaderboard(df)
    st.dataframe(lb, use_container_width=True, hide_index=True)

with t2:
    st.info("### 🏗️ Under Development")

st.divider()

# --- PRIVATE DEBUG SECTION ---
st.subheader("🛠️ System Access")
pwd_input = st.text_input("Enter Master Password to access Debug Tools", type="password")

if pwd_input == st.secrets["MPASSWORD"]:
    with st.expander("🔓 Debug & Audit Console", expanded=True):
        st.warning("You are in Debug Mode. Filters below do NOT affect the main leaderboard.")
        
        col_a, col_b = st.columns(2)
        with col_a:
            ex_trigger = st.text_input("Debug Exclusion (Contains)", value="---")
        with col_b:
            in_trigger = st.text_input("Debug Inclusion (Required)", value="")

        target_user = st.selectbox("Select User to Audit", options=[""] + sorted(df['Author'].unique().tolist()))
        
        if target_user:
            audit_results = run_debug_audit(df, target_user, ex_trigger, in_trigger)
            
            def color_audit(row):
                color = 'background-color: rgba(0, 255, 0, 0.1)' if row['COUNTED?'] else 'background-color: rgba(255, 0, 0, 0.05)'
                return [color] * len(row)

            st.dataframe(audit_results.style.apply(color_audit, axis=1), use_container_width=True)
        
        # CSV Download for the current audit session
        st.download_button("📥 Download Audit Session CSV", data=df.to_csv(index=False), file_name="audit_raw_log.csv")
else:
    if pwd_input != "":
        st.error("Invalid Credentials.")
