import streamlit as st
from src.refresh_logic import trigger_refresh, get_global_cooldown
from src.guide_loader import render_markdown_guide
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="Refresh Request", page_icon="🔄")

# --- 1. LOCAL LOCK INITIALIZATION ---
# This lock stays active for 10 minutes or until the browser tab is closed.
if 'local_lock_until' not in st.session_state:
    st.session_state['local_lock_until'] = datetime.now(timezone.utc)

# --- 2. DATA FETCH & AUTO-REFRESH ---
is_allowed, is_syncing, time_left, last_mod, debug_info = get_global_cooldown()

# Calculate local lock time
now = datetime.now(timezone.utc)
local_seconds_left = int((st.session_state['local_lock_until'] - now).total_seconds())
local_locked = local_seconds_left > 0

# --- 3. UI LAYOUT: HEADER & REFRESH ---
st.title("🔄 Data Refresh Hub")

# Move Refresh Button Upwards as requested
if st.button("🛰️ Update System Status", use_container_width=True):
    st.rerun()

# --- 4. TIER SELECTION ---
tier = st.radio("Access Level:", ["Normal", "Authorized Personnel"], horizontal=True)

max_days = 7
guide_file = "NRefreshRequest_Guide.md"
authorized = True

if tier == "Authorized Personnel":
    pwd = st.text_input("Enter APASSWORD:", type="password")
    if pwd == st.secrets.get("APASSWORD"):
        st.success("Authorized: 30-Day Range Unlocked")
        max_days = 30 # Corrected to 30
        guide_file = "ARefreshRequest_Guide.md"
    else:
        authorized = False
        if pwd: st.error("Incorrect Password")

# --- 5. RENDER MARKDOWN (Restored) ---
try:
    render_markdown_guide(guide_file)
except Exception as e:
    st.caption(f"Guide Loader Note: {e}")

st.divider()

# --- 6. STATUS METRICS ---
c1, c2 = st.columns(2)
with c1:
    if is_syncing:
        st.warning("⏳ **Global Syncing...**")
    elif local_locked:
        st.info(f"🔒 **Request Sent ({local_seconds_left}s)**")
    elif not is_allowed:
        st.error(f"🛑 **Cooldown:** {time_left}m")
    else:
        st.success("✅ **System Ready**")

with c2:
    if last_mod:
        st.metric("Last Update (UTC)", last_mod.strftime("%H:%M"))
    else:
        st.metric("Last Update", "Offline")

# --- 7. THE TRIGGER ---
st.divider()
days = st.select_slider("Select Lookback (Days):", range(1, max_days + 1), value=2)

# Logic for Button Text and Disable State
if is_syncing:
    btn_label, btn_dis = "⏳ Global Sync in Progress", True
elif local_locked:
    btn_label, btn_dis = f"✅ Instruction Sent ({local_seconds_left}s)", True
elif not is_allowed:
    btn_label, btn_dis = f"🛑 Cooldown ({time_left}m)", True
elif not authorized:
    btn_label, btn_dis = "🔒 Authorized Personnel Only", True
else:
    btn_label, btn_dis = "🚀 Trigger Sync Now", False

if st.button(btn_label, disabled=btn_dis, use_container_width=True):
    # ACTIVATE LOCAL LOCK IMMEDIATELY
    st.session_state['local_lock_until'] = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    if trigger_refresh(days):
        st.toast("Instruction received! GitHub Action starting...")
        st.balloons()
        st.rerun()
    else:
        # Reset lock if trigger fails
        st.session_state['local_lock_until'] = datetime.now(timezone.utc)
        st.error("Failed to contact GitHub.")

# --- 8. DEBUG ---
with st.expander("🛠️ Developer Debug Info"):
    st.json(debug_info)
