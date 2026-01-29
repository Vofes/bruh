import pandas as pd
import streamlit as st

DB_LINK = st.secrets["DROPBOXLINK"]

@st.cache_data(ttl=3600)
def load_chat_data():
    """Fetches headerless data from Dropbox and prepares it for the processor."""
    # 1. Read with header=None to match the GitHub Action output
    df = pd.read_csv(DB_LINK, header=None, dtype=str, low_memory=False, on_bad_lines='skip')

    df.columns = ['MessageID', 'Author', 'Timestamp', 'Content'] + [f'extra_{i}' for i in range(len(df.columns)-4)]

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True, errors='coerce')
    df = df.dropna(subset=['Timestamp'])

    df['Content'] = df['Content'].fillna('').astype(str)
    return df
