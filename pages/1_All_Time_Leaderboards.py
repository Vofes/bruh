import streamlit as st
import pandas as pd
import re
import sys
from pathlib import Path

# 1. Setup Pathing
root = Path(__file__).parents[1]
sys.path.append(str(root))
from app import load_data

st.set_page_config(page_title="The Archive of Honor", page_icon="🏆", layout="wide")

st.title("🏆 All-Time Leaderboards")
df = load_data()

# --- FILTERS (Logic for both Leaderboard and Debug) ---
st.sidebar.header("🛠️ Global Filters")
exclude_trigger = st.sidebar.text_input("Exclusion Filter (Contains)", value="---", help="Messages containing this will be ignored.")
include_trigger = st.sidebar.text_input("Inclusion Filter (Required)", value="", help="If set, messages must contain this to be counted.")

# Apply Filters to the dataframe
processed_df = df.copy()
processed_df['Content'] = processed_df['Content'].astype(str)

if exclude_trigger:
    processed_df = processed_df[~processed_df['Content'].str.contains(exclude_trigger, regex=False)]
if include_trigger:
    processed_df = processed_df[processed_df['Content'].str.contains(include_trigger, regex=False)]

# --- MAIN TABS ---
tab_raw, tab_valid = st.tabs(["🥇 Raw Leaderboard", "⚖️ Valid Bruh Count"])

with tab_raw:
    pattern = r'(?i)^bruh\s+(\d+)$'
    raw_bruhs = processed_df[processed_df['Content'].str.match(pattern, na=False)].copy()
    
    raw_lb = raw_bruhs.groupby('Author').size().reset_index(name='Bruh Count').sort_values(by='Bruh Count', ascending=False)
    
    st.dataframe(raw_lb, use_container_width=True, hide_index=True)

with tab_valid:
    st.info("### 🏗️ Under Development")

st.divider()

# --- DEBUG & AUDIT SECTION ---
st.header("🔍 Debugging & Audit Tool")
st.write("Use this to verify why certain messages were or weren't counted.")

# 1. User Specific Lookup
target_user = st.selectbox("Select User to Audit", options=[""] + sorted(df['Author'].unique().tolist()))

if target_user:
    user_all_msgs = df[df['Author'] == target_user].copy()
    
    # Identify which ones passed the "Bruh" pattern
    user_all_msgs['Was Counted'] = user_all_msgs['Content'].str.match(r'(?i)^bruh\s+(\d+)$', na=False)
    
    # Identify which ones were filtered out by Include/Exclude
    if exclude_trigger:
        user_all_msgs['Passed Filter'] = ~user_all_msgs['Content'].str.contains(exclude_trigger, regex=False)
    else:
        user_all_msgs['Passed Filter'] = True

    st.subheader(f"Audit Log for {target_user}")
    
    # Highlight the rows: Green for counted, Red for ignored
    def color_rows(row):
        if row['Was Counted'] and row['Passed Filter']:
            return ['background-color: rgba(0, 255, 0, 0.1)'] * len(row)
        return ['background-color: rgba(255, 0, 0, 0.05)'] * len(row)

    st.dataframe(user_all_msgs.style.apply(color_rows, axis=1), use_container_width=True)

# 2. CSV Download of the Processed Data
st.subheader("📥 Export Debug Data")
csv = processed_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download Processed CSV (Filtered)",
    data=csv,
    file_name='debug_bruh_log.csv',
    mime='text/csv',
    use_container_width=True
)
