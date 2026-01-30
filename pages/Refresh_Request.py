import streamlit as st
from src.refresh_logic import trigger_refresh, get_global_cooldown
from src.guide_loader import render_markdown_guide
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="Refresh Request", page_icon="🔄")

# --- 1. LOCAL LOCK INITIALIZATION ---
if 'local_lock_until' not in st.session_state:
    st.session_state['local_lock_until'] = datetime.now(timezone.utc)

# --- 2. DATA FETCH ---
is_allowed, is_syncing, time_left, last_mod, debug_info = get_global_cooldown()

# Calculate local lock
now = datetime.now(timezone.utc)
# The local lock is just a "blind" shield for the first few minutes after clicking
local_locked = now < st.session_state['local_lock_until']

st.title("🔄 Data Refresh Hub")

# --- 3. TIER SELECTION & PASSWORD LOGIC ---
tier = st.radio("Access Level:", ["Normal", "Authorized Personnel"], horizontal=True)
max_days, guide_file, authorized, is_mod, use_text_input = 7, "NRefreshRequest_Guide.md", True, False, False

if tier == "Authorized Personnel":
    pwd = st.text_input("Enter Credentials:", type="password")
    if pwd == st.secrets.get("MOD_PASSWORD"):
        st.success("👑 Moderator Access")
        is_mod, use_text_input, guide_file = True, True, "ARefreshRequest_Guide.md"
    elif pwd == st.secrets.get("APASSWORD"):
        st.success("✅ Authorized Access")
        max_days, guide_file = 30, "ARefreshRequest_Guide.md"
    else:
        authorized = False
        if pwd and len(pwd) > 0: st.error("Incorrect Password")
else:
    authorized = True

# --- 4. RENDER GUIDE ---
try:
    render_markdown_guide(guide_file)
except:
    st.caption("Loading instructions...")

st.divider()

# --- 5. STATUS METRICS (STRICT HIERARCHY) ---
c1, c2 = st.columns(2)
with c1:
    # 1. GLOBAL COOLDOWN (Red) - Highest Priority
    if not is_allowed and not is_syncing:
        st.error(f"🛑 **Global Cooldown:** {time_left}m")
    
    # 2. SYNCING (Yellow) - Second Priority
    elif is_syncing or local_locked:
        st.warning("⏳ **Syncing in Progress...**")
    
    # 3. READY (Green)
    else:
        st.success("✅ **System Ready**")

with c2:
    if last_mod:
        st.metric("Last Update (UTC)", last_mod.strftime("%H:%M"))
    else:
        st.metric("Last Update", "Offline")

# --- 6. TRIGGER SECTION ---
st.divider()

if use_text_input:
    days = st.number_input("Enter Custom Lookback (Days):", min_value=1, max_value=9999, value=30)
else:
    days = st.select_slider("Select Lookback (Days):", range(1, max_days + 1), value=2)

# --- BUTTON TEXT LOGIC ---
if not is_allowed and not is_syncing:
    btn_label, btn_dis = f"🛑 Cooldown ({time_left}m)", True
elif is_syncing or local_locked:
    btn_label, btn_dis = "⏳ Syncing...", True
elif not authorized:
    btn_label, btn_dis = "🔒 Credentials Required", True
else:
    btn_label, btn_dis = "🚀 Trigger Sync Now", False

if st.button(btn_label, disabled=btn_dis, use_container_width=True):
    # Set the local shield for 10 minutes to cover the gap before lock.txt exists
    st.session_state['local_lock_until'] = datetime.now(timezone.utc) + timedelta(minutes=10)
    if trigger_refresh(days):
        st.toast("Instruction received!")
        st.rerun()
    else:
        st.session_state['local_lock_until'] = datetime.now(timezone.utc)
        st.error("GitHub Dispatch failed.")

if st.button("🛰️ Update System Status", use_container_width=True):
    st.rerun()

# --- 7. MODERATOR DEBUG TOOLS ---
if is_mod:
    with st.expander("👑 Moderator Debug Console"):
        st.json(debug_info)
