import streamlit as st
import pandas as pd
import requests
from collections import Counter
import io

# https://drive.google.com/file/d//view?usp=drivesdk

# --- CONFIG ---
# PASTE YOUR GOOGLE DRIVE FILE ID HERE
FILE_ID = '1OF-SHDDp0dVdfXSm-rEifvkx5hWLBPa6' 

st.set_page_config(page_title="Bruh Partner Tracker", page_icon="🧪")

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

@st.cache_data(show_spinner=False)
def download_large_gdrive_file(file_id):
    """Downloads large files from GDrive by bypassing the virus scan warning."""
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={'id': file_id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)
    
    # Read the content into a pandas dataframe
    return pd.read_csv(io.BytesIO(response.content), header=None, 
                       names=['id', 'user', 'time', 'msg'], low_memory=False)

# --- UI ---
st.title("🧪 Bruh Partner Test")
target_user = st.sidebar.text_input("Username to check", value="vofes")
num_to_show = st.sidebar.number_input("Partners to show", min_value=1, value=10)

try:
    with st.spinner("Accessing 100MB Google Drive file..."):
        df = download_large_gdrive_file(FILE_ID)
    
    # 1. Logic: Filter for 'bruh'
    bruh_mask = df['msg'].str.strip().str.lower().str.startswith('bruh', na=False)
    bruh_users = df[bruh_mask]['user'].tolist()
    
    # 2. Logic: Find Neighbors
    target_count = 0
    partners = Counter()
    total_matches = 0
    
    for i in range(len(bruh_users)):
        if str(bruh_users[i]).lower() == target_user.lower():
            target_count += 1
            # Above
            if i > 0:
                above = str(bruh_users[i-1])
                if above.lower() != target_user.lower():
                    partners[above] += 1
                    total_matches += 1
            # Below
            if i < len(bruh_users) - 1:
                below = str(bruh_users[i+1])
                if below.lower() != target_user.lower():
                    partners[below] += 1
                    total_matches += 1

    # 3. Results
    st.success("Analysis Complete!")
    c1, c2 = st.columns(2)
    c1.metric(f"Bruhs by {target_user}", target_count)
    c2.metric("Partner Interactions", total_matches)
    
    st.subheader(f"Top {num_to_show} Partners")
    results = pd.DataFrame(partners.most_common(num_to_show), columns=["Username", "Count"])
    st.table(results)

except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.info("Check if your File ID is correct and 'Anyone with the link' is enabled.")
