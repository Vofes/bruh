import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
from src.guide_loader import render_markdown_guide 

# 1. Setup & Secrets
DB_LINK = st.secrets["DROPBOXLINK"]

# Ensure we track when the user last manually checked for updates
if 'last_update_check' not in st.session_state:
    st.session_state['last_update_check'] = "Never"

# --- CORE FUNCTIONS ---

def get_dropbox_metadata():
    """Cheap check: Fetches only the headers from Dropbox to get the last modified time."""
    try:
        response = requests.get(DB_LINK, stream=True, timeout=5)
        last_mod_str = response.headers.get('last-modified')
        if last_mod_str:
            dt = datetime.strptime(last_mod_str, '%a, %d %b %Y %H:%M:%S %Z')
            return dt.replace(tzinfo=timezone.utc)
    except:
        return None
    return None

@st.cache_data(show_spinner=False)
def load_data(version_trigger):
    """
    Downloads and cleans the CSV. 
    The 'version_trigger' is just a timestamp to force a cache break when needed.
    """
    df = pd.read_csv(DB_LINK, header=None, dtype=str, low_memory=False)
    df.columns = ['MessageID', 'Author', 'Timestamp', 'Content'] + [f'col_{i}' for i in range(4, len(df.columns))]
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True, errors='coerce')
    df = df.dropna(subset=['Timestamp']).sort_values(by='Timestamp', ascending=True)
    
    # Store the exact time THIS specific data was cached
    st.session_state['data_cache_time'] = datetime.now(timezone.utc)
    return df

# --- PAGE LAYOUT ---

st.title("📊 Discord Chat Analytics")

# 1. Guide (Markdown Loader)
with st.expander("📖 View Bruh-App Guide"):
    render_markdown_guide("bruhapp_guide.md")

st.divider()

# 2. THE SMART SYNC LOGIC (The "Cheap Check")
live_time = get_dropbox_metadata()

# Initialize data_cache_time if it doesn't exist (first run)
if 'data_cache_time' not in st.session_state:
    st.session_state['data_cache_time'] = datetime.min.replace(tzinfo=timezone.utc)

# Versioning: If Live File is newer than our Cached Data, we trigger a refresh
is_stale = False
if live_time and live_time > st.session_state['data_cache_time']:
    is_stale = True

# UI Columns for #1 Sync Time and #2 Sync Status
m1, m2, m3 = st.columns([1, 1.2, 0.8])

with m1:
    # #1 SYNC TIME: Age of the CSV content currently in memory
    cached_at = st.session_state.get('data_cache_time', datetime.now(timezone.utc))
    st.metric("Data Local Age", cached_at.strftime("%H:%M:%S UTC"))
    st.caption("Time data was last pulled")

with m2:
    # #2 SYNC: The Check and Refresh Option
    if is_stale:
        st.warning("🔄 New Data Available")
        if st.button("📥 Sync New Data Now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    else:
        st.success("✅ Data is Up-to-Date")
        if st.button("🔍 Check for Updates", use_container_width=True):
            st.session_state['last_update_check'] = datetime.now(timezone.utc).strftime("%H:%M:%S")
            st.rerun()
    st.caption(f"Last checked: {st.session_state['last_update_check']}")

with m3:
    # #3 TOTAL MESSAGES
    # We load data here - it only actually "runs" the download if the cache is empty
    df = load_data(st.session_state.get('data_cache_time'))
    st.metric("Total Messages", f"{len(df):,}")

st.divider()

# --- DATA VIEWING ---

if not df.empty:
    # Latest Message Info
    latest_msg = df['Timestamp'].max()
    st.info(f"🕒 **Latest Message In Data:** {latest_msg.strftime('%A, %b %d, %Y at %I:%M %p UTC')}")
    
    # Preview
    with st.expander("View Latest 10 Rows"):
        st.dataframe(df.tail(10), use_container_width=True)
else:
    st.error("No data found. Please trigger a refresh from the Request page.")
