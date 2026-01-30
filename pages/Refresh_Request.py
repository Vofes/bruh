import streamlit as st
from src.refresh_logic import trigger_refresh, get_global_cooldown
from src.guide_loader import render_markdown_guide

st.set_page_config(page_title="Refresh Request", page_icon="🔄")

render_markdown_guide("RefreshRequestGude.md")
st.divider()

st.subheader("Global Sync Request")

# Check global status
is_allowed, time_left = get_global_cooldown()

if not is_allowed:
    st.error(f"🛑 **Global Cooldown Active.** The log was updated recently.")
    st.info(f"Please wait **{time_left} minutes** before anyone can request another sync.")
    st.button("🚀 Trigger Refresh", disabled=True)
else:
    st.success("✅ System ready. No active cooldown.")
    days_to_sync = st.select_slider("Days to look back:", options=[1, 2, 3, 4, 5], value=2)
    
    if st.button("🚀 Trigger Refresh"):
        with st.spinner("Dispatching GitHub Action..."):
            if trigger_refresh(days_to_sync):
                st.success("Request sent! The file will update shortly.")
                st.balloons()
                # We force a rerun to show the newly triggered cooldown
                st.rerun()
            else:
                st.error("Failed to trigger. Check GitHub Token permissions.")
