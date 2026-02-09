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
    # 1. Guide at top
    with st.expander("❓ How are Raw Bruhs counted?"):
        render_markdown_guide("Raw_AllTime_Leaderboard_Guide.md")

    # 2. View Switcher at the top
    view_mode = st.radio("Select View Type:", ["🏆 Rankings Table", "📊 Analytics Graph"], horizontal=True)
    st.divider()

    # Get data from Brain
    full_lb = get_static_raw_leaderboard(df)

    if view_mode == "🏆 Rankings Table":
        # Table shows EVERYONE (Threshold doesn't apply here)
        lb_display = full_lb.copy()
        lb_display = lb_display.sort_values(by='Command_Count', ascending=False).reset_index(drop=True)
        lb_display.insert(0, 'Rank', range(1, len(lb_display) + 1))

        # Podium for the top 3
        top_3 = lb_display.head(3)
        if not top_3.empty:
            m1, m2, m3 = st.columns(3)
            medals = [{"c": "#FFD700", "i": "🥇"}, {"c": "#C0C0C0", "i": "🥈"}, {"c": "#CD7F32", "i": "🥉"}]
            for i in range(len(top_3)):
                with [m1, m2, m3][i]:
                    row = top_3.iloc[i]
                    st.markdown(f"<h2 style='text-align: center; color: {medals[i]['c']};'>{medals[i]['i']} {row['Author']}</h2>", unsafe_allow_html=True)
                    st.metric("Raw Bruhs", f"{int(row['Command_Count']):,}")
                    st.caption(f"Density: {row['Bruh_Percentage']:.3f}%")

        st.write("### Full Standings")
        st.dataframe(
            lb_display, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", format="#%d"),
                "bruh-er": "User",
                "Raw Bruhs": "Raw Bruhs",
                "Bruh_Percentage": st.column_config.NumberColumn("Density", format="%.3f%%"),
                "Total_Mentions": "Any 'Bruh' Mention"
            }
        )

    else:
            # Analytics View
            st.subheader("📊 Community Distribution")
        
            st.info("Users below the threshold will be grouped into 'Others'.")
        
        # Updated Range: 0.25% to 2.0%
            chart_threshold = st.slider(
                "Min Density for Chart (%)", 
                min_value=0.250, 
                max_value=2.000, 
                value=0.500, # Default starting point
                step=0.001, 
                format="%.3f%%"
            )
        
            c_left, c_right = st.columns([2, 1])
            with c_left:
            # This now correctly bundles everyone below threshold into "Others"
                fig = get_bruh_pie_chart(full_lb, chart_threshold)
                st.plotly_chart(fig, use_container_width=True)
        
            with c_right:
                st.metric("Global Raw Bruhs", f"{int(full_lb['Command_Count'].sum()):,}")
                st.metric("Total bruh-ers", len(full_lb))


# --- TAB 2: VALID LEADERBOARD ---
with tab_valid:
    st.header("⚖️ Validated Hall")
    st.info("🏗️ Under Development: Anti-spam filters coming soon.")

st.divider()

# --- 3. SECURE SYSTEM ACCESS ---
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
    elif pwd:
        st.error("Invalid Password")
