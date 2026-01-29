import streamlit as st
from src.refresh_logic import trigger_github_sync, get_file_age_minutes

st.set_page_config(page_title="Refresh Request")
st.title("🔄 Sync Control")

# 20-minute logic
file_age = get_file_age_minutes()
cooldown = 20 

tab1, tab2 = st.tabs(["Normal Refresh", "Authorized Refresh"])

with tab1:
    st.info(f"Normal Mode (0-100h). Required cooldown: {cooldown} mins.")
    n_hours = st.slider("Hours", 1, 100, 24, key="n_h")
    
    if file_age < cooldown:
        st.error(f"🚫 System locked. Please wait {cooldown - file_age} more minutes.")
        st.button("Request Refresh", disabled=True, key="n_btn")
    else:
        if st.button("Request Refresh", key="n_btn_act"):
            if trigger_github_sync(n_hours):
                st.success("Request Sent! Wait ~2 mins for Dropbox update.")
            else:
                st.error("Failed to trigger.")

with tab2:
    st.info("Authorized Mode (0-1000h). No cooldown.")
    pwd = st.text_input("Admin Password", type="password")
    a_hours = st.slider("Hours", 1, 1000, 500, key="a_h")
    
    if st.button("Execute Admin Force"):
        if pwd == st.secrets["REFRESH_PASSWORD"]:
            if trigger_github_sync(a_hours):
                st.success(f"Admin Force Sent for {a_hours}h!")
            else:
                st.error("Trigger Failed.")
        else:
            st.error("Invalid Password.")
