import streamlit as st
from src.refresh_logic import trigger_refresh, get_global_cooldown
from datetime import datetime, timezone

st.set_page_config(page_title="Refresh Request", page_icon="🔄")

# 1. Check Backend Status
is_allowed, is_syncing, time_left, last_mod, debug = get_global_cooldown()

st.title("🔄 Data Refresh Hub")

# 2. Authorization Tiers
tier = st.radio("Access Level:", ["Normal", "Authorized Personnel"], horizontal=True)
max_days = 7
is_authorized = False

if tier == "Authorized Personnel":
    pwd = st.text_input("Enter APASSWORD:", type="password")
    if pwd == st.secrets.get("APASSWORD"):
        st.success("Authorization Confirmed")
        max_days = 28
        is_authorized = True
    elif pwd:
        st.error("Invalid Password")

# 3. Status Display
st.divider()
if is_syncing:
    st.warning("⏳ **Currently Syncing...** Please wait for the process to finish.")
elif not is_allowed:
    st.error(f"🛑 **Cooldown Active.** System available in {time_left} minutes.")
else:
    st.success("✅ **System Ready.** No active syncs or cooldowns.")

if last_mod:
    st.caption(f"Last successful sync detected at: {last_mod.strftime('%Y-%m-%d %H:%M:%S')} UTC")

# 4. Trigger Section
st.divider()
days = st.select_slider("Lookback Window (Days):", options=list(range(1, max_days + 1)), value=2)

# Button is disabled if: (System cooling down) OR (Currently syncing) OR (AP Tier selected but not authorized)
btn_disabled = (not is_allowed) or is_syncing or (tier == "Authorized Personnel" and not is_authorized)

if st.button("🚀 Trigger Sync Now", disabled=btn_disabled, use_container_width=True):
    if trigger_refresh(days):
        st.toast("GitHub Action Dispatched!")
        st.balloons()
        st.rerun()

# Debug for you
with st.expander("🛠️ Debug Info"):
    st.json(debug)
