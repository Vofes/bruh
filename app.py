import streamlit as st
import pandas as pd
import re
import gdown
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Bruh Bot Check", layout="wide")
st.title("🤖 Bruh Chain Validator")

# --- SIDEBAR: MANUAL INPUTS ---
st.sidebar.header("Settings & Auth")

# Put the TOKEN/URL here manually in the app
drive_url_input = st.sidebar.text_input("Drive Download URL", type="password", help="Paste the direct download link here", value="1OF-SHDDp0dVdfXSm-rEifvkx5hWLBPa6")
start_input = st.sidebar.text_input("Starting Bruh Number", value="311925")
jump_input = st.sidebar.text_input("Troll Jump Limit", value="500")

# Validation logic remains the same
def run_validation(csv_path, start_num, limit):
    pattern = re.compile(r'^(bruh|Bruh)\s(\d+)(\s.*)?$')
    df = pd.read_csv(csv_path)
    mistakes, is_active, valid_count = [], False, 0
    current_target, last_valid, authors = start_num + 1, start_num, []

    for i, row in df.iterrows():
        try:
            author, raw_msg = str(row[1]), str(row[3]).strip()
            match = pattern.match(raw_msg)
            if not match: continue
            found_num = int(match.group(2))

            if not is_active:
                if found_num == start_num:
                    is_active, authors = True, [author]
                continue

            if found_num == last_valid: continue

            if found_num == current_target:
                if author in authors:
                    mistakes.append({"Line": i+2, "Author": author, "Msg": raw_msg, "Reason": "2-Person Rule"})
                else:
                    valid_count += 1
                current_target += 1
                last_valid = found_num
                authors = (authors + [author])[-2:]
            elif 0 < (found_num - current_target) <= limit:
                mistakes.append({"Line": i+2, "Author": author, "Msg": raw_msg, "Reason": "Skip"})
                current_target, last_valid, authors = found_num + 1, found_num, [author]
            else:
                mistakes.append({"Line": i+2, "Author": author, "Msg": raw_msg, "Reason": "Invalid/Troll"})
        except: continue
    return pd.DataFrame(mistakes), valid_count

# --- BUTTON TO EXECUTE ---
if st.button("🚀 Fetch & Validate"):
    if not drive_url_input:
        st.error("Please provide the Drive URL in the sidebar!")
    else:
        with st.spinner("Downloading..."):
            try:
                output = "temp_logs.csv"
                # Use the manual URL from the text box
                gdown.download(drive_url_input, output, quiet=True)
                
                df_mistakes, total_valid = run_validation(output, int(start_input), int(jump_input))
                
                st.metric("Valid Count", total_valid)
                st.dataframe(df_mistakes)
                
                if os.path.exists(output): os.remove(output)
            except Exception as e:
                st.error(f"Error: {e}")
