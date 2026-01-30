import streamlit as st
from src.refresh_logic import trigger_refresh, get_cooldown_status
from src.guide_loader import render_markdown_guide
from datetime import datetime

st.set_page_config(page_title="Refresh Request", page_icon="🔄")

# 1. Load the Guide using your custom function
try:
    render_markdown_guide("RefreshRequest_Guide.md")
except Exception as e:
    st.error(f"Could not load guide: {e}")

st.divider()

# 2. Refresh Interface
st.subheader("Manual Data Sync")
st.info("🔄 This request updates the **test_merge.csv** file.")

# Normal requests allow 1 to 5 days
days_to_sync = st.select_slider(
    "Select lookback period (Days):",
    options=[1, 2, 3, 4, 5],
    value=2
)

can_refresh, time_left = get_cooldown_status()

if can_refresh:
    if st.button("🚀 Trigger Refresh"):
        with st.spinner("Sending request to GitHub..."):
            success = trigger_refresh(days_to_sync)
            if success:
                st.session_state['last_refresh'] = datetime.now()
                st.success("Request sent! The test file will update in 2-3 minutes.")
                st.balloons()
            else:
                st.error("Request failed. Ensure GITHUB_TOKEN and GITHUB_REPO are set in Secrets.")
else:
    st.warning(f"Cooldown Active: Please wait **{time_left} minutes** before requesting again.")
