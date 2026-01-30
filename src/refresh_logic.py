import requests
import streamlit as st
from datetime import datetime, timezone

def get_global_cooldown():
    # 1. Initialize Debug Dictionary immediately
    debug = {"status": "Starting", "error": None}
    
    # 2. Hybrid Lock: Check local session first
    if st.session_state.get('just_triggered', False):
        last_click = st.session_state.get('click_time', datetime.now(timezone.utc))
        diff = datetime.now(timezone.utc) - last_click
        mins_since_click = int(diff.total_seconds() // 60)
        
        if diff.total_seconds() < 120:  # 2 minute buffer
            debug["status"] = "Local Buffer Active"
            # Return 4 values: is_allowed, time_left, last_mod, debug
            return False, 15, None, debug

    # 3. Global Lock: Dropbox Check
    try:
        auth_url = "https://api.dropbox.com/oauth2/token"
        auth_data = {
            "grant_type": "refresh_token",
            "refresh_token": st.secrets["DROPBOX_REFRESH_TOKEN"],
            "client_id": st.secrets["DROPBOX_APP_KEY"],
            "client_secret": st.secrets["DROPBOX_APP_SECRET"]
        }
        
        auth_res = requests.post(auth_url, data=auth_data)
        access_token = auth_res.json().get("access_token")

        if not access_token:
            debug["error"] = "Auth failed: No access token"
            return True, 0, None, debug

        meta_url = "https://api.dropboxapi.com/2/files/get_metadata"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {"path": "/bruh/bruh_log/bruh_log.csv"}
        
        res = requests.post(meta_url, headers=headers, json=payload)
        
        if res.status_code == 200:
            last_mod_str = res.json()['server_modified'].replace('Z', '')
            last_mod = datetime.fromisoformat(last_mod_str).replace(tzinfo=timezone.utc)
            
            diff = datetime.now(timezone.utc) - last_mod
            mins_passed = int(diff.total_seconds() // 60)
            
            debug["mins_passed"] = mins_passed
            debug["status"] = "Dropbox Check Success"

            if mins_passed < 15:
                return False, (15 - mins_passed), last_mod, debug
            
            # If we are past 15 mins, clear the local 'just_triggered' flag
            st.session_state['just_triggered'] = False
            return True, 0, last_mod, debug
        
        else:
            debug["error"] = f"Dropbox API {res.status_code}"
            
    except Exception as e:
        debug["error"] = str(e)
    
    # Final Fallback (ensures 4 values are always returned)
    return True, 0, None, debug
