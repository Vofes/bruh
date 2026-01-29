import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone

# 1. Configuration
DB_LINK = st.secrets["DROPBOXLINK"]
# Replace with your actual GitHub raw link to the guide
GUIDE_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/guides/bruhapp-guide.md"

def get_last_sync_info():
    """Checks the Dropbox file metadata for a rough sync estimate."""
    try:
        # Use a GET request to ensure we get fresh headers
        response = requests.get(DB_LINK, stream=True)
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
    """Downloads CSV, cleans headers, and handles UTC timestamps."""
    df = pd.read_csv(DB_LINK, header=None, dtype=str, low_memory=False)
    df.columns = ['MessageID', 'Author', 'Timestamp', 'Content'] + [f'col_{i}' for i in range(4, len(df.columns))]
    
    # Coerce errors to handle any stray header rows
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True, errors='coerce')
    df = df.dropna(subset=['Timestamp']).sort_values(by='Timestamp')
    return df

# --- Sidebar: Sync & Stats ---
st.sidebar.title("📡 Live Status")
hours, mins, last_sync_dt = get_last_sync_info()

if hours is not None:
    status_text = f"{mins}m ago" if hours == 0 else f"{hours}h {mins}m ago"
    st.sidebar.success(f"File Updated: {status_text}")
else:
    st.sidebar.warning("⚠️ Sync metadata unavailable")

# --- Main App Logic ---
st.title("Discord Chat Analytics")

# 1. Display the Guide
try:
    guide_content = requests.get(GUIDE_URL).text
    with st.expander("📖 View Bruh-App Guide"):
        st.markdown(guide_content)
except Exception:
    st.error("Could not load guide from GitHub.")

# 2. Load Data
with st.spinner("Fetching latest bruhs..."):
    df = load_data()

# 3. Data Insights (The requested fix)
if not df.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Messages", f"{len(df):,}")
    
    with col2:
        # Get the latest timestamp from the data itself
        latest_msg_time = df['Timestamp'].max()
        human_time = latest_msg_time.strftime("%A, %b %d, %Y at %I:%M %p UTC")
        st.write("**Latest Message Received:**")
        st.info(f"🕒 {human_time}")
else:
    st.error("Dataframe is empty. Check your source file.")

# 4. Preview (Optional)
with st.expander("View Raw Data Preview"):
    st.dataframe(df.tail(10)) # Tail shows newest messages
