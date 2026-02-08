import pandas as pd
import requests
import re
import streamlit as st

def get_raw_bruh_data(dropbox_url):
    # Dropbox workaround: change ?dl=0 to ?dl=1 to get direct download link
    direct_url = dropbox_url.replace("www.dropbox.com", "dl.dropboxusercontent.com").replace("?dl=0", "?dl=1")
    
    try:
        # Assuming the export is a CSV. Adjust to pd.read_json if it's JSON.
        df = pd.read_csv(direct_url)
        
        # Regex: find "bruh" + space + any digits
        # This will catch "bruh 1", "bruh 500", etc.
        pattern = r'^bruh\s+(\d+)$'
        
        # Filter messages that match the pattern
        # Replace 'content' and 'author' with the actual column names in your Dropbox file
        df['is_bruh'] = df['content'].str.contains(pattern, case=False, na=False, regex=True)
        bruh_df = df[df['is_bruh'] == True].copy()
        
        # Count bruhs per author
        leaderboard = bruh_df.groupby('author').size().reset_index(name='Bruh Count')
        return leaderboard.sort_values(by='Bruh Count', ascending=False)
    
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return pd.DataFrame()
