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
    # 1. Check if this specific user JUST clicked the button (Local Lock)
    if st.session_state.get('just_triggered', False):
        # If they clicked less than 2 minutes ago, keep them locked
        # while the GitHub Action finishes.
        last_click = st.session_state.get('click_time', datetime.now(timezone.utc))
        diff = datetime.now(timezone.utc) - last_click
        if diff.total_seconds() < 120: # 2 minute local buffer
            return False, 15, None, {"status": "Local Buffer Active"}

    # 2. Otherwise, proceed to the Global Dropbox check
    try:
        # ... (Include your existing Dropbox API logic here) ...
        # (Assuming the rest of the function follows the previous logic)
        pass
    except Exception as e:
        return True, 0, None, {"error": str(e)}
        
        if not access_token:
            debug["error"] = "Auth failed: No access token"
            return True, 0, None, debug

        # 2. Fetch Metadata
        meta_url = "https://api.dropboxapi.com/2/files/get_metadata"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {"path": "/bruh/bruh_log/bruh_log.csv"}
        
        res = requests.post(meta_url, headers=headers, json=payload)
        
        if res.status_code == 200:
            meta = res.json()
            last_mod_str = meta['server_modified'].replace('Z', '')
            last_mod = datetime.fromisoformat(last_mod_str).replace(tzinfo=timezone.utc)
            
            now_utc = datetime.now(timezone.utc)
            diff = now_utc - last_mod
            mins_passed = int(diff.total_seconds() // 60)
            
            debug["mins_passed"] = mins_passed
            debug["server_time"] = last_mod
            debug["now_time"] = now_utc

            if mins_passed < 15:
                return False, (15 - mins_passed), last_mod, debug
            return True, 0, last_mod, debug
        else:
            debug["error"] = f"Dropbox API {res.status_code}: {res.text}"
            
    except Exception as e:
        debug["error"] = str(e)
    
    return True, 0, None, debug
