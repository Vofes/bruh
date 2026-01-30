import streamlit as st
from src.refresh_logic import trigger_refresh, get_cooldown_status
from src.guide_loader import render_guide # Assuming this is your function
from datetime import datetime

st.set_page_config(page_title="Refresh Request", page_icon="🔄")

# 1. Load the Guide from GitHub/Local
try:
    render_guide("RefreshRequestGude.md")
except:
    st.info("Guide loading...")

st.divider()

# 2. Refresh UI
st.subheader("Manual Data Sync")
st.write("Request a fresh export from Discord. This will update the test file.")

days_to_sync = st.slider("Select days to look back:", 1, 5, 2)

can_refresh, time_left = get_cooldown_status()

if can_refresh:
    if st.button("🚀 Trigger Refresh"):
        with st.spinner("Communicating with GitHub..."):
            success = trigger_refresh(days_to_sync)
            if success:
                st.session_state['last_refresh'] = datetime.now()
                st.success(f"Refresh triggered! Check Dropbox for 'test_merge.csv' in a few minutes.")
                st.balloons()
            else:
                st.error("GitHub API rejected the request. Check your tokens.")
else:
    st.warning(f"Cooldown Active: Please wait {time_left} minutes before requesting again.")

st.info("Note: During this test phase, output is saved to `/bruh/bruh_log/test_merge.csv`.")
