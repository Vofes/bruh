import requests
import streamlit as st
from datetime import datetime, timezone

def trigger_refresh(days):
    """Starts the GitHub Action."""
    try:
        repo = st.secrets["GITHUB_REPO"]
        token = st.secrets["GITHUB_TOKEN"]
        url = f"https://api.github.com/repos/{repo}/dispatches"
        headers = {
            "Authorization": f"Bearer {token}", 
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "event_type": "manual_refresh_event", 
            "client_payload": {"days": int(days)}
        }
        response = requests.post(url, json=payload, headers=headers)
        return response.status_code == 204
    except Exception as e:
        print(f"GitHub Trigger Error: {e}")
        return False

def get_global_cooldown():
    """Returns (is_allowed, time_left, last_mod, debug_dict)"""
    # 1. Setup Debug
    debug = {"status": "Starting", "error": None}
    
    # 2. Hybrid Lock: Check if THIS browser session just clicked
    if st.session_state.get('just_triggered', False):
        last_click = st.session_state.get('click_time')
        if last_click:
            diff = datetime.now(timezone.utc) - last_click
            if diff.total_seconds() < 120:  # 2 minute local buffer
                debug["status"] = "Local Buffer Active"
                return False, 15, None, debug

    # 3. Global Lock: Check Dropbox
    try:
        # Check if secrets exist
        if "DROPBOX_REFRESH_TOKEN" not in st.secrets:
            debug["error"] = "Missing DROPBOX_REFRESH_TOKEN in Secrets"
            return True, 0, None, debug

        # Get Access Token
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
            debug["error"] = "Dropbox Auth Failed (Check Keys/Token)"
            return True, 0, None, debug

        # Get Metadata
        meta_url = "https://api.dropboxapi.com/2/files/get_metadata"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {"path": "/bruh/bruh_log/bruh_log.csv"}
        
        res = requests.post(meta_url, headers=headers, json=payload)
        
        if res.status_code == 200:
            last_mod_str = res.json()['server_modified'].replace('Z', '')
            last_mod = datetime.fromisoformat(last_mod_str).replace(tzinfo=timezone.utc)
            
            now_utc = datetime.now(timezone.utc)
            diff = now_utc - last_mod
            mins_passed = int(diff.total_seconds() // 60)
            
            debug["mins_passed"] = mins_passed
            debug["status"] = "Success"

            if mins_passed < 15:
                return False, (15 - mins_passed), last_mod, debug
            
            # If we are past 15 mins, clear the local session flag
            st.session_state['just_triggered'] = False
            return True, 0, last_mod, debug
        else:
            debug["error"] = f"Dropbox API Error {res.status_code}"
            
    except Exception as e:
        debug["error"] = f"Code Error: {str(e)}"
    
    # Fallback exit
    return True, 0, None, debug
