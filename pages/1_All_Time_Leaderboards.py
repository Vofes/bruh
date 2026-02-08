import streamlit as st
import sys
from pathlib import Path

# Pathing to find /src/
root = Path(__file__).parents[1]
sys.path.append(str(root))

from app import load_data
from src.raw_leaderboard_logic import process_bruh_data, audit_user_messages

st.set_page_config(page_title="The Archive of Honor", page_icon="🏆", layout="wide")

# 1. Load Data
df = load_data()

st.title("🏆 All-Time Leaderboards")
st.markdown("---")

# --- DEBUG & FILTER SECTION (Now in a closable box at the bottom) ---
# We define these variables first so the Leaderboard can use them
with st.expander("🛠️ Debug Settings & Audit Tools", expanded=False):
    st.subheader("Global Filters")
    col_a, col_b = st.columns(2)
    with col_a:
        ex_trigger = st.text_input("Exclusion Filter (Contains)", value="---")
    with col_b:
        in_trigger = st.text_input("Inclusion Filter (Required)", value="")

    st.divider()
    
    st.subheader("User Auditor")
    target_user = st.selectbox("Select User to Audit", options=[""] + sorted(df['Author'].unique().tolist()))
    
    # Process data with current filters
    leaderboard, processed_df, pattern = process_bruh_data(df, ex_trigger, in_trigger)

    if target_user:
        audit_df = audit_user_messages(df, target_user, pattern, ex_trigger, in_trigger)
        
        def color_audit(row):
            color = 'background-color: rgba(0, 255, 0, 0.1)' if row['COUNTED?'] else 'background-color: rgba(255, 0, 0, 0.05)'
            return [color] * len(row)

        st.dataframe(audit_df.style.apply(color_audit, axis=1), use_container_width=True)

    st.download_button("📥 Download Filtered CSV for Debug", data=processed_df.to_csv(index=False), file_name="debug_log.csv")

# --- MAIN LEADERBOARD DISPLAY ---
# (Note: This is below the logic but visually at the top of the app)
t1, t2 = st.tabs(["🥇 Raw Leaderboard", "⚖️ Valid Bruh Count"])

with t1:
    st.header("The Raw Archive")
    st.caption(f"Currently filtering out messages containing: '{ex_trigger}'" if ex_trigger else "No exclusion filters active.")
    st.dataframe(leaderboard, use_container_width=True, hide_index=True)

with t2:
    st.info("### 🏗️ Under Development")
    st.write("This tab will eventually house the filtered, anti-spam rankings.")
