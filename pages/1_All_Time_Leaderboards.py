import streamlit as st
import pandas as pd
import re
import sys
from pathlib import Path

# 1. Setup Pathing to reach /src/
root = Path(__file__).parents[1]
sys.path.append(str(root))

# Import your existing loader from app.py to keep data in sync
from app import load_data

st.set_page_config(page_title="The Archive of Honor", page_icon="🏆", layout="wide")

# --- TITLES ---
st.title("🏆 All-Time Leaderboards")
st.markdown("---")

# 2. Create the Navigation Tabs
tab_raw, tab_valid = st.tabs(["🥇 Raw Leaderboard", "⚖️ Valid Bruh Count"])

# Load the central data
df = load_data()

# --- TAB 1: RAW LEADERBOARD ---
with tab_raw:
    st.header("The Raw Archive")
    st.subheader("*Every 'bruh [number]' ever recorded.*")
    
    if not df.empty:
        # Regex: Case-insensitive 'bruh' + space + digits
        pattern = r'(?i)^bruh\s+(\d+)$'
        
        # Process Raw Count
        df['Content'] = df['Content'].astype(str)
        raw_bruhs = df[df['Content'].str.match(pattern, na=False)].copy()
        
        raw_leaderboard = raw_bruhs.groupby('Author').size().reset_index(name='Bruh Count')
        raw_leaderboard = raw_leaderboard.sort_values(by='Bruh Count', ascending=False)

        # Decoration for Top 3
        top_3 = raw_leaderboard.head(3)
        m1, m2, m3 = st.columns(3)
        
        with m1:
            if len(top_3) > 0:
                st.metric("🥇 1st Place", top_3.iloc[0]['Author'], f"{top_3.iloc[0]['Bruh Count']} Bruhs")
        with m2:
            if len(top_3) > 1:
                st.metric("🥈 2nd Place", top_3.iloc[1]['Author'], f"{top_3.iloc[1]['Bruh Count']} Bruhs")
        with m3:
            if len(top_3) > 2:
                st.metric("🥉 3rd Place", top_3.iloc[2]['Author'], f"{top_3.iloc[2]['Bruh Count']} Bruhs")

        st.divider()
        st.dataframe(raw_leaderboard, use_container_width=True, hide_index=True)
    else:
        st.error("No data found. Check the main page sync.")

# --- TAB 2: VALID LEADERBOARD ---
with tab_valid:
    st.header("The Validated Hall")
    st.info("### 🏗️ Under Development")
    st.write("""
    This leaderboard will filter out spam, self-responses, and broken sequences. 
    Only the most honorable 'bruhs' will be counted here.
    """)
    
    # Placeholder for the future
    st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJwamZ4emh5ZzF3eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/3o7TKSjPqcKID6nEIC/giphy.gif")
