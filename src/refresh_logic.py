import requests
import streamlit as st
from datetime import datetime, timezone

def trigger_refresh(days):
    try:
        url = f"https://api.github.com/repos/{st.secrets['GITHUB_REPO']}/dispatches"
        headers = {
            "Authorization": f"Bearer {st.secrets['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github.v3+json"
        }
        res = requests.post(url, json={"event_type": "manual_refresh_event", "client_payload": {"days": int(days)}}, headers=headers)
        return res.status_code == 204
    except:
        return False

def get_global_cooldown():
    # Defaults
    last_mod = None
    is_syncing = False
    mins_passed = 999
    debug = {"status": "Checking..."}
    
    try:
        # Token Exchange
        auth = requests.post("https://api.dropbox.com/oauth2/token", data={
            "grant_type": "refresh_token", "refresh_token": st.secrets["DROPBOX_REFRESH_TOKEN"],
            "client_id": st.secrets["DROPBOX_APP_KEY"], "client_secret": st.secrets["DROPBOX_APP_SECRET"]
        }).json()
        token = auth.get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # 1. Check Log for timestamp (MUST DO FIRST)
        m_res = requests.post("https://api.dropboxapi.com/2/files/get_metadata", headers=headers, json={"path": "/bruh/bruh_log/bruh_log.csv"}).json()
        if 'server_modified' in m_res:
            last_mod = datetime.fromisoformat(m_res['server_modified'].replace('Z', '')).replace(tzinfo=timezone.utc)
            mins_passed = int((datetime.now(timezone.utc) - last_mod).total_seconds() // 60)

        # 2. Check for Lock File (Syncing)
        l_res = requests.post("https://api.dropboxapi.com/2/files/get_metadata", headers=headers, json={"path": "/bruh/lock.txt"})
        is_syncing = (l_res.status_code == 200)

        # Return (Is Allowed, Is Syncing, Minutes Left, Last Modified)
        return (mins_passed >= 15), is_syncing, (15 - mins_passed), last_mod
    except Exception as e:
        return True, False, 0, None
