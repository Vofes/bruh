import requests
import streamlit as st
from datetime import datetime, timezone

def trigger_refresh(days):
    try:
        url = f"https://api.github.com/repos/{st.secrets['GITHUB_REPO']}/dispatches"
        headers = {"Authorization": f"Bearer {st.secrets['GITHUB_TOKEN']}", "Accept": "application/vnd.github.v3+json"}
        res = requests.post(url, json={"event_type": "manual_refresh_event", "client_payload": {"days": int(days)}}, headers=headers)
        return res.status_code == 204
    except: return False

def get_global_cooldown():
    # Setup standard return structure
    debug = {"auth": "pending", "csv_check": "pending", "lock_check": "pending", "errors": []}
    last_mod = None
    is_syncing = False
    mins_passed = 999
    
    try:
        # 1. Auth
        auth_res = requests.post("https://api.dropbox.com/oauth2/token", data={
            "grant_type": "refresh_token", "refresh_token": st.secrets["DROPBOX_REFRESH_TOKEN"],
            "client_id": st.secrets["DROPBOX_APP_KEY"], "client_secret": st.secrets["DROPBOX_APP_SECRET"]
        })
        debug["auth"] = auth_res.status_code
        token = auth_res.json().get("access_token")

        if not token:
            debug["errors"].append("No access token returned")
            return True, False, 0, None, debug

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # 2. Check CSV (for Last Sync)
        m_res = requests.post("https://api.dropboxapi.com/2/files/get_metadata", headers=headers, json={"path": "/bruh/bruh_log/bruh_log.csv"})
        debug["csv_check"] = m_res.status_code
        if m_res.status_code == 200:
            data = m_res.json()
            last_mod = datetime.fromisoformat(data['server_modified'].replace('Z', '')).replace(tzinfo=timezone.utc)
            mins_passed = int((datetime.now(timezone.utc) - last_mod).total_seconds() // 60)
        else:
            debug["errors"].append(f"CSV Metadata fail: {m_res.text}")

        # 3. Check Lock (for Syncing status)
        l_res = requests.post("https://api.dropboxapi.com/2/files/get_metadata", headers=headers, json={"path": "/bruh/lock.txt"})
        debug["lock_check"] = l_res.status_code
        is_syncing = (l_res.status_code == 200)

        return (mins_passed >= 15), is_syncing, (15 - mins_passed), last_mod, debug
        
    except Exception as e:
        debug["errors"].append(str(e))
        return True, False, 0, None, debug
