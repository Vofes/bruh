import requests
import streamlit as st
from datetime import datetime, timezone

def set_global_lock(access_token, state=True):
    """Creates or Deletes a lock file on Dropbox to signal 'Syncing' status."""
    if state:
        url = "https://content.dropboxapi.com/2/files/upload"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Dropbox-API-Arg": '{"path": "/bruh/lock.txt", "mode": "overwrite"}',
            "Content-Type": "application/octet-stream"
        }
        requests.post(url, headers=headers, data="busy")
    else:
        url = "https://api.dropboxapi.com/2/files/delete_v2"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        requests.post(url, headers=headers, json={"path": "/bruh/lock.txt"})

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
        access_token = requests.post(auth_url, data=auth_data).json().get("access_token")

        # 2. Check for Global Lock (Is it currently syncing?)
        lock_url = "https://api.dropboxapi.com/2/files/get_metadata"
        lock_headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        is_syncing = requests.post(lock_url, headers=lock_headers, json={"path": "/bruh/lock.txt"}).status_code == 200

        # 3. Check CSV Metadata for Cooldown
        meta_url = "https://api.dropboxapi.com/2/files/get_metadata"
        res = requests.post(meta_url, headers=lock_headers, json={"path": "/bruh/bruh_log/bruh_log.csv"})
        
        last_mod = None
        mins_passed = 999
        
        if res.status_code == 200:
            last_mod_str = res.json()['server_modified'].replace('Z', '')
            last_mod = datetime.fromisoformat(last_mod_str).replace(tzinfo=timezone.utc)
            mins_passed = int((datetime.now(timezone.utc) - last_mod).total_seconds() // 60)

        # Logic Returns: (is_allowed, is_syncing, time_left, last_mod, debug)
        if is_syncing:
            return False, True, 0, last_mod, debug
        if mins_passed < 15:
            return False, False, (15 - mins_passed), last_mod, debug
            
        return True, False, 0, last_mod, debug
            
    except Exception as e:
        debug["error"] = str(e)
        return True, False, 0, None, debug
