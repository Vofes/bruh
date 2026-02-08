import streamlit as st
import sys
from pathlib import Path

root = Path(__file__).parents[1]
sys.path.append(str(root))

from app import load_data
from src.raw_leaderboard_logic import get_static_raw_leaderboard, run_debug_audit

st.set_page_config(page_title="Raw Leaderboards", page_icon="🏆", layout="wide")

df = load_data()

st.title("🏆 All-Time Raw Leaderboards")
st.markdown("### *The Hall of Eternal Echoes*")

# --- TOP 3 PODIUM ---
# --- TOP 3 PODIUM ---
lb = get_static_raw_leaderboard(df)
top_3 = lb.head(3).reset_index(drop=True) # drop=True prevents 'index' column issues

if not top_3.empty:
    m1, m2, m3 = st.columns(3)
    # Define the podium data clearly
    medals = [
        {"label": "🥇 Gold", "color": "#FFD700"},
        {"label": "🥈 Silver", "color": "#C0C0C0"},
        {"label": "🥉 Bronze", "color": "#CD7F32"}
    ]
    
    cols = [m1, m2, m3]
    
    for i in range(len(top_3)):
        col = cols[i]
        medal = medals[i]
        user_row = top_3.iloc[i]
        
        with col:
            # FIX: Changed unsafe_allow_dict to unsafe_allow_html
            st.markdown(
                f"<h3 style='text-align: center; color: {medal['color']};'>{medal['label']}</h3>", 
                unsafe_allow_html=True
            )
            st.metric(
                label=str(user_row['Author']), 
                value=f"{int(user_row['Command_Count'])} Cmds"
            )
            st.caption(f"Total 'bruh' mentions: {int(user_row['Total_Mentions'])}")
st.divider()

# --- MAIN TABLE ---
st.dataframe(
    lb, 
    use_container_width=True, 
    hide_index=True,
    column_config={
        "Author": "Legend Name",
        "Command_Count": "Bruh [Number] Count",
        "Total_Mentions": "Any 'Bruh' Mention"
    }
)

# --- SECURE SYSTEM ACCESS ---
st.write("")
with st.expander("🔐 System Access & Debug Tools"):
    pwd_input = st.text_input("Enter Master Password", type="password")
    
    if pwd_input == st.secrets["MPASSWORD"]:
        st.success("Access Granted")
        
        # Audit Controls
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            ex_filter = st.text_input("Exclusion (Exclude messages with this)")
        with c2:
            in_filter = st.text_input("Inclusion (Only messages with this)")
        with c3:
            show_counted = st.checkbox("Show successfully counted messages", value=True)

        target_user = st.selectbox("Select User to Audit", options=[""] + sorted(df['Author'].unique().tolist()))

        if target_user:
            audit_df = run_debug_audit(df, target_user, ex_filter, in_filter, show_counted)
            
            st.write(f"Showing last {len(audit_df)} filtered messages for {target_user}:")
            st.dataframe(audit_df, use_container_width=True)
            
            # Download ONLY the filtered results
            csv = audit_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Filtered Audit CSV", data=csv, file_name=f"{target_user}_audit.csv")
    elif pwd_input:
        st.error("Incorrect Password")
