import streamlit as st
import sys
from pathlib import Path

# Pathing to find /src/
root = Path(__file__).parents[1]
sys.path.append(str(root))

from app import load_data
from src.raw_leaderboard_logic import process_bruh_data, audit_user_messages

st.set_page_config(page_title="The Archive of Honor", page_icon="🏆", layout="wide")

# Sidebar Filters
st.sidebar.header("🛠️ Global Filters")
ex_trigger = st.sidebar.text_input("Exclusion Filter (Contains)", value="---")
in_trigger = st.sidebar.text_input("Inclusion Filter (Required)", value="")

# 1. Get Data
df = load_data()

# 2. Get Brains to process logic
leaderboard, processed_df, pattern = process_bruh_data(df, ex_trigger, in_trigger)

# --- DISPLAY ---
st.title("🏆 All-Time Leaderboards")
t1, t2 = st.tabs(["🥇 Raw Leaderboard", "⚖️ Valid Bruh Count"])

with t1:
    st.dataframe(leaderboard, use_container_width=True, hide_index=True)

with t2:
    st.info("### 🏗️ Under Development")

st.divider()

# --- AUDIT TOOL ---
st.header("🔍 Debugging & Audit Tool")
target_user = st.selectbox("Select User to Audit", options=[""] + sorted(df['Author'].unique().tolist()))

if target_user:
    audit_df = audit_user_messages(df, target_user, pattern, ex_trigger, in_trigger)
    
    def color_audit(row):
        color = 'background-color: rgba(0, 255, 0, 0.1)' if row['COUNTED?'] else 'background-color: rgba(255, 0, 0, 0.05)'
        return [color] * len(row)

    st.dataframe(audit_df.style.apply(color_audit, axis=1), use_container_width=True)

# Download Button
st.download_button("📥 Download Filtered CSV", data=processed_df.to_csv(index=False), file_name="debug_log.csv")
