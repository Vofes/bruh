import streamlit as st
from src.refresh_logic import trigger_refresh, get_global_cooldown
from src.guide_loader import render_markdown_guide
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="Refresh Request", page_icon="🔄")

# 1. INITIALIZE LOCAL LOCK
if 'local_lock_until' not in st.session_state:
    st.session_state['local_lock_until'] = datetime.now(timezone.utc)

# 2. FETCH DATA
is_allowed, is_syncing, time_left_global, last_mod, debug = get_global_cooldown()

# 3. CALCULATE LOCAL LOCK
now = datetime.now(timezone.utc)
seconds_remaining_local = int((st.session_state['local_lock_until'] - now).total_seconds())
local_lock_active = seconds_remaining_local > 0

st.title("🔄 Refresh Request Hub")

# 4. AUTH TIERS
tier = st.radio("Access Level:", ["Normal", "Authorized Personnel"], horizontal=True)
is_authorized = True
max_days = 7
guide_file = "NRefreshRequest_Guide.md"

if tier == "Authorized Personnel":
    pwd = st.text_input("Enter APASSWORD:", type="password")
    if pwd == st.secrets.get("APASSWORD"):
        st.success("Authorized")
        max_days, guide_file = 28, "ARefreshRequest_Guide.md"
    else:
        is_authorized = False
        if pwd: st.error("Invalid Password")

# 5. RENDER GUIDE
try:
    render_markdown_guide(guide_file)
except:
    st.caption("Guide loading...")

st.divider()

# 6. METRICS (Always visible)
col1, col2 = st.columns(2)
with col1:
    if is_syncing:
        st.warning("⏳ **Syncing...**")
    elif not is_allowed:
        st.error(f"🛑 **Cooldown:** {time_left_global}m")
    else:
        st.success("✅ **Ready**")

with col2:
    # This now pulls from the top-level fetch
    if last_mod:
        st.metric("Last Data Update", last_mod.strftime("%H:%M UTC"))
    else:
        st.metric("Last Data Update", "Offline")

# 7. TRIGGER BUTTON
st.divider()
days = st.select_slider("Days:", options=list(range(1, max_days + 1)), value=2)

# Logic for Button Text
if is_syncing:
    btn_text, btn_off = "⏳ Syncing...", True
elif local_lock_active:
    btn_text, btn_off = f"🚀 Trigger Sync ({seconds_remaining_local}s)", True
elif not is_allowed:
    btn_text, btn_off = f"🚀 Trigger Sync ({time_left_global}m)", True
elif not is_authorized:
    btn_text, btn_off = "🚀 Enter Password", True
else:
    btn_text, btn_off = "🚀 Trigger Sync Now", False

if st.button(btn_text, disabled=btn_off, use_container_width=True):
    # SET LOCK BEFORE TRIGGERING
    st.session_state['local_lock_until'] = datetime.now(timezone.utc) + timedelta(minutes=10)
    if trigger_refresh(days):
        st.toast("Dispatched!")
        st.balloons()
        st.rerun()
    else:
        st.session_state['local_lock_until'] = datetime.now(timezone.utc)
        st.error("Failed.")

# 8. PERMANENT REFRESH BUTTON (Always visible if any lock is active)
if is_syncing or local_lock_active or not is_allowed:
    st.write("") # Spacer
    if st.button("🔄 Check for Status Update", use_container_width=True):
        st.rerun()

with st.expander("🛠️ Debug Info"):
    st.json(debug)
