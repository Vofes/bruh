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
# Format in Secrets: DRIVE = "your_file_id_here"
drive_id = st.secrets.get("DRIVE", "")

start_input = st.sidebar.text_input("Starting Bruh Number", value="311925")
jump_input = st.sidebar.text_input("Troll Jump Limit", value="500")

# Toggle for Troll/Invalid messages
show_trolls = st.sidebar.checkbox("Show 'Invalid/Troll' in output", value=False)

# --- VALIDATION ENGINE ---
def run_validation(csv_path, start_num, limit, include_trolls):
    pattern = re.compile(r'^(bruh|Bruh)\s(\d+)(\s.*)?$')
    
    try:
        # Robust parsing to handle extra commas in messages
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
            author = str(row.iloc[1])
            raw_msg = str(row.iloc[3]).strip()
            line_id = i + 2 
            
            match = pattern.match(raw_msg)
            if not match:
                continue
                
            found_num = int(match.group(2))

            if not is_active:
                if found_num == start_num:
                    is_active = True
                    recent_authors = [author]
                continue

            if found_num == last_valid_num:
                continue 

            is_double_bruh = author in recent_authors

            if found_num == current_target:
                if is_double_bruh:
                    mistakes.append({"Line": line_id, "Author": author, "Message": raw_msg, "Reason": "2-Person Rule"})
                else:
                    valid_count += 1
                
                last_valid_num = found_num
                current_target += 1
                recent_authors = (recent_authors + [author])[-2:]

            else:
                diff = found_num - current_target
                
                # Small Skip
                if 0 < diff <= limit:
                    mistakes.append({"Line": line_id, "Author": author, "Message": raw_msg, "Reason": f"Skip detected (+{diff})"})
                    current_target = found_num + 1
                    last_valid_num = found_num
                    recent_authors = [author] 
                
                # Massive Jump or Backwards (Troll)
                else:
                    if include_trolls:
                        mistakes.append({"Line": line_id, "Author": author, "Message": raw_msg, "Reason": "Invalid/Troll Number"})
        except Exception:
            continue

    return pd.DataFrame(mistakes), valid_count

# --- EXECUTION ---
if st.button("🚀 Run Bot Check"):
    if not drive_id:
        st.error("❌ DRIVE token not found in Streamlit Secrets!")
    else:
        direct_url = f'https://drive.google.com/uc?export=download&id={drive_id}'
        
        with st.spinner("Downloading and scanning logs..."):
            try:
                output = "temp_logs.csv"
                gdown.download(direct_url, output, quiet=True)
                
                # Security Check for HTML responses
                with open(output, 'r', encoding='utf-8', errors='ignore') as f:
                    chunk = f.read(200)
                    if "<!DOCTYPE html>" in chunk or "<html" in chunk:
                        st.error("❌ Access Denied. Check Drive sharing permissions.")
                        os.remove(output)
                        st.stop()

                df_mistakes, total_valid = run_validation(
                    output, 
                    int(start_input), 
                    int(jump_input), 
                    show_trolls
                )
                
                st.divider()
                c1, c2 = st.columns(2)
                c1.metric("Valid Bruhs", total_valid)
                c2.metric("Reported Mistakes", len(df_mistakes))
                
                if not df_mistakes.empty:
                    st.subheader("📋 Mistake Log")
                    st.dataframe(df_mistakes, use_container_width=True)
                    
                    csv_data = df_mistakes.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Report CSV", csv_data, "bruh_mistakes.csv", "text/csv")
                else:
                    st.success("The chain is perfect!")
                
                if os.path.exists(output):
                    os.remove(output)
                    
            except Exception as e:
                st.error(f"Error: {e}")
