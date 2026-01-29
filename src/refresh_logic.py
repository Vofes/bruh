import requests
import streamlit as st

def trigger_github_sync(update_hours):
    """Triggers the GitHub Action via Repository Dispatch."""
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    
    url = f"https://api.github.com/repos/{repo}/dispatches"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # This 'event_type' must match your YAML file later
    data = {
        "event_type": "manual_refresh",
        "client_payload": {"hours": update_hours}
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.status_code == 204
