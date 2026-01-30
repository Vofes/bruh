import requests
import streamlit as st
from datetime import datetime, timezone

def get_global_cooldown():
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
            return True, 0

        # 2. Get Metadata
        meta_url = "https://api.dropboxapi.com/2/files/get_metadata"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {"path": "/bruh/bruh_log/bruh_log.csv"}
        
        res = requests.post(meta_url, headers=headers, json=payload)
        
        if res.status_code == 200:
            # Parse Dropbox Time (Format: 2024-10-27T10:00:00Z)
            # We strip the Z and force it to UTC
            server_time_str = res.json()['server_modified'].replace('Z', '')
            last_mod = datetime.fromisoformat(server_time_str).replace(tzinfo=timezone.utc)
            
            # Use datetime.now(timezone.utc) to ensure we aren't using local time
            now_utc = datetime.now(timezone.utc)
            
            diff = now_utc - last_mod
            mins_passed = int(diff.total_seconds() // 60)
            
            # DEBUG: These show up in your "Manage App" logs
            print(f"DEBUG: File Last Mod (UTC): {last_mod}")
            print(f"DEBUG: Current Time (UTC): {now_utc}")
            print(f"DEBUG: Minutes Passed: {mins_passed}")

            if mins_passed < 15:
                return False, (15 - mins_passed)
                
    except Exception as e:
        print(f"DEBUG: Cooldown Error: {e}")
    
    return True, 0
