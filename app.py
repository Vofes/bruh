import streamlit as st
import pandas as pd
import re
import gdown
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Bruh Bot Check", page_icon="🤖", layout="wide")

st.title("🤖 Bruh Chain Bot Check")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Configuration")

# Fetch Token ID from Streamlit Secrets
drive_id = st.secrets.get("DRIVE", "")

# Line Range Selection
st.sidebar.subheader("Line Range")
start_line = st.sidebar.number_input("Start Line Index", value=0, step=1)
end_line = st.sidebar.number_input("End Line Index", value=500000, step=1)

# Logic Settings
start_num = st.sidebar.text_input("Starting Bruh Number", value="311925")
jump_limit = st.sidebar.number_input("Troll Jump Limit", value=500)

# View Toggles
show_valid = st.sidebar.checkbox("Show Validated Bruhs (Success Log)", value=False)
show_trolls = st.sidebar.checkbox("Show 'Invalid/Troll' in output", value=False)

# --- VALIDATION ENGINE ---
def run_validation(df, start_num, limit, include_trolls):
    # Synchronized Regex with your local script
    pattern = re.compile(r'^bruh\s+(\d+)', re.IGNORECASE)
    
    mistakes = []
    valid_logs = []
    valid_count = 0
    is_active = False
    current_target = None
    last_valid_num = None
    recent_authors = [] 

    for i, row in df.iterrows():
        try:
            # Match index logic: df index + 2 usually matches Excel row numbers
            line_id = i + 2 
            author = str(row.iloc[1])
            raw_msg = str(row.iloc[3]).strip()
            
            match = pattern.match(raw_msg)
            if not match:
                continue
                
            found_num = int(match.group(1))

            # PHASE 1: SEARCHING FOR START
            if not is_active:
                if found_num == start_num:
                    is_active = True
                    current_target = found_num + 1
                    last_valid_num = found_num
                    recent_authors = [author]
                    # Log the start
                    valid_logs.append({"Line": line_id, "Author": author, "Message": raw_msg, "Status": "START ANCHOR"})
                continue

            # PHASE 2: VALIDATION
            if found_num == last_valid_num:
                continue 

            is_double_bruh = author in recent_authors

            if found_num == current_target:
                if is_double_bruh:
                    mistakes.append({"Line": line_id, "Author": author, "Message": raw_msg, "Reason": "2-Person Rule", "Expected": current_target, "Found": found_num})
                else:
                    valid_count += 1
                    valid_logs.append({"Line": line_id, "Author": author, "Message": raw_msg, "Status": "VALID", "Expected": current_target, "Found": found_num})
                
                last_valid_num = found_num
                current_target += 1
                recent_authors = (recent_authors + [author])[-2:]

            else:
                diff = found_num - current_target
                if 0 < diff <= limit:
                    mistakes.append({"Line": line_id, "Author": author, "Message": raw_msg, "Reason": f"Skip (+{diff})", "Expected": current_target, "Found": found_num})
                    current_target = found_num + 1
                    last_valid_num = found_num
                    recent_authors = [author] 
                else:
                    if include_trolls:
                        mistakes.append({"Line": line_id, "Author": author, "Message": raw_msg, "Reason": "Invalid/Troll", "Expected": current_target, "Found": found_num})
        except Exception:
            continue

    return pd.DataFrame(mistakes), pd.DataFrame(valid_logs), valid_count

# --- EXECUTION ---
if st.button("🚀 Run Bot Check"):
    if not drive_id:
        st.error("❌ DRIVE token not found in Streamlit Secrets!")
    else:
        direct_url = f'https://drive.google.com/uc?export=download&id={drive_id}'
        
        with st.spinner("Downloading logs..."):
            try:
                output = "temp_logs.csv"
                gdown.download(direct_url, output, quiet=True)
                
                # Check for Google Drive HTML error
                with open(output, 'r', encoding='utf-8', errors='ignore') as f:
                    if "<!DOCTYPE html>" in f.read(200):
                        st.error("❌ Access Denied. Check Drive sharing permissions.")
                        os.remove(output)
                        st.stop()

                # Load only the required slice
                full_df = pd.read_csv(output, on_bad_lines='skip', engine='python', encoding='utf-8-sig')
                sliced_df = full_df.iloc[int(start_line):int(end_line)]

                # Layout: Side by Side
                col_raw, col_results = st.columns([1, 1])

                with col_raw:
                    st.subheader("📄 Raw CSV Preview")
                    st.caption(f"Showing lines {start_line} to {end_line}")
                    st.dataframe(sliced_df, use_container_width=True)

                df_mistakes, df_valid, total_valid = run_validation(
                    sliced_df, 
                    int(start_num), 
                    int(jump_limit), 
                    show_trolls
                )
                
                with col_results:
                    st.subheader("📊 Analysis Results")
                    c1, c2 = st.columns(2)
                    c1.metric("Valid Bruhs", total_valid)
                    c2.metric("Mistakes", len(df_mistakes))
                    
                    if show_valid:
                        st.write("✅ **Valid Messages Log**")
                        st.dataframe(df_valid, use_container_width=True)
                    
                    if not df_mistakes.empty:
                        st.write("❌ **Mistake Log**")
                        st.dataframe(df_mistakes, use_container_width=True)
                        
                        csv_data = df_mistakes.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download Mistakes CSV", csv_data, "mistakes.csv", "text/csv")
                    else:
                        st.success("No mistakes found in this range!")
                
                if os.path.exists(output):
                    os.remove(output)
                    
            except Exception as e:
                st.error(f"Error during processing: {e}")
