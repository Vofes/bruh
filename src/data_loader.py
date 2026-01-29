import streamlit as st
import pandas as pd
import gdown
import os

@st.cache_data(show_spinner=False)
def get_botcheck_data():
    # Centralized Drive ID - Update here to change file
    drive_id = st.secrets.get("DRIVE", "YOUR_ID_HERE")
    url = f'https://drive.google.com/uc?export=download&id={drive_id}'
    output = "temp_data.csv"
    
    try:
        gdown.download(url, output, quiet=True)
        # Using utf-8-sig to handle special characters in names
        df = pd.read_csv(output, on_bad_lines='skip', engine='python', encoding='utf-8-sig')
        if os.path.exists(output): os.remove(output)
        return df
    except Exception as e:
        st.error(f"Loader Error: {e}")
        return None
