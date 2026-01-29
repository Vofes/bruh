import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone
# Import your guide logic from the src folder
from src.guides import display_guide 

# 1. Configuration
DB_LINK = st.secrets["DROPBOXLINK"]

def get_last_sync_info():
    """Checks the Dropbox file metadata for a rough sync estimate."""
    try:
        response = requests.get(DB_LINK, stream=True)
        last_mod_str = response.headers.get('last-modified')
        if last_mod_str:
            last_mod = datetime.strptime(last_mod_str, '%a, %d %b %Y %H:%M:%S %Z')
            last_mod = last_mod.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            diff = now - last_mod
            hours = int(diff.total_seconds() // 3600)
            minutes = int((diff.total_seconds() % 3600) // 60)
            return hours, minutes
    except Exception:
        return None, None
    return None, None

@st.cache_data(ttl=3600) 
def load_data():
    """Downloads CSV, cleans headers, and handles UTC timestamps."""
    df = pd.read_csv(DB_LINK, header=None, dtype=str, low_memory=False)
    # Mapping based on our sync logic
    df.columns = ['MessageID', 'Author', 'Timestamp', 'Content'] + [f'col_{i}' for i in range(4, len(df.columns))]
    
    # Clean up Timestamp to UTC
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True, errors='coerce')
    df = df.dropna(subset=['Timestamp']).sort_values(by='Timestamp')
    return df

# --- Sidebar: Live Status ---
st.sidebar.title("📡 Live Status")
hours, mins = get_last_sync_info()

if hours is not None:
    status_text = f"{mins}m ago" if hours == 0 else f"{hours}h {mins}m ago"
    st.sidebar.success(f"File Updated: {status_text}")
else:
    st.sidebar.warning("⚠️ Sync metadata unavailable")

# --- Main App Logic ---
st.title("Discord Chat Analytics")

# 1. Use the Guide from your src file
display_guide()

# 2. Load Data
with st.spinner("Fetching latest messages..."):
    df = load_data()

# 3. Data Insights (Total rows and Latest Timestamp)
if not df.empty:
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Messages", f"{len(df):,}")
    
    with col2:
        latest_msg_time = df['Timestamp'].max()
        # Human-readable UTC format
        human_time = latest_msg_time.strftime("%A, %b %d, %Y at %I:%M %p UTC")
        st.write("**Latest Message In Data:**")
        st.info(f"🕒 {human_time}")
    st.divider()
else:
    st.error("Dataframe is empty. Please check the source file.")

# 4. Preview
with st.expander("View Latest 10 Rows"):
    st.dataframe(df.tail(10))
