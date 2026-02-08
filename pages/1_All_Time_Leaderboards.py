import streamlit as st
import sys
from pathlib import Path

root = Path(__file__).parents[1]
sys.path.append(str(root))

from app import load_data
from src.raw_leaderboard_logic import get_static_raw_leaderboard, run_debug_audit
from src.guide_loader import render_markdown_guide

st.set_page_config(page_title="Raw Leaderboards", page_icon="🏆", layout="wide")

# --- 1. HELP GUIDE (At the very top) ---
with st.expander("❓ How are these counted? (Click for Help)"):
    render_markdown_guide("Raw_AllTime_Leaderboard_Guide.md")

st.title("🏆 All-Time Raw Leaderboards")
st.markdown("### *The Hall of Eternal Echoes*")

df = load_data()

# --- 2. TOP 3 PODIUM (Colored Names) ---
lb = get_static_raw_leaderboard(df)
top_3 = lb.head(3).reset_index(drop=True)

if not top_3.empty:
    m1, m2, m3 = st.columns(3)
    medals = [
        {"icon": "🥇", "color": "#FFD700"},
        {"icon": "🥈", "color": "#C0C0C0"},
        {"icon": "🥉", "color": "#CD7F32"}
    ]
    
    cols = [m1, m2, m3]
    for i in range(len(top_3)):
        col = cols[i]
        meta = medals[i]
        row = top_3.iloc[i]
        
        with col:
            # Name is now colored based on rank
            st.markdown(
                f"<h2 style='text-align: center; color: {meta['color']};'>{meta['icon']} {row['Author']}</h2>", 
                unsafe_allow_html=True
            )
            # Removed "Cmds", just showing the raw number
            st.metric(label="Raw Count", value=f"{int(row['Command_Count']):,}")
            st.caption(f"Total 'bruh' mentions: {int(row['Total_Mentions']):,}")

st.divider()

# --- 3. MAIN TABLE ---
st.dataframe(lb, use_container_width=True, hide_index=True)

# --- 4. SECURE SYSTEM ACCESS (Debug Tools) ---
with st.expander("🔐 System Access & Debug Tools"):
    pwd_input = st.text_input("Enter Master Password", type="password")
    if pwd_input == st.secrets["MPASSWORD"]:
        # ... (keep the same auditor logic from previous response) ...
        st.success("Access Granted")
        # [Rest of your audit code here]
