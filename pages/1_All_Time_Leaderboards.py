import streamlit as st
import sys
from pathlib import Path

# --- 1. SETUP & PATHING ---
root = Path(__file__).parents[1]
sys.path.append(str(root))

from app import load_data
from src.raw_leaderboard_logic import get_static_raw_leaderboard, run_debug_audit, get_bruh_pie_chart
from src.guide_loader import render_markdown_guide

st.set_page_config(page_title="The Archive of Honor", page_icon="🏆", layout="wide")

st.title("🏆 All-Time Leaderboards")
df = load_data()

# --- 2. MAIN TABS ---
tab_raw, tab_valid = st.tabs(["🥇 Raw Leaderboard", "⚖️ Valid Bruh Count"])

# --- TAB 1: RAW LEADERBOARD ---

with tab_raw:
    # ... (Guide and Switcher logic) ...

    full_lb = get_static_raw_leaderboard(df)

    if view_mode == "🏆 Rankings Table":
        lb_display = full_lb.copy().sort_values(by='Raw_Bruhs', ascending=False).reset_index(drop=True)
        lb_display.insert(0, 'Rank', range(1, len(lb_display) + 1))

        # Podium
        top_3 = lb_display.head(3)
        if not top_3.empty:
            m1, m2, m3 = st.columns(3)
            medals = [{"c": "#FFD700", "i": "🥇"}, {"c": "#C0C0C0", "i": "🥈"}, {"c": "#CD7F32", "i": "🥉"}]
            for i in range(len(top_3)):
                with [m1, m2, m3][i]:
                    row = top_3.iloc[i]
                    st.markdown(f"<h2 style='text-align: center; color: {medals[i]['c']};'>{medals[i]['i']} {row['Author']}</h2>", unsafe_allow_html=True)
                    st.metric("Raw Bruhs", f"{int(row['Raw_Bruhs']):,}")
                    st.caption(f"Purity: {row['Bruh_Purity']}%")

        st.write("### Full Standings")
        
        # WE SET THE DEFAULT VISIBILITY HERE
        st.dataframe(
            lb_display, 
            use_container_width=True, 
            hide_index=True,
            # This list defines what shows up BY DEFAULT and in what order
            column_order=("Rank", "Author", "Raw_Bruhs", "Bruh_Purity", "Global_Share"),
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", format="#%d"),
                "Author": "User",
                "Raw_Bruhs": st.column_config.NumberColumn("Raw Bruhs", format="%d"),
                "Bruh_Purity": st.column_config.NumberColumn("Purity", format="%.2f%%"),
                "Global_Share": st.column_config.NumberColumn("Share", format="%.3f%%"),
                "Total_Mentions": st.column_config.NumberColumn("Total 'Bruh' Mentions", format="%d"),
                "Total_Messages": st.column_config.NumberColumn("Total Channel Messages", format="%d")
            }
        )
        st.caption("💡 Use the 'eye' icon in the table header to show hidden stats like Total Mentions.")


# --- TAB 2: VALID LEADERBOARD ---
with tab_valid:
    st.info("🏗️ Under Development")

st.divider()

# --- 3. DEBUG TOOLS ---
with st.expander("🔐 System Access & Debug Tools"):
    pwd = st.text_input("Master Password", type="password")
    if pwd == st.secrets["MPASSWORD"]:
        st.success("Access Granted")
        col1, col2, col3 = st.columns(3)
        with col1: ex = st.text_input("Exclusion Filter", value="---")
        with col2: inc = st.text_input("Inclusion Filter")
        with col3: sc = st.checkbox("Show Counted", value=True)
        
        user_list = sorted(df['Author'].unique().tolist())
        target_user = st.selectbox("Audit User", options=[""] + user_list)
        
        if target_user:
            audit_df = run_debug_audit(df, target_user, ex, inc, sc)
            st.dataframe(audit_df, use_container_width=True)
            st.download_button("📥 Download Filtered CSV", audit_df.to_csv(index=False), f"{target_user}_audit.csv")
