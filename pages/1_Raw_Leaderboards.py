import streamlit as st
import sys
from pathlib import Path

# Add src to path
root = Path(__file__).parents[1]
sys.path.append(str(root / "src"))

from raw_leaderboard_logic import get_raw_bruh_data

st.set_page_config(page_title="Raw Leaderboards", page_icon="🏆")

st.title("🏆 Raw Leaderboards")
st.markdown("### *The All-Time Hall of Honor*")
st.write("To appear here is a mark of legendary status. Only the rawest bruhs are recorded.")

# Get link from secrets (Recommended) or hardcode
DROPBOXLINK = st.secrets["DROPBOXLINK"]

data = get_raw_bruh_data(DROPBOXLINK)

if not data.empty:
    # Highlighting the Top 3
    top_3 = data.head(3)
    cols = st.columns(3)
    
    medals = ["🥇 Gold", "🥈 Silver", "🥉 Bronze"]
    for i, col in enumerate(cols):
        if i < len(top_3):
            col.metric(label=medals[i], value=top_3.iloc[i]['Bruh Count'])
            col.caption(f"**{top_3.iloc[i]['author']}**")

    st.divider()
    
    # Full Table
    st.dataframe(data, use_container_width=True, hide_index=True)
else:
    st.info("The hall is currently empty. Waiting for legends to arrive...")
