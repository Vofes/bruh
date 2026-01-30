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
# This stores the timestamp of the file currently loaded in the app
if 'current_file_time' not in st.session_state:
    st.session_state['current_file_time'] = None

# --- CORE FUNCTIONS ---

def get_dropbox_metadata():
    """Fetches the live 'Last-Modified' header from Dropbox."""
    try:
        # Cache-buster ensures we don't get a stale header from a previous request
        url = f"{DB_LINK}&t={int(time.time())}"
        response = requests.head(url, timeout=5)
        last_mod_str = response.headers.get('last-modified')
        
        if last_mod_str:
            dt = datetime.strptime(last_mod_str, '%a, %d %b %Y %H:%M:%S %Z')
            return dt.replace(tzinfo=timezone.utc)
    except Exception as e:
        return None
    return None

@st.cache_data(show_spinner=False)
def load_data():
    """Downloads CSV and returns the dataframe + its source timestamp."""
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
# Get the live time from Dropbox immediately
live_file_time = get_dropbox_metadata()

# If this is the first run, load data and store its timestamp
if st.session_state['current_file_time'] is None:
    df = load_data()
    st.session_state['current_file_time'] = live_file_time
    st.session_state['last_update_check'] = datetime.now(timezone.utc).strftime("%H:%M:%S")
else:
    df = load_data()

# 3. COMPARE: Is the live file newer than the one we have in memory?
is_stale = False
if live_file_time and st.session_state['current_file_time']:
    # We compare the two Dropbox timestamps directly. 
    # If the live one is even 1 second newer than our stored one, it's stale.
    if live_file_time > st.session_state['current_file_time']:
        is_stale = True

# UI Columns
m1, m2, m3 = st.columns([1, 1.2, 0.8])

with m1:
    # #1 DATA LOCAL AGE (The timestamp of the file currently in memory)
    file_time = st.session_state['current_file_time']
    if file_time:
        st.metric("Data File Time", file_time.strftime("%H:%M:%S UTC"))
    else:
        st.metric("Data File Time", "Checking...")
    st.caption("Modified time of loaded file")

with m2:
    # #2 SYNC STATUS
    if is_stale:
        st.warning("🔄 New File Detected")
        if st.button("📥 Sync New Data Now", use_container_width=True):
            st.cache_data.clear()
            st.session_state['current_file_time'] = None # Reset so it re-fetches
            st.rerun()
    else:
        st.success("✅ Data is Up-to-Date")
        if st.button("🔍 Check for Updates", use_container_width=True):
            st.session_state['last_update_check'] = datetime.now(timezone.utc).strftime("%H:%M:%S")
            st.rerun()
    st.caption(f"Last checked: {st.session_state['last_update_check']}")

with m3:
    # #3 TOTAL MESSAGES
    st.metric("Total Messages", f"{len(df):,}")

st.divider()

# --- DATA VIEWING ---
if not df.empty:
    latest_msg = df['Timestamp'].max()
    st.info(f"🕒 **Latest Message In Data:** {latest_msg.strftime('%A, %b %d, %Y at %I:%M %p UTC')}")
    
    with st.expander("View Latest 10 Rows"):
        st.dataframe(df.tail(10), use_container_width=True)
