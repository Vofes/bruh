import pandas as pd
import streamlit as st
import requests

# The Direct Download Link
DB_LINK = "https://www.dropbox.com/scl/fi/ine04ie48l60j6pj804px/chat_logs.csv?rlkey=3bhydbcigk7ndawwrdee7pv8f&st=igoinb9c&dl=1"

@st.cache_data(ttl=3600)
def load_chat_data():
    """Fetches data from Dropbox instead of local disk."""
    # We use pd.read_csv directly on the URL
    df = pd.read_csv(DB_LINK, low_memory=False, on_bad_lines='skip')
    
    # Basic cleanup that your app likely expects
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
    return df
