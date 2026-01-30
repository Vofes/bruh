import requests
import streamlit as st
from datetime import datetime, timezone

def trigger_refresh(days):
    """Starts the GitHub Action."""
    repo = st.secrets["GITHUB_REPO"]
    token = st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{repo}/dispatches"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    payload = {"event_type": "manual_refresh_event", "client_payload": {"days": int(days)}}
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code == 204

def get_global_cooldown():
    """Talks to Dropbox to see if the file is 'fresh'."""
    try:
        # 1. Get temporary access token
        auth_url = "https://api.dropbox.com/oauth2/token"
        auth_data = {
            "grant_type": "refresh_token",
            "refresh_token": st.secrets["DROPBOX_REFRESH_TOKEN"],
            "client_id": st.secrets["DROPBOX_APP_KEY"],
            "client_secret": st.secrets["DROPBOX_APP_SECRET"]
        }
        access_token = requests.post(auth_url, data=auth_data).json().get("access_token")

        # 2. Check File Metadata
        meta_url = "https://api.dropboxapi.com/2/files/get_metadata"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {"path": "/bruh/bruh_log/bruh_log.csv"} # Match your DB path exactly!
        
        res = requests.post(meta_url, headers=headers, json=payload)
        
        if res.status_code == 200:
            last_mod_str = res.json()['server_modified'].replace('Z', '')
            last_mod = datetime.fromisoformat(last_mod_str).replace(tzinfo=timezone.utc)
            diff = datetime.now(timezone.utc) - last_mod
            mins_passed = int(diff.total_seconds() // 60)
            
            if mins_passed < 15:
                return False, (15 - mins_passed), last_mod
            return True, 0, last_mod
    except Exception as e:
        print(f"Error checking cooldown: {e}")
    
    return True, 0, None
