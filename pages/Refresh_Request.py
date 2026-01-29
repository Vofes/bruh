import streamlit as st
import time
from datetime import datetime, timedelta
from src.refresh_logic import trigger_github_sync

st.set_page_config(page_title="Refresh Request")

# --- Initialize Session State for Cooldown ---
if 'last_refresh_time' not in st.session_state:
    st.session_state['last_refresh_time'] = None

st.title("🔄 Refresh Request")

mode = st.radio("Select Mode", ["Normal", "Authorised"], horizontal=True)

# --- Logic for Normal Mode ---
if mode == "Normal":
    st.info("Normal mode allows updates for the last 0-100 hours.")
    hours = st.slider("Hours to update", 0, 100, 24)
    
    # Check cooldown (10 minutes)
    can_refresh = True
    if st.session_state['last_refresh_time']:
        elapsed = datetime.now() - st.session_state['last_refresh_time']
        if elapsed < timedelta(minutes=10):
            can_refresh = False
            remaining = 10 - int(elapsed.total_seconds() // 60)
            st.warning(f"⚠️ Please wait {remaining} minutes before refreshing again.")

    if st.button("Run Normal Refresh", disabled=not can_refresh):
        with st.spinner("Requesting sync..."):
            if trigger_github_sync(hours):
                st.session_state['last_refresh_time'] = datetime.now()
                st.success(f"✅ Sync triggered for last {hours}h! Data will update in a few minutes.")
            else:
                st.error("❌ Failed to trigger sync. Check GitHub Token.")

# --- Logic for Authorised Mode ---
else:
    st.info("Authorised mode allows updates for the last 0-1000 hours.")
    pwd = st.text_input("Enter Admin Password", type="password")
    hours = st.slider("Hours to update", 0, 1000, 500)
    
    if st.button("Run Authorised Refresh"):
        if pwd == st.secrets["REFRESH_PASSWORD"]:
            with st.spinner("Requesting deep sync..."):
                if trigger_github_sync(hours):
                    st.success(f"🚀 Admin Sync triggered for {hours}h!")
                else:
                    st.error("❌ Sync failed.")
        else:
            st.error("🚫 Incorrect Password.")
