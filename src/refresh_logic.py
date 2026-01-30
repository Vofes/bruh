import requests
import streamlit as st
from datetime import datetime, timezone

def get_global_cooldown():
    """Checks Dropbox metadata to see when the log was last updated."""
    token = st.secrets["DROPBOX_TOKEN"] # Ensure this is your access token
    url = "https://api.dropboxapi.com/2/files/get_metadata"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "path": "/bruh/bruh_log/bruh_log.csv",
        "include_media_info": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            metadata = response.json()
            # server_modified is in UTC ISO8601 format
            last_mod_str = metadata['server_modified'].replace('Z', '')
            last_modified = datetime.fromisoformat(last_mod_str).replace(tzinfo=timezone.utc)
            
            diff = datetime.now(timezone.utc) - last_modified
            minutes_passed = int(diff.total_seconds() // 60)
            
            if minutes_passed < 15:
                return False, 15 - minutes_passed
            return True, 0
    except Exception as e:
        st.error(f"Cooldown Check Failed: {e}")
    
    return True, 0 # Default to allowed if check fails

def trigger_refresh(days):
    # ... (Keep your existing trigger_refresh code here) ...
    repo = st.secrets["GITHUB_REPO"]
    token = st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{repo}/dispatches"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    payload = {"event_type": "manual_refresh_event", "client_payload": {"days": int(days)}}
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code == 204
