import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone
# Correct import from your specific file structure
from src.guide_loader import render_markdown_guide 

# 1. Configuration - Link must be in Streamlit Secrets with dl=1
DB_LINK = st.secrets["DROPBOXLINK"]

def get_last_sync_info():
    """Checks the Dropbox file metadata for a rough sync estimate."""
    try:
        # Use GET with stream=True to reliably fetch headers
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
    """Downloads CSV from Dropbox, cleans headers, and handles UTC timestamps."""
    # Load with header=None because our GitHub Action saves without headers
    df = pd.read_csv(DB_LINK, header=None, dtype=str, low_memory=False)
    
    # Map columns based on our sync logic: ID, Author, Timestamp, Content
    df.columns = ['MessageID', 'Author', 'Timestamp', 'Content'] + [f'col_{i}' for i in range(4, len(df.columns))]
    
    # Convert Timestamp to UTC and coerce errors to skip stray header text
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True, errors='coerce')
    
    # Drop rows that failed conversion (like the word 'Timestamp' itself)
    df = df.dropna(subset=['Timestamp'])
    
    # Sort so the newest messages are always at the bottom
    df = df.sort_values(by='Timestamp', ascending=True)
    return df

# --- Sidebar Status ---
st.sidebar.title("📡 Live Status")
hours, mins = get_last_sync_info()

if hours is not None:
    status_text = f"{mins}m ago" if hours == 0 else f"{hours}h {mins}m ago"
    st.sidebar.success(f"File Updated: {status_text}")
else:
    st.sidebar.warning("⚠️ Sync metadata unavailable")

# --- Main App Logic ---
st.title("Discord Chat Analytics")

# 1. Render the Guide using your custom loader
# Wrap it in an expander if you don't want it taking up the whole screen
with st.expander("📖 View Bruh-App Guide"):
    render_markdown_guide("bruhapp_guide.md")

# 2. Load Data
with st.spinner("Fetching latest messages from Dropbox..."):
    df = load_data()

# 3. Data Insights (The human-readable stats)
if not df.empty:
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Messages", f"{len(df):,}")
    
    with col2:
        # Get latest timestamp from actual data (most accurate)
        latest_msg_time = df['Timestamp'].max()
        human_time = latest_msg_time.strftime("%A, %b %d, %Y at %I:%M %p UTC")
        st.write("**Latest Message In Data:**")
        st.info(f"🕒 {human_time}")
    st.divider()
else:
    st.error("Dataframe is empty. Please check your source file and link.")

# 4. Preview
with st.expander("View Latest 10 Rows"):
    st.dataframe(df.tail(10))
