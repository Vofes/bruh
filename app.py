import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timezone
from src.guide_loader import render_markdown_guide 

# 1. Setup
DB_LINK = st.secrets["DROPBOXLINK"]

# Ensure session state variables exist
if 'last_update_check' not in st.session_state:
    st.session_state['last_update_check'] = "Never"
if 'current_file_time' not in st.session_state:
    st.session_state['current_file_time'] = None

# --- CORE FUNCTIONS ---

def get_actual_dropbox_mtime():
    """Uses the Dropbox API to get the REAL modified time of the file."""
    try:
        auth_res = requests.post("https://api.dropbox.com/oauth2/token", data={
            "grant_type": "refresh_token", 
            "refresh_token": st.secrets["DROPBOX_REFRESH_TOKEN"],
            "client_id": st.secrets["DROPBOX_APP_KEY"], 
            "client_secret": st.secrets["DROPBOX_APP_SECRET"]
        }).json()
        token = auth_res.get("access_token")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        data = {"path": "/bruh/bruh_log/bruh_log.csv"} 
        
        res = requests.post("https://api.dropboxapi.com/2/files/get_metadata", headers=headers, json=data).json()
        
        if 'server_modified' in res:
            dt_str = res['server_modified'].replace('Z', '')
            return datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
    except Exception:
        return None
    return None

# REMOVED the version_trigger from here so it doesn't auto-refresh
@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    """Downloads CSV. Only runs if 60 mins pass OR cache is cleared manually."""
    df = pd.read_csv(DB_LINK, header=None, dtype=str, low_memory=False)
    df.columns = ['MessageID', 'Author', 'Timestamp', 'Content'] + [f'col_{i}' for i in range(4, len(df.columns))]
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True, errors='coerce')
    df = df.dropna(subset=['Timestamp']).sort_values(by='Timestamp', ascending=True)
    return df

# --- PAGE LAYOUT ---
st.title("📊 Discord Chat Analytics")

with st.expander("📖 View Bruh-App Guide"):
    render_markdown_guide("bruhapp_guide.md")

st.divider()

# 2. THE SMART SYNC CHECK
live_file_time = get_actual_dropbox_mtime()

# Initial Load logic
if st.session_state['current_file_time'] is None:
    if live_file_time:
        st.session_state['current_file_time'] = live_file_time
    else:
        st.session_state['current_file_time'] = datetime.now(timezone.utc)
    st.session_state['last_update_check'] = datetime.now(timezone.utc).strftime("%H:%M:%S")

# 3. LOAD DATA (Standard Load)
df = load_data()

# 4. COMPARE
is_stale = False
if live_file_time and st.session_state['current_file_time']:
    # Detect if Dropbox is newer than our session's recorded file time
    if live_file_time > st.session_state['current_file_time']:
        is_stale = True

# UI Columns
m1, m2, m3 = st.columns([1, 1.2, 0.8])

# --- CALCULATE TIME DIFFERENCE ---
now = datetime.now(timezone.utc)
file_time = st.session_state['current_file_time']
diff = now - file_time

# Break down the timedelta
days = diff.days
hours, remainder = divmod(diff.seconds, 3600)
minutes, seconds = divmod(remainder, 60)

# Create a clean string for the display
time_ago_str = f"{days}d {hours}h {minutes}m {seconds}s ago"

with m1:
    st.metric("Last Data Update", time_ago_str)
    st.caption(f"Reflected: {file_time.strftime('%H:%M:%S UTC')}")
with m2:
    if is_stale:
        st.warning("🔄 New Data Detected")
        if st.button("📥 Sync New Data Now", use_container_width=True):
            st.cache_data.clear() # Clears the 60-min cache
            st.session_state['current_file_time'] = live_file_time # Updates session time
            st.rerun()
    else:
        st.success("✅ Data is Up-to-Date")
        if st.button("🔍 Check for Updates", use_container_width=True):
            st.session_state['last_update_check'] = datetime.now(timezone.utc).strftime("%H:%M:%S")
            st.rerun()
    st.caption(f"Last checked: {st.session_state['last_update_check']}")

with m3:
    st.metric("Total Messages", f"{len(df):,}")

st.divider()

# --- DATA VIEWING ---
if not df.empty:
    latest_msg = df['Timestamp'].max()
    st.info(f"🕒 **Latest Message In Data:** {latest_msg.strftime('%A, %b %d, %Y at %I:%M %p UTC')}")
    
    with st.expander("View Latest 10 Rows"):
        st.dataframe(df.tail(10), use_container_width=True)
