import streamlit as st
from src.refresh_logic import trigger_refresh, get_global_cooldown
from src.guide_loader import render_markdown_guide

# 1. Fetch Global State
is_allowed, is_syncing, time_left, last_mod = get_global_cooldown()

st.title("🔄 Data Refresh Hub")

# 2. Access Tiers
tier = st.radio("Access Level:", ["Normal", "Authorized Personnel"], horizontal=True)

max_days = 7
guide_file = "NRefreshRequest_Guide.md"
authorized = True

if tier == "Authorized Personnel":
    pwd = st.text_input("Enter APASSWORD:", type="password")
    if pwd == st.secrets.get("APASSWORD"):
        st.success("Authorized: 1-30 Day Access")
        max_days, guide_file = 30, "ARefreshRequest_Guide.md"
    else:
        authorized = False
        if pwd: st.error("Incorrect Password")

# 3. Show Guide
try:
    render_markdown_guide(guide_file)
except:
    st.info("Loading guide...")

st.divider()

# 4. Status Metrics
col1, col2 = st.columns(2)
with col1:
    if is_syncing:
        st.warning("⏳ **Syncing...**")
    elif not is_allowed:
        st.error(f"🛑 **Cooldown:** {time_left}m")
    else:
        st.success("✅ **System Ready**")

with col2:
    if last_mod:
        st.metric("Last Data Update", last_mod.strftime("%H:%M UTC"))
    else:
        st.metric("Last Data Update", "Offline")

# 5. Trigger Section
st.divider()
days = st.select_slider("Lookback Window (Days):", range(1, max_days + 1), value=2)

# Button Text & Logic
if is_syncing:
    btn_text = "⏳ Sync in Progress"
elif not is_allowed:
    btn_text = f"🚀 Cooldown ({time_left}m)"
elif not authorized:
    btn_text = "🔒 Password Required"
else:
    btn_text = "🚀 Trigger Refresh"

if st.button(btn_text, disabled=(not is_allowed or is_syncing or not authorized), use_container_width=True):
    if trigger_refresh(days):
        st.toast("Sync Started!")
        st.rerun()

# 6. FIXED REFRESH BUTTON (Always visible for easy status checks)
st.write("") 
if st.button("🔄 Check for Status Update", use_container_width=True):
    st.rerun()
