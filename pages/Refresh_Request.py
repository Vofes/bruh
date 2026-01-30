import streamlit as st
from src.refresh_logic import trigger_refresh, get_global_cooldown
from src.guide_loader import render_markdown_guide
from datetime import datetime, timezone

st.set_page_config(page_title="Refresh Request", page_icon="🔄", layout="centered")

# Load guide
try:
    render_markdown_guide("RefreshRequestGude.md")
except:
    st.warning("Manual Sync Guide loading...")

st.divider()

# Get the backend data
is_allowed, time_left, last_mod, debug_info = get_global_cooldown()

# --- TOP METRIC BAR ---
st.subheader("System Status")
m1, m2, m3 = st.columns(3)

with m1:
    status = "Ready" if is_allowed else "Cooling Down"
    st.metric("System State", status)

with m2:
    if last_mod:
        # Shows time in HH:MM format
        st.metric("Last File Sync (UTC)", last_mod.strftime("%H:%M"))
    else:
        st.metric("Last File Sync", "Offline")

with m3:
    st.metric("Cooldown", f"{time_left} mins" if not is_allowed else "0 mins")

# --- DEBUG SECTION ---
with st.expander("🛠️ Developer Debug Logs"):
    st.json(debug_info)
    if debug_info.get("error"):
        st.error(f"Logic Error: {debug_info['error']}")

st.divider()

# --- REFRESH ACTION SECTION ---

if not is_allowed:
    st.info(f"🕒 System cooling down. Available in **{time_left} minutes**.")
    st.button("🚀 Trigger Refresh", disabled=True, use_container_width=True)
else:
    days = st.select_slider("Select lookback range:", options=[1, 2, 3, 4, 5], value=2)
    
    if st.button("🚀 Trigger Refresh", use_container_width=True):
        # IMMEDIATE LOCAL LOCK
        st.session_state['just_triggered'] = True
        st.session_state['click_time'] = datetime.now(timezone.utc)
        
        with st.spinner("Initializing GitHub Workflow..."):
            if trigger_refresh(days):
                st.toast("Success! The update is now in progress.")
                st.balloons()
                # We rerun to ensure the UI immediately shows the 'disabled' button
                st.rerun()
            else:
                # Reset lock if GitHub fails
                st.session_state['just_triggered'] = False
                st.error("GitHub Dispatch failed.")
