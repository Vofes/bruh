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

    # A. THE SLIDER (Filter based on % of total server messages)
    st.write("#### 🎚️ Population Filter")
    threshold = st.slider(
        "Minimum Bruh Density (%)", 
        min_value=0.000, 
        max_value=5.000, 
        value=0.100, 
        step=0.001,
        format="%.3f%%",
        help="Filters out users who haven't contributed at least this % of the total 'bruhs' in the database."
    )

    # B. GET DATA & APPLY FILTER
    full_lb = get_static_raw_leaderboard(df)
    
    # Filter by percentage threshold
    lb = full_lb[full_lb['Bruh_Percentage'] >= threshold].copy()
    
    # C. RANKING (Based on Command_Count)
    lb = lb.sort_values(by='Command_Count', ascending=False).reset_index(drop=True)
    lb.insert(0, 'Rank', range(1, len(lb) + 1))

    # D. PODIUM LOGIC
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
                st.caption(f"Density: {row['Bruh_Percentage']:.3f}% | Mentions: {int(row['Total_Mentions']):,}")

    st.divider()


    
    # E. MAIN TABLE
    st.dataframe(
        lb, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", format="#%d"),
            "Author": "Legend Name",
            "Command_Count": st.column_config.NumberColumn("Bruh [Number] Count", format="%d"),
            "Bruh_Percentage": st.column_config.NumberColumn("Density", format="%.3f%%"),
            "Total_Mentions": "Any 'Bruh' Mention"
        }
    )

# --- TAB 2: VALID LEADERBOARD ---
with tab_valid:
    st.header("⚖️ Validated Hall")
    st.info("### 🏗️ Under Development")
    st.write("Specific 'Valid' guide and anti-spam rankings coming soon.")

st.divider()


# ... (Keep existing imports) ...
import plotly.express as px

with tab_raw:
    with st.expander("❓ How are Raw Bruhs counted?"):
        render_markdown_guide("Raw_AllTime_Leaderboard_Guide.md")

    st.markdown("### *The Raw Leaderboards*")

    # SUB-NAVIGATION for Raw Tab
    view_mode = st.radio("Select View:", ["🏆 Rankings", "📊 Analytics"], horizontal=True)

    lb_data = get_static_raw_leaderboard(df)

    if view_mode == "🏆 Rankings":
        # ... (Insert your existing Slider, Podium, and Dataframe code here) ...
        # Ensure you use 'lb_data' as the source
        st.write("Displaying Table View...") # Placeholder for your existing code
        
    else:
        st.subheader("📈 Community Analytics")
        
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            # INTERACTIVE PIE CHART
            from src.raw_leaderboard_logic import get_bruh_pie_chart
            pie_fig = get_bruh_pie_chart(lb_data)
            st.plotly_chart(pie_fig, use_container_width=True)
            
        with col_right:
            # TOTAL COMMUNITY STATS
            total_bruhs = lb_data['Command_Count'].sum()
            total_users = len(lb_data)
            st.metric("Total Community Bruhs", f"{total_bruhs:,}")
            st.metric("Active Bruh-ers", total_users)
            st.info("Hover over the chart to see specific counts and percentages!")


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
            st.write(f"Showing filtered results for {target_user} (Capped at last 500):")
            st.dataframe(audit_df, use_container_width=True)
            
            csv = audit_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Filtered Audit CSV", data=csv, file_name=f"{target_user}_audit.csv")
    elif pwd_input:
        st.error("Incorrect Password")
