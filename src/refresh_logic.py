import requests
import streamlit as st
from datetime import datetime, timedelta

def trigger_refresh(days):
    repo = st.secrets["GITHUB_REPO"]
    token = st.secrets["GITHUB_TOKEN"]
    
    url = f"https://api.github.com/repos/{repo}/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "event_type": "manual_refresh_event",
        "client_payload": {"days": str(days)}
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code == 204

def get_cooldown_status():
    if 'last_refresh' not in st.session_state:
        return True, 0
    
    elapsed = datetime.now() - st.session_state['last_refresh']
    remaining = 60 - (elapsed.total_seconds() // 60)
    
    if elapsed > timedelta(hours=1):
        return True, 0
    return False, int(remaining)
