import streamlit as st
from src.refresh_logic import trigger_refresh, get_global_cooldown
from src.guide_loader import render_markdown_guide
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="Refresh Request", page_icon="🔄")

# 1. INITIALIZE SESSION STATE FOR LOCAL LOCK
if 'local_lock_until' not in st.session_state:
    st.session_state['local_lock_until'] = datetime.now(timezone.utc)

# 2. CHECK STATUS
is_allowed, is_syncing, time_left, last_mod, debug = get_global_cooldown()

# Check if local lock is still active
seconds_remaining_local = (st.session_state['local_lock_until'] - datetime.now(timezone.utc)).total_seconds()
local_lock_active = seconds_remaining_local > 0

# 3. AUTHORIZATION TIERS
st.title("🔄 Refresh Request Hub")
tier = st.radio("Access Level:", ["Normal", "Authorized Personnel"], horizontal=True)

max_days = 7
guide_file = "NRefreshRequest_Guide.md"
is_authorized = True # Default for Normal

if tier == "Authorized Personnel":
    pwd = st.text_input("Enter APASSWORD:", type="password")
    if pwd == st.secrets.get("APASSWORD"):
        st.success("Authorization Confirmed")
        max_days = 28
        guide_file = "ARefreshRequest_Guide.md"
    else:
        is_authorized = False
        if pwd: st.error("Invalid Password")

# 4. RENDER GUIDE
try:
    render_markdown_guide(guide_file)
except:
    st.caption(f"Guide '{guide_file}' not found.")

# 5. STATUS DISPLAY
st.divider()
m1, m2 = st.columns(2)

with m1:
    if is_syncing:
        st.warning("⏳ **Currently Syncing...**")
    elif local_lock_active:
        st.info(f"🔒 Local Lock: {int(seconds_remaining_local)}s")
    elif not is_allowed:
        st.error(f"🛑 Cooldown: {time_left}m")
    else:
        st.success("✅ System Ready")

with m2:
    if last_mod:
        st.metric("Last Sync (UTC)", last_mod.strftime("%H:%M"))
    else:
        st.metric("Last Sync", "Unknown")

# 6. REFRESH BUTTON LOGIC
st.divider()
days = st.select_slider("Lookback Window (Days):", options=list(range(1, max_days + 1)), value=2)

# Disable if: Global Cooldown OR Syncing OR Local Lock OR Wrong Password
btn_disabled = (not is_allowed) or is_syncing or local_lock_active or (not is_authorized)

if st.button("🚀 Trigger Sync Now", disabled=btn_disabled, use_container_width=True):
    # Set Local Lock IMMEDIATELY (10 Minutes)
    st.session_state['local_lock_until'] = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    if trigger_refresh(days):
        st.toast("GitHub Action Dispatched!")
        st.balloons()
        st.rerun()
    else:
        # If trigger fails, release local lock so user can try again
        st.session_state['local_lock_until'] = datetime.now(timezone.utc)
        st.error("GitHub Dispatch failed.")

# Auto-refresh helper: If syncing, suggest a refresh
if is_syncing or local_lock_active:
    if st.button("🔄 Refresh Page Status"):
        st.rerun()

with st.expander("🛠️ Debug Info"):
    st.json(debug)
