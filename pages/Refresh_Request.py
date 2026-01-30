import streamlit as st
from src.refresh_logic import trigger_refresh, get_global_cooldown
from src.guide_loader import render_markdown_guide
from datetime import datetime, timezone

st.set_page_config(page_title="Refresh Request", page_icon="🔄")

render_markdown_guide("RefreshRequestGude.md")
st.divider()

# Fetch status from our new logic
is_allowed, time_left, last_mod, error = get_global_cooldown()

# --- UI VISUALS ---
st.subheader("System Status")
col1, col2 = st.columns(2)

with col1:
    if is_allowed:
        st.success("✅ Ready to Sync")
    else:
        st.error(f"🛑 Cooldown: {time_left}m left")

with col2:
    if last_mod:
        # Display how long ago the file was updated
        st.metric("Last File Update (UTC)", last_mod.strftime("%H:%M:%S"))
    else:
        st.metric("Last File Update", "Unknown")

# Debugging section for you to see what's happening under the hood
with st.expander("🔍 Debug Information"):
    st.write(f"**Current Time (UTC):** {datetime.now(timezone.utc).strftime('%H:%M:%S')}")
    st.write(f"**Last Modified (UTC):** {last_mod}")
    if error:
        st.warning(f"**Error Reported:** {error}")

st.divider()

# --- REFRESH ACTION ---
if not is_allowed:
    st.warning(f"Please wait {time_left} more minutes. System is cooling down from the last update.")
    st.button("🚀 Trigger Refresh", disabled=True)
else:
    days_to_sync = st.select_slider("Days to look back:", options=[1, 2, 3, 4, 5], value=2)
    if st.button("🚀 Trigger Refresh"):
        with st.spinner("Dispatching GitHub Action..."):
            if trigger_refresh(days_to_sync):
                st.success("Request sent! Page will lock for 15m once Dropbox receives the file.")
                st.balloons()
                st.rerun()
            else:
                st.error("GitHub dispatch failed.")
