import requests
import streamlit as st
from datetime import datetime, timezone

def get_file_age_minutes():
    """Checks Dropbox to see how many minutes ago the file was updated."""
    try:
        # Use the Dropbox link from secrets
        db_link = st.secrets["DROPBOXLINK"]
        response = requests.get(db_link, stream=True)
        last_mod_str = response.headers.get('last-modified')
        
        if last_mod_str:
            last_mod = datetime.strptime(last_mod_str, '%a, %d %b %Y %H:%M:%S %Z').replace(tzinfo=timezone.utc)
            diff = datetime.now(timezone.utc) - last_mod
            return int(diff.total_seconds() // 60)
    except:
        return 999  # If check fails, assume it's old enough
    return 999

def trigger_github_sync(update_hours):
    """Triggers the GitHub Action via Repository Dispatch."""
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    
    url = f"https://api.github.com/repos/{repo}/dispatches"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "event_type": "manual_refresh",
        "client_payload": {"hours": update_hours}
    }
    
    response = requests.post(url, headers=headers, json=data)
    # GitHub returns 204 No Content on success
    return response.status_code == 204
