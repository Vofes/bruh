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
if 'data_cache_time' not in st.session_state:
    st.session_state['data_cache_time'] = None

# --- CORE FUNCTIONS ---

def get_dropbox_metadata():
    """Fetches headers with a cache-buster to ensure we see the latest version."""
    try:
        # Adding a timestamp to the URL forces Dropbox to bypass its own cache
        cache_buster = f"&t={int(time.time())}"
        url = DB_LINK + cache_buster
        
        response = requests.head(url, timeout=5) # HEAD is even lighter than GET stream
        last_mod_str = response.headers.get('last-modified')
        
        if last_mod_str:
            dt = datetime.strptime(last_mod_str, '%a, %d %b %Y %H:%M:%S %Z')
            return dt.replace(tzinfo=timezone.utc)
    except Exception as e:
        return None
    return None

@st.cache_data(show_spinner=False)
def load_data():
    """Downloads and cleans the CSV."""
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

# 2. DATA LOADING (INITIAL)
if st.session_state['data_cache_time'] is None:
    with st.spinner("Initial load..."):
        df = load_data()
        st.session_state['data_cache_time'] = datetime.now(timezone.utc)
        st.session_state['last_update_check'] = datetime.now(timezone.utc).strftime("%H:%M:%S")
else:
    df = load_data()

# 3. THE SMART SYNC CHECK
live_file_time = get_dropbox_metadata()
cached_time = st.session_state['data_cache_time']

# Logic: Is the file on Dropbox newer than when we last saved data to our session?
is_stale = False
if live_file_time and cached_time:
    # Adding a 5-second buffer to ignore tiny sync delays
    if live_file_time > (cached_time + pd.Timedelta(seconds=5)):
        is_stale = True

# UI Columns
m1, m2, m3 = st.columns([1, 1.2, 0.8])

with m1:
    # #1 DATA LOCAL AGE
    if cached_time:
        st.metric("Data Local Age", cached_time.strftime("%H:%M:%S UTC"))
    else:
        st.metric("Data Local Age", "Pending...")
    st.caption("Time data was last pulled")

with m2:
    # #2 SYNC STATUS
    if is_stale:
        st.warning("🔄 New Data Detected")
        if st.button("📥 Sync New Data Now", use_container_width=True):
            st.cache_data.clear()
            st.session_state['data_cache_time'] = None # Forces re-init
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
