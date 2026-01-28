import streamlit as st
import pandas as pd
import re
import gdown
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Bruh Bot Check", page_icon="🤖", layout="wide")

st.title("🤖 Bruh Chain Bot Check")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Validator Settings")

# Text inputs for configuration
start_input = st.sidebar.text_input("Starting Bruh Number", value="311925")
jump_input = st.sidebar.text_input("Troll Jump Limit", value="500")

# Convert inputs to integers safely
try:
    START_BRUH = int(start_input)
    JUMP_LIMIT = int(jump_input)
except ValueError:
    st.sidebar.error("Please enter valid numbers!")
    START_BRUH = 311925
    JUMP_LIMIT = 500

# Fetch the Drive Secret
DRIVE_URL = st.secrets.get("DRIVE", "")

# --- VALIDATION ENGINE ---
def run_validation(csv_path, start_num, limit):
    # Regex: 'bruh' or 'Bruh' + 1 space + numbers + (optional space + anything)
    pattern = re.compile(r'^(bruh|Bruh)\s(\d+)(\s.*)?$')
    
    # Read CSV (Assuming Author is Col 1 and Message is Col 3)
    df = pd.read_csv(csv_path)
    mistakes = []
    valid_count = 0
    
    is_active = False
    current_target = start_num + 1
    last_valid_num = start_num
    recent_authors = [] 

    for i, row in df.iterrows():
        try:
            author = str(row[1])
            raw_msg = str(row[3]).strip()
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
                continue # Ignore repeats

            is_double_bruh = author in recent_authors

            if found_num == current_target:
                if is_double_bruh:
                    mistakes.append({"Line": line_id, "Author": author, "Message": raw_msg, "Reason": "2-Person Rule"})
                else:
                    valid_count += 1
                
                last_valid_num = found_num
                current_target += 1
                recent_authors = (recent_authors + [author])[-2:] # Keep last 2

            else:
                diff = found_num - current_target
                
                # Small Skip
                if 0 < diff <= limit:
                    mistakes.append({"Line": line_id, "Author": author, "Message": raw_msg, "Reason": f"Skip detected (+{diff})"})
                    current_target = found_num + 1
                    last_valid_num = found_num
                    recent_authors = [author] 
                
                # Ignore troll jumps
                else:
                    mistakes.append({"Line": line_id, "Author": author, "Message": raw_msg, "Reason": "Invalid Number (Ignored)"})
        except:
            continue

    return pd.DataFrame(mistakes), valid_count

# --- MAIN UI ---
if not DRIVE_URL:
    st.warning("⚠️ No 'DRIVE' secret found. Please add your link to the Streamlit secrets.")
else:
    if st.button("🚀 Run Bot Check"):
        with st.spinner(f"Scanning for mistakes starting from {START_BRUH}..."):
            try:
                output = "temp_logs.csv"
                gdown.download(DRIVE_URL, output, quiet=True, fuse=False)
                
                df_mistakes, total_valid = run_validation(output, START_BRUH, JUMP_LIMIT)
                
                st.divider()
                c1, c2 = st.columns(2)
                c1.metric("Valid Bruhs", total_valid)
                c2.metric("Mistakes to Fix", len(df_mistakes))
                
                if not df_mistakes.empty:
                    st.subheader("📋 Mistake Log")
                    st.dataframe(df_mistakes, use_container_width=True)
                    
                    csv_data = df_mistakes.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Mistakes CSV", csv_data, "bruh_report.csv", "text/csv")
                else:
                    st.success("Chain is perfect!")
                
                if os.path.exists(output):
                    os.remove(output)
                    
            except Exception as e:
                st.error(f"Error: {e}")

st.caption(f"Currently monitoring sequences following: {START_BRUH} -> {START_BRUH+1}")
