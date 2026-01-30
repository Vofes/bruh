import requests
import streamlit as st
from datetime import datetime, timezone

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
    try:
        # 1. Get Access Token
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
            print("DEBUG: Could not generate Dropbox Access Token")
            return True, 0

        # 2. Get Metadata
        meta_url = "https://api.dropboxapi.com/2/files/get_metadata"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        
        # Dropbox paths are case-sensitive and must start with /
        # If your folder is "Bruh" instead of "bruh", this fails!
        payload = {"path": "/bruh/bruh_log/bruh_log.csv"}
        
        res = requests.post(meta_url, headers=headers, json=payload)
        
        if res.status_code == 200:
            meta = res.json()
            # server_modified is the time it reached Dropbox
            server_time_str = meta['server_modified'].replace('Z', '')
            last_mod = datetime.fromisoformat(server_time_str).replace(tzinfo=timezone.utc)
            now_utc = datetime.now(timezone.utc)
            
            diff = now_utc - last_mod
            mins_passed = int(diff.total_seconds() // 60)
            
            print(f"DEBUG: Last Mod: {last_mod} | Now: {now_utc} | Mins: {mins_passed}")

            if mins_passed < 15:
                return False, (15 - mins_passed)
        else:
            # THIS IS IMPORTANT: If this prints in your logs, the path is wrong
            print(f"DEBUG: Dropbox API returned {res.status_code}: {res.text}")
                
    except Exception as e:
        print(f"DEBUG: Cooldown Logic Error: {e}")
    
    return True, 0
