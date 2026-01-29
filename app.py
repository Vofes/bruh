import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone

# 1. Configuration - Now using the secret link
DB_LINK = st.secrets["DROPBOXLINK"]

def get_last_sync_info():
    """Checks the Dropbox file metadata to see when it was last updated."""
    try:
        response = requests.head(DB_LINK, allow_redirects=True)
        last_mod_str = response.headers.get('last-modified')
        if last_mod_str:
            last_mod = datetime.strptime(last_mod_str, '%a, %d %b %Y %H:%M:%S %Z')
            last_mod = last_mod.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            diff = now - last_mod
            hours = int(diff.total_seconds() // 3600)
            minutes = int((diff.total_seconds() % 3600) // 60)
            return hours, minutes, last_mod
    except Exception:
        return None, None, None
    return None, None, None

@st.cache_data(ttl=3600) 
def load_data():
    """Downloads the CSV from Dropbox using headerless format."""
    # Updated to header=None and explicit column naming
    df = pd.read_csv(DB_LINK, header=None, dtype=str, low_memory=False)
    
    # Assign names based on our sync logic: ID, Author, Timestamp, Content
    df.columns = ['MessageID', 'Author', 'Timestamp', 'Content'] + [f'col_{i}' for i in range(4, len(df.columns))]
    
    # Clean up Timestamp to UTC
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True)
    
    return df

# --- Sidebar Status ---
st.sidebar.title("📡 Data Status")
hours, mins, last_sync_dt = get_last_sync_info()

if hours is not None:
    if hours == 0:
        st.sidebar.success(f"✅ Synced {mins}m ago")
    else:
        st.sidebar.info(f"🕒 Synced {hours}h {mins}m ago")
else:
    st.sidebar.warning("⚠️ Could not retrieve sync time")

# --- Main App Logic ---
st.title("Discord Chat Analytics")

with st.spinner("Downloading data from Dropbox..."):
    df = load_data()

st.write(f"Loaded **{len(df):,}** messages successfully.")

# Display a preview
st.dataframe(df.head(10))
