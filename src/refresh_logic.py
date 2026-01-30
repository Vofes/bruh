import requests
import streamlit as st
from datetime import datetime, timezone

# Ensure this function starts at the very beginning of the line!
def trigger_refresh(days):
    """Triggers the GitHub Action via Repository Dispatch."""
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

def get_global_cooldown():
    """Checks Dropbox metadata to see when the log was last updated."""
    # Simplified version for checking if it imports correctly
    try:
        # Check if secrets exist before trying to use them
        if "DROPBOX_REFRESH_TOKEN" not in st.secrets:
            return True, 0
            
        url = "https://api.dropbox.com/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": st.secrets["DROPBOX_REFRESH_TOKEN"],
            "client_id": st.secrets["DROPBOX_APP_KEY"],
            "client_secret": st.secrets["DROPBOX_APP_SECRET"]
        }
        auth_res = requests.post(url, data=data)
        access_token = auth_res.json().get("access_token")
        
        if not access_token:
            return True, 0

        # Dropbox check
        meta_url = "https://api.dropboxapi.com/2/files/get_metadata"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {"path": "/bruh/bruh_log/bruh_log.csv"}
        
        res = requests.post(meta_url, headers=headers, json=payload)
        if res.status_code == 200:
            last_mod_str = res.json()['server_modified'].replace('Z', '')
            last_mod = datetime.fromisoformat(last_mod_str).replace(tzinfo=timezone.utc)
            diff = datetime.now(timezone.utc) - last_mod
            mins = int(diff.total_seconds() // 60)
            if mins < 15:
                return False, 15 - mins
    except Exception:
        pass
    return True, 0
