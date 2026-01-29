import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone

# 1. Configuration - The Direct Download Link (dl=1)
DB_LINK = "https://www.dropbox.com/scl/fi/ine04ie48l60j6pj804px/chat_logs.csv?rlkey=3bhydbcigk7ndawwrdee7pv8f&st=igoinb9c&dl=1"

def get_last_sync_info():
    """Checks the Dropbox file metadata to see when it was last updated."""
    try:
        response = requests.head(DB_LINK, allow_redirects=True)
        last_mod_str = response.headers.get('last-modified')
        if last_mod_str:
            # Parse the Dropbox time format
            last_mod = datetime.strptime(last_mod_str, '%a, %d %b %Y %H:%M:%S %Z')
            last_mod = last_mod.replace(tzinfo=timezone.utc)
            
            # Calculate time difference
            now = datetime.now(timezone.utc)
            diff = now - last_mod
            hours = int(diff.total_seconds() // 3600)
            minutes = int((diff.total_seconds() % 3600) // 60)
            return hours, minutes, last_mod
    except Exception:
        return None, None, None
    return None, None, None

@st.cache_data(ttl=3600) # Cache the data for 1 hour to keep the app fast
def load_data():
    """Downloads the CSV from Dropbox."""
    df = pd.read_csv(DB_LINK, low_memory=False)
    # Perform any basic cleaning here (convert dates, etc.)
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

# ... Your charts and leaderboard code go here ...
