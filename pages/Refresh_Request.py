import streamlit as st
from datetime import datetime
from src.refresh_logic import trigger_github_sync, get_file_age_minutes

st.set_page_config(page_title="Refresh Request", page_icon="🔄")

st.title("🔄 System Refresh")

# --- Anti-Spam Check ---
minutes_since_last_sync = get_file_age_minutes()
cooldown_period = 10  # 10 minutes spam protection

st.sidebar.metric("Last Sync", f"{minutes_since_last_sync} min ago")

# Selection Mode
mode = st.selectbox("Authorization Level", ["Normal User", "Authorized Admin"])

if mode == "Normal User":
    st.info(f"Normal Mode: 0-100 hours. Cooldown: {cooldown_period} mins.")
    hours = st.slider("Hours to scan back", 1, 100, 24)
    
    # Check if we are in cooldown
    if minutes_since_last_sync < cooldown_period:
        st.warning(f"⚠️ System is on cooldown. Please wait {cooldown_period - minutes_since_last_sync} more minutes.")
        st.button("Run Normal Refresh", disabled=True)
    else:
        if st.button("🚀 Run Normal Refresh"):
            if trigger_github_sync(hours):
                st.success("✅ Trigger sent! Dropbox will update in 1-2 minutes.")
                st.balloons()
            else:
                st.error("❌ GitHub API error. Check GITHUB_TOKEN in secrets.")

else:
    # Authorized Admin Mode
    st.info("Admin Mode: 0-1000 hours. Bypasses cooldown.")
    admin_password = st.text_input("Admin Password", type="password")
    hours = st.slider("Hours to scan back", 1, 1000, 500)
    
    if st.button("⚡ Force Admin Refresh"):
        if admin_password == st.secrets["REFRESH_PASSWORD"]:
            if trigger_github_sync(hours):
                st.success(f"🚀 Admin override successful! Syncing last {hours} hours.")
            else:
                st.error("❌ Trigger failed.")
        else:
            st.error("🚫 Invalid Admin Password.")
