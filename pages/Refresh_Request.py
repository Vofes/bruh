import streamlit as st
from src.refresh_logic import trigger_refresh, get_global_cooldown
from datetime import datetime, timezone

st.set_page_config(page_title="Refresh Request", page_icon="🔄")

# 1. Status Check
is_allowed, is_syncing, time_left, last_mod, debug = get_global_cooldown()

# 2. Tier Selection & Password
st.subheader("Sync Configuration")
tier = st.radio("Access Level:", ["Normal", "Authorized Personnel"], horizontal=True)

max_days = 7
is_authorized = False

if tier == "Authorized Personnel":
    pwd = st.text_input("Enter APASSWORD:", type="password")
    if pwd == st.secrets["APASSWORD"]:
        st.success("Authorization Confirmed")
        max_days = 28
        is_authorized = True
    elif pwd != "":
        st.error("Invalid Password")

# 3. UI Metrics
st.divider()
m1, m2 = st.columns(2)
with m1:
    if is_syncing:
        st.warning("⏳ Sync in Progress...")
    elif not is_allowed:
        st.error(f"🛑 Cooldown: {time_left}m")
    else:
        st.success("✅ System Ready")

with m2:
    if is_syncing:
        st.info("The system is currently writing to Dropbox.")
    elif last_mod:
        st.metric("Last Successful Sync", last_mod.strftime("%H:%M UTC"))
    else:
        st.metric("Last Successful Sync", "Unknown")

# 4. The Action
st.divider()
days = st.select_slider("Days to look back:", options=list(range(1, max_days + 1)), value=2)

if st.button("🚀 Trigger Sync", disabled=(not is_allowed or is_syncing or (tier=="Authorized Personnel" and not is_authorized))):
    if trigger_refresh(days):
        # We should ideally set the lock here, but trigger_refresh starts the process
        st.toast("Sync Request Dispatched!")
        st.balloons()
        st.rerun()
