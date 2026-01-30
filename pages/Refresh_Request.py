import streamlit as st
from src.refresh_logic import trigger_refresh, get_global_cooldown
from src.guide_loader import render_markdown_guide

# 1. Fetch State
is_allowed, is_syncing, time_left, last_mod, debug_info = get_global_cooldown()

st.title("🔄 Data Refresh Hub")

# 2. Tier Selection
tier = st.radio("Access Level:", ["Normal", "Authorized Personnel"], horizontal=True)

max_days = 7
guide_file = "NRefreshRequest_Guide.md"
authorized = True

if tier == "Authorized Personnel":
    pwd = st.text_input("Enter APASSWORD:", type="password")
    if pwd == st.secrets.get("APASSWORD"):
        st.success("Authorized: 1-30 Day Lookback")
        max_days, guide_file = 30, "ARefreshRequest_Guide.md"
    else:
        authorized = False
        if pwd: st.error("Incorrect Password")

# 3. Render Markdown
try:
    render_markdown_guide(guide_file)
except:
    st.caption(f"Waiting for {guide_file}...")

st.divider()

# 4. Status Metrics
c1, c2 = st.columns(2)
with c1:
    if is_syncing:
        st.warning("⏳ **Syncing...**")
    elif not is_allowed:
        st.error(f"🛑 **Cooldown:** {time_left}m")
    else:
        st.success("✅ **System Ready**")

with c2:
    if last_mod:
        st.metric("Last Update (UTC)", last_mod.strftime("%H:%M"))
    else:
        st.metric("Last Update", "Offline")

# 5. Trigger
st.divider()
days = st.select_slider("Select Days:", range(1, max_days + 1), value=2)

btn_label = "⏳ Syncing..." if is_syncing else ("🚀 Trigger Refresh" if is_allowed else f"🛑 Cooldown ({time_left}m)")

if st.button(btn_label, disabled=(not is_allowed or is_syncing or not authorized), use_container_width=True):
    if trigger_refresh(days):
        st.toast("Success!"); st.rerun()

# 6. Manual Refresh
if st.button("🔄 Refresh Page Status", use_container_width=True):
    st.rerun()

# 7. DEVELOPER DEBUG TOOLS
with st.expander("🛠️ Developer Debug Info"):
    st.write("### API Response Codes")
    st.json(debug_info)
    if st.button("🔓 Force Clear (Reset App View)"):
        st.rerun()
