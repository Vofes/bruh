import streamlit as st
import pandas as pd
from collections import Counter
import io

# --- PAGE CONFIG ---
st.set_page_config(page_title="Bruh Partner Tracker", page_icon="💬")

st.title("💬 Bruh Partner Tracker")
st.markdown("Analyze chat logs to find who 'bruhs' next to you.")

# --- SIDEBAR CONFIG ---
st.sidebar.header("Configuration")
target_user = st.sidebar.text_input("Username to search", value="vofes")
num_partners = st.sidebar.number_input("Amount of people to show (Recommended: 10)", 
                                      min_value=1, max_value=100, value=10)

# --- FILE UPLOADER ---
uploaded_file = st.file_uploader("Upload your chat log CSV (Up to 200MB)", type="csv")

if uploaded_file is not None:
    # We use pandas to read the 100MB file quickly
    with st.spinner('Processing large file...'):
        try:
            # Adjust names based on your chat log format
            df = pd.read_csv(uploaded_file, header=None, names=['id', 'user', 'timestamp', 'message'])
            
            # 1. Filter only valid 'bruh' messages (Case-insensitive)
            # We convert to string and check if it starts with 'bruh'
            is_bruh = df['message'].str.strip().str.lower().str.startswith('bruh', na=False)
            bruh_only_df = df[is_bruh].reset_index(drop=True)
            
            # 2. Extract users into a list for fast neighbor checking
            bruh_users = bruh_only_df['user'].tolist()
            
            target_bruh_count = 0
            partner_counts = Counter()
            total_partner_interactions = 0

            # 3. Analyze Neighbors
            for i in range(len(bruh_users)):
                current_user = str(bruh_users[i])
                
                if current_user.lower() == target_user.lower():
                    target_bruh_count += 1
                    
                    # Check partner ABOVE
                    if i > 0:
                        above = bruh_users[i-1]
                        if str(above).lower() != target_user.lower():
                            partner_counts[above] += 1
                            total_partner_interactions += 1
                            
                    # Check partner BELOW
                    if i < len(bruh_users) - 1:
                        below = bruh_users[i+1]
                        if str(below).lower() != target_user.lower():
                            partner_counts[below] += 1
                            total_partner_interactions += 1

            # --- DISPLAY RESULTS ---
            st.divider()
            col1, col2 = st.columns(2)
            col1.metric("User Bruhs", target_bruh_count)
            col2.metric("Total Partner Interactions", total_partner_interactions)

            # Get top partners
            top_partners = partner_counts.most_common(num_partners)
            
            if top_partners:
                st.subheader(f"Top {num_partners} Bruh Partners")
                # Create a clean table
                results_df = pd.DataFrame(top_partners, columns=["Partner Username", "Interaction Count"])
                st.table(results_df)
                
                # Download button for the results
                csv_data = results_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Results as CSV", data=csv_data, file_name="bruh_partners.csv", mime="text/csv")
            else:
                st.warning("No partners found for this user in the 'bruh' chain.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
else:
    st.info("Please upload a CSV file to begin.")
