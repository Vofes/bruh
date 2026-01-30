import streamlit as st
from src.refresh_logic import trigger_refresh, get_global_cooldown
from src.guide_loader import render_markdown_guide
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="Refresh Request", page_icon="🔄")

# 1. INITIALIZE LOCAL LOCK IN SESSION STATE
if 'local_lock_until' not in st.session_state:
    st.session_state['local_lock_until'] = datetime.now(timezone.utc)

# 2. GET GLOBAL STATUS (Includes Global Lock and CSV Cooldown)
# Returns: is_allowed, is_syncing, time_left_global, last_mod, debug
is_allowed, is_syncing, time_left_global, last_mod, debug = get_global_cooldown()

# 3. CALCULATE LOCAL LOCK SECONDS
now = datetime.now(timezone.utc)
seconds_remaining_local = int((st.session_state['local_lock_until'] - now).total_seconds())
local_lock_active = seconds_remaining_local > 0

st.title("🔄 Refresh Request Hub")

# 4. AUTHORIZATION TIERS & GUIDES
tier = st.radio("Access Level:", ["Normal", "Authorized Personnel"], horizontal=True)

if tier == "Authorized Personnel":
    pwd = st.text_input("Enter APASSWORD:", type="password")
    if pwd == st.secrets.get("APASSWORD"):
        st.success("Authorized: 28-Day Access Granted")
        max_days, is_authorized, guide_file = 28, True, "ARefreshRequest_Guide.md"
    else:
        max_days, is_authorized, guide_file = 7, False, "NRefreshRequest_Guide.md"
        if pwd: st.error("Invalid Password")
else:
    max_days, is_authorized, guide_file = 7, True, "NRefreshRequest_Guide.md"

# 5. RENDER THE CORRECT MARKDOWN
try:
    render_markdown_guide(guide_file)
except:
    st.caption(f"Guide '{guide_file}' not found.")

st.divider()

# 6. STATUS METRICS
m1, m2 = st.columns(2)

with m1:
    if is_syncing:
        st.warning("⏳ **Syncing in Progress...**")
    elif not is_allowed:
        st.error(f"🛑 **Cooldown:** {time_left_global}m remaining")
    else:
        st.success("✅ **System Ready**")

with m2:
    # Ensure Last Sync displays even during cooldowns
    if last_mod:
        # We use a custom string to ensure it doesn't revert to "Offline"
        st.metric("Last Data Update", last_mod.strftime("%H:%M UTC"))
    else:
        st.metric("Last Data Update", "Pending...")

# 7. THE TRIGGER BUTTON WITH DYNAMIC TEXT
st.divider()
days = st.select_slider("Select Lookback (Days):", options=list(range(1, max_days + 1)), value=2)

# Determine Button Text and Disable Logic
if is_syncing:
    button_text = "⏳ Syncing (Please Wait)"
    btn_disabled = True
elif local_lock_active:
    button_text = f"🚀 Trigger Sync Now ({seconds_remaining_local}s)"
    btn_disabled = True
elif not is_allowed:
    button_text = f"🚀 Trigger Sync Now ({time_left_global}m)"
    btn_disabled = True
elif not is_authorized:
    button_text = "🚀 Trigger Sync Now (Login Required)"
    btn_disabled = True
else:
    button_text = "🚀 Trigger Sync Now"
    btn_disabled = False

if st.button(button_text, disabled=btn_disabled, use_container_width=True):
    # SET LOCAL LOCK IMMEDIATELY (10 Minutes)
    st.session_state['local_lock_until'] = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    if trigger_refresh(days):
        st.toast("GitHub Action Dispatched!")
        st.balloons()
        st.rerun()
    else:
        # Reset local lock if it fails
        st.session_state['local_lock_until'] = datetime.now(timezone.utc)
        st.error("GitHub Dispatch failed.")

# Auto-refresh button for users to check status
if is_syncing or local_lock_active or not is_allowed:
    st.button("🔄 Check for Update", on_click=lambda: None)

with st.expander("🛠️ Debug Info"):
    st.json(debug)
