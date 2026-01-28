import streamlit as st
import pandas as pd
import re
import gdown
import os
import io

# --- PAGE CONFIG ---
st.set_page_config(page_title="Bruh Bot Check", page_icon="🤖", layout="wide")

st.title("🤖 Bruh Chain Bot Check")
st.markdown("Validates the community 'bruh' sequence using the Discord log CSV.")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Configuration")

# Ask for the File ID (Token) instead of the full URL
drive_id = st.sidebar.text_input("Google Drive File ID", type="password", help="The long string of characters in your Drive share link", value="1OF-SHDDp0dVdfXSm-rEifvkx5hWLBPa6")
start_input = st.sidebar.text_input("Starting Bruh Number", value="311925")
jump_input = st.sidebar.text_input("Troll Jump Limit", value="500")

# --- VALIDATION ENGINE ---
def run_validation(csv_path, start_num, limit):
    # Matches 'bruh' or 'Bruh', one space, then digits. Allows extra text after.
    pattern = re.compile(r'^(bruh|Bruh)\s(\d+)(\s.*)?$')
    
    # We use on_bad_lines='skip' to prevent crashes from extra commas in messages
    try:
        df = pd.read_csv(csv_path, on_bad_lines='skip', engine='python', encoding='utf-8-sig')
    except Exception as e:
        st.error(f"Failed to parse CSV: {e}")
        return pd.DataFrame(), 0
    
    mistakes = []
    valid_count = 0
    is_active = False
    current_target = start_num + 1
    last_valid_num = start_num
    recent_authors = [] 

    for i, row in df.iterrows():
        try:
            # Using .iloc ensures we grab columns by position regardless of header names
            # Col 1: Author, Col 3: Message
            author = str(row.iloc[1])
            raw_msg = str(row.iloc[3]).strip()
            line_id = i + 2 
            
            match = pattern.match(raw_msg)
            if not match:
                continue
                
            found_num = int(match.group(2))

            # Phase 1: Search for anchor
            if not is_active:
                if found_num == start_num:
                    is_active = True
                    recent_authors = [author]
                continue

            # Phase 2: Logic
            if found_num == last_valid_num:
                continue # Ignore duplicate numbers

            is_double_bruh = author in recent_authors

            if found_num == current_target:
                if is_double_bruh:
                    mistakes.append({"Line": line_id, "Author": author, "Message": raw_msg, "Reason": "2-Person Rule"})
                else:
                    valid_count += 1
                
                last_valid_num = found_num
                current_target += 1
                recent_authors = (recent_authors + [author])[-2:] # Track last 2 people

            else:
                diff = found_num - current_target
                
                # Small Skip
                if 0 < diff <= limit:
                    mistakes.append({"Line": line_id, "Author": author, "Message": raw_msg, "Reason": f"Skip detected (+{diff})"})
                    current_target = found_num + 1
                    last_valid_num = found_num
                    recent_authors = [author] 
                
                # Massive Jump or Backwards
                else:
                    mistakes.append({"Line": line_id, "Author": author, "Message": raw_msg, "Reason": "Invalid/Troll Number"})
        except Exception:
            continue

    return pd.DataFrame(mistakes), valid_count

# --- EXECUTION ---
if st.button("🚀 Run Bot Check"):
    if not drive_id:
        st.error("Please enter the Google Drive File ID in the sidebar.")
    else:
        # Construct the direct download URL from the ID
        direct_url = f'https://drive.google.com/uc?export=download&id={drive_id}'
        
        with st.spinner("Downloading and scanning logs..."):
            try:
                output = "temp_logs.csv"
                gdown.download(direct_url, output, quiet=True)
                
                # Verify if the download is actually a webpage (Access Denied)
                with open(output, 'r', encoding='utf-8', errors='ignore') as f:
                    chunk = f.read(200)
                    if "<!DOCTYPE html>" in chunk or "<html" in chunk:
                        st.error("❌ Access Denied. Make sure the Drive file is set to 'Anyone with the link can view'.")
                        os.remove(output)
                        st.stop()

                # Convert inputs to integers
                start_val = int(start_input)
                jump_val = int(jump_input)

                df_mistakes, total_valid = run_validation(output, start_val, jump_val)
                
                # Display Results
                st.divider()
                c1, c2 = st.columns(2)
                c1.metric("Valid Bruhs", total_valid)
                c2.metric("Mistakes Recorded", len(df_mistakes))
                
                if not df_mistakes.empty:
                    st.subheader("📋 Mistake Log")
                    st.dataframe(df_mistakes, use_container_width=True)
                    
                    csv_data = df_mistakes.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Report CSV", csv_data, "bruh_mistakes.csv", "text/csv")
                else:
                    st.success("The chain is perfect! No mistakes found.")
                
                # Cleanup
                if os.path.exists(output):
                    os.remove(output)
                    
            except ValueError:
                st.error("Please ensure Start Number and Jump Limit are valid integers.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

st.divider()
st.caption("Instructions: Get your Google Drive file ID from the share link. Ensure the file is shared as 'Anyone with the link can view'.")
