import streamlit as st
from src.refresh_logic import trigger_refresh, get_global_cooldown
from src.guide_loader import render_markdown_guide
from datetime import datetime

st.set_page_config(page_title="Refresh Request", page_icon="🔄")

# Try to load your guide
try:
    render_markdown_guide("RefreshRequest_GuIde.md")
except:
    st.info("Loading Guide...")

st.divider()

# Get the actual status from Dropbox
is_allowed, time_left, last_mod = get_global_cooldown()

st.subheader("System Sync Status")

if last_mod:
    st.write(f"📂 **Last Dropbox Update:** {last_mod.strftime('%Y-%m-%d %H:%M:%S')} UTC")

if not is_allowed:
    st.error(f"🛑 **Global Cooldown:** Please wait {time_left} minutes.")
    st.button("🚀 Trigger Refresh", disabled=True)
else:
    st.success("✅ System Ready for Sync")
    days = st.select_slider("Lookback Days:", options=[1,2,3,4,5], value=2)
    
    if st.button("🚀 Trigger Refresh"):
        if trigger_refresh(days):
            st.success("Request sent to GitHub! Refreshing UI...")
            st.balloons()
            st.rerun()
        else:
            st.error("GitHub Action failed to start.")
