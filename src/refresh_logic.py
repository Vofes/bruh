import requests
import streamlit as st
from datetime import datetime, timezone

def trigger_refresh(days):
    """Starts the GitHub Action via Repository Dispatch."""
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
        st.error(f"GitHub Trigger Error: {e}")
        return False

def get_global_cooldown():
    debug = {"status": "Starting", "error": None}
    try:
        # 1. Get Access Token
        auth_url = "https://api.dropbox.com/oauth2/token"
        auth_data = {
            "grant_type": "refresh_token",
            "refresh_token": st.secrets["DROPBOX_REFRESH_TOKEN"],
            "client_id": st.secrets["DROPBOX_APP_KEY"],
            "client_secret": st.secrets["DROPBOX_APP_SECRET"]
        }
        res = requests.post(auth_url, data=auth_data).json()
        access_token = res.get("access_token")

        # 2. ALWAYS Get CSV Metadata first (to ensure Last Sync works)
        meta_url = "https://api.dropboxapi.com/2/files/get_metadata"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        
        csv_res = requests.post(meta_url, headers=headers, json={"path": "/bruh/bruh_log/bruh_log.csv"})
        last_mod = None
        mins_passed = 999
        
        if csv_res.status_code == 200:
            last_mod_str = csv_res.json()['server_modified'].replace('Z', '')
            last_mod = datetime.fromisoformat(last_mod_str).replace(tzinfo=timezone.utc)
            mins_passed = int((datetime.now(timezone.utc) - last_mod).total_seconds() // 60)

        # 3. Check for Global Lock (Syncing)
        lock_res = requests.post(meta_url, headers=headers, json={"path": "/bruh/lock.txt"})
        is_syncing = (lock_res.status_code == 200)

        # 4. Return all data
        if is_syncing:
            return False, True, 0, last_mod, debug
        
        if mins_passed < 15:
            return False, False, (15 - mins_passed), last_mod, debug
            
        return True, False, 0, last_mod, debug
            
    except Exception as e:
        debug["error"] = str(e)
        return True, False, 0, None, debug
