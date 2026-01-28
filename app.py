import streamlit as st
import pandas as pd
import requests
from collections import Counter
import io

# https://drive.google.com/file/d//view?usp=drivesdk

# --- CONFIG ---
# PASTE YOUR GOOGLE DRIVE FILE ID HERE
FILE_ID = '1OF-SHDDp0dVdfXSm-rEifvkx5hWLBPa6'  

st.set_page_config(page_title="Bruh Partner Tracker", page_icon="📈", layout="wide")

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
    
    # Process the CSV data
    # quotechar='"' handles commas inside messages
    # on_bad_lines='skip' prevents crashes if a row is corrupted
    return pd.read_csv(
        io.BytesIO(response.content), 
        header=None, 
        names=['id', 'user', 'time', 'msg'], 
        quotechar='"', 
        on_bad_lines='skip', 
        low_memory=False
    )

# --- SIDEBAR ---
st.sidebar.header("Search Settings")
target_user = st.sidebar.text_input("Username to analyze", value="vofes")
num_to_show = st.sidebar.number_input("Partners to display (Recommended: 10)", min_value=1, value=10)

# --- MAIN PAGE ---
st.title("📈 Community Bruh Tracker")
st.markdown(f"Currently tracking partners for: **{target_user}**")

try:
    with st.spinner("Downloading and processing 100MB chat log..."):
        df = download_large_gdrive_file(FILE_ID)
    
    # 1. Logic: Filter for 'bruh' at start of message (case-insensitive)
    # We use .astype(str) to ensure no errors with empty messages
    bruh_mask = df['msg'].astype(str).str.strip().str.lower().str.startswith('bruh', na=False)
    bruh_only_df = df[bruh_mask]
    bruh_users = bruh_only_df['user'].tolist()
    
    # 2. Logic: Count target's bruhs and find neighbors
    target_count = 0
    partners = Counter()
    total_interactions = 0
    
    # We loop through the list of users who sent "bruh" messages
    for i in range(len(bruh_users)):
        current_name = str(bruh_users[i])
        
        if current_name.lower() == target_user.lower():
            target_count += 1
            
            # Check Neighbor ABOVE
            if i > 0:
                above = str(bruh_users[i-1])
                if above.lower() != target_user.lower():
                    partners[above] += 1
                    total_interactions += 1
            
            # Check Neighbor BELOW
            if i < len(bruh_users) - 1:
                below = str(bruh_users[i+1])
                if below.lower() != target_user.lower():
                    partners[below] += 1
                    total_interactions += 1

    # --- DISPLAY ---
    st.divider()
    m1, m2 = st.columns(2)
    m1.metric(f"Total Bruhs by {target_user}", target_count)
    m2.metric("Total Partner Connections", total_interactions)

    if target_count > 0:
        st.subheader(f"Top {num_to_show} Partners")
        # Sort and limit the results
        top_partners = partners.most_common(num_to_show)
        
        if top_partners:
            results_df = pd.DataFrame(top_partners, columns=["Partner Username", "Count"])
            # Display the table
            st.table(results_df)
            
            # Export option
            csv_export = results_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Results as CSV", data=csv_export, 
                               file_name=f"{target_user}_partners.csv", mime="text/csv")
        else:
            st.info("User found, but they have no 'bruh' neighbors.")
    else:
        st.warning(f"No messages starting with 'bruh' were found for user: {target_user}")

except Exception as e:
    st.error(f"Failed to process logs: {e}")
    st.info("Check if your File ID is correct and 'Anyone with the link' is enabled in Google Drive.")
