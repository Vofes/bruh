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

def get_dropbox_metadata():
    """Fetches the live 'Last-Modified' header from Dropbox."""
    try:
        # Cache-buster ensures we don't get a stale header
        # We use head() for speed; if it fails, we return None
        url = f"{DB_LINK}&t={int(time.time())}"
        response = requests.head(url, timeout=7)
        last_mod_str = response.headers.get('last-modified')
        
        if last_mod_str:
            dt = datetime.strptime(last_mod_str, '%a, %d %b %Y %H:%M:%S %Z')
            return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None
    return None

# RESTORED 60-MINUTE TTL (3600 seconds)
@st.cache_data(ttl=3600, show_spinner=False)
def load_data(force_reload_trigger):
    """Downloads CSV. Triggered to reload if version changes."""
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
# Run the check at the start of every script run
live_file_time = get_dropbox_metadata()

# FALLBACK: If current_file_time is stuck, initialize it with whatever we can get
if st.session_state['current_file_time'] is None:
    if live_file_time:
        st.session_state['current_file_time'] = live_file_time
    else:
        # If Dropbox is down, use a placeholder so the UI doesn't hang
        st.session_state['current_file_time'] = datetime.now(timezone.utc)

# 3. LOAD DATA
# We pass live_file_time into the cache function. 
# If live_file_time changes, the cache "key" changes, forcing a new download.
df = load_data(st.session_state['current_file_time'])

# 4. COMPARE: Is the live file newer than the one stored in session?
is_stale = False
if live_file_time and st.session_state['current_file_time']:
    if live_file_time > st.session_state['current_file_time']:
        is_stale = True

# UI Columns
m1, m2, m3 = st.columns([1, 1.2, 0.8])

with m1:
    # #1 DATA FILE TIME
    file_time = st.session_state['current_file_time']
    st.metric("Data File Time", file_time.strftime("%H:%M:%S UTC"))
    st.caption("Modified time of loaded file")

with m2:
    # #2 SYNC STATUS
    if is_stale:
        st.warning("🔄 New File Detected")
        if st.button("📥 Sync New Data Now", use_container_width=True):
            st.cache_data.clear()
            # Update session state to the new time so the warning disappears after sync
            st.session_state['current_file_time'] = live_file_time
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
