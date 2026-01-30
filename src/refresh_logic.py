import requests
import streamlit as st
from datetime import datetime, timezone

def get_dropbox_access_token():
    """Generates a temporary access token using the refresh token."""
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": st.secrets["DROPBOX_REFRESH_TOKEN"],
        "client_id": st.secrets["DROPBOX_APP_KEY"],
        "client_secret": st.secrets["DROPBOX_APP_SECRET"]
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def get_global_cooldown():
    """Checks Dropbox metadata to see when the log was last updated."""
    # 1. Get a temporary token
    access_token = get_dropbox_access_token()
    if not access_token:
        return True, 0 # Allow if auth fails to avoid locking the app
    
    url = "https://api.dropboxapi.com/2/files/get_metadata"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    # Path must match exactly what is in your GitHub Action
    data = {"path": "/bruh/bruh_log/bruh_log.csv"}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            metadata = response.json()
            # server_modified is UTC (e.g., 2023-10-27T10:00:00Z)
            last_mod_str = metadata['server_modified'].replace('Z', '')
            last_modified = datetime.fromisoformat(last_mod_str).replace(tzinfo=timezone.utc)
            
            diff = datetime.now(timezone.utc) - last_modified
            minutes_passed = int(diff.total_seconds() // 60)
            
            if minutes_passed < 15:
                return False, 15 - minutes_passed
    except Exception:
        pass 
    
    return True, 0
