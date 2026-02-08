import streamlit as st
import sys
from pathlib import Path

# --- 1. SETUP & PATHING ---
root = Path(__file__).parents[1]
sys.path.append(str(root))

from app import load_data
from src.raw_leaderboard_logic import get_static_raw_leaderboard, run_debug_audit
from src.guide_loader import render_markdown_guide

st.set_page_config(page_title="All Time Leaderboards", page_icon="🏆", layout="wide")

st.title("🏆 All-Time Leaderboards")
df = load_data()

# --- 2. TAB NAVIGATION ---
tab_raw, tab_valid = st.tabs(["🥇 Raw Leaderboard", "⚖️ Valid Bruh Count"])

# --- TAB 1: RAW LEADERBOARD ---
with tab_raw:
    # Tab-Specific Guide
    with st.expander("❓ How are Raw Bruhs counted?"):
        render_markdown_guide("Raw_AllTime_Leaderboard_Guide.md")

    st.markdown("### *The Raw Leaderboards*")
    
    # Get Data
    lb = get_static_raw_leaderboard(df)
    
    # Add Rank Column (Based on Command_Count)
    lb = lb.sort_values(by='Command_Count', ascending=False).reset_index(drop=True)
    lb.insert(0, 'Rank', range(1, len(lb) + 1))

    # Podium Logic
    top_3 = lb.head(3)
    if not top_3.empty:
        m1, m2, m3 = st.columns(3)
        medals = [
            {"icon": "🥇", "color": "#FFD700"},
            {"icon": "🥈", "color": "#C0C0C0"},
            {"icon": "🥉", "color": "#CD7F32"}
        ]
        
        cols = [m1, m2, m3]
        for i in range(len(top_3)):
            with cols[i]:
                meta = medals[i]
                row = top_3.iloc[i]
                st.markdown(
                    f"<h2 style='text-align: center; color: {meta['color']};'>{meta['icon']} {row['Author']}</h2>", 
                    unsafe_allow_html=True
                )
                st.metric(label="Raw Count", value=f"{int(row['Command_Count']):,}")
                st.caption(f"Total 'bruh' mentions: {int(row['Total_Mentions']):,}")

    st.divider()
    
    # Main Table with Rank
    st.dataframe(
        lb, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", format="#%d"),
            "Author": "Legend Name",
            "Command_Count": "Bruh [Number] Count",
            "Total_Mentions": "Any 'Bruh' Mention"
        }
    )

# --- TAB 2: VALID LEADERBOARD ---
with tab_valid:
    # Future tab-specific guide could go here
    st.header("⚖️ Validated Hall")
    st.info("### 🏗️ Under Development")
    st.write("Specific 'Valid' guide and rankings coming soon.")

st.divider()

# --- 3. SECURE SYSTEM ACCESS (Audit Tools) ---
with st.expander("🔐 System Access & Debug Tools"):
    pwd_input = st.text_input("Enter Master Password", type="password")
    
    if pwd_input == st.secrets["MPASSWORD"]:
        st.success("Access Granted")
        
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            ex_filter = st.text_input("Debug Exclusion", value="---")
        with c2:
            in_filter = st.text_input("Debug Inclusion")
        with c3:
            show_counted = st.checkbox("Show successfully counted messages", value=True)

        target_user = st.selectbox("Select User to Audit", options=[""] + sorted(df['Author'].unique().tolist()))

        if target_user:
            audit_df = run_debug_audit(df, target_user, ex_filter, in_filter, show_counted)
            st.write(f"Showing filtered results for {target_user}:")
            st.dataframe(audit_df, use_container_width=True)
            
            csv = audit_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Filtered Audit CSV", data=csv, file_name=f"{target_user}_audit.csv")
    elif pwd_input:
        st.error("Incorrect Password")
