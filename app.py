import streamlit as st
import pandas as pd
import re
import gdown
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Bruh Bot Check", page_icon="🤖", layout="wide")

st.title("🤖 Bruh Chain Bot Check")

# --- SIDEBAR & CACHING ---
st.sidebar.header("1. Data Source")
drive_id = st.secrets.get("DRIVE", "")

@st.cache_data(show_spinner="Downloading from Drive...")
def download_csv(d_id):
    if not d_id:
        return None
    url = f'https://drive.google.com/uc?export=download&id={d_id}'
    output = "temp_logs.csv"
    gdown.download(url, output, quiet=True)
    
    # Security/Permission Check
    with open(output, 'r', encoding='utf-8', errors='ignore') as f:
        if "<!DOCTYPE html>" in f.read(200):
            if os.path.exists(output): os.remove(output)
            return "AUTH_ERROR"
            
    df = pd.read_csv(output, on_bad_lines='skip', engine='python', encoding='utf-8-sig')
    if os.path.exists(output): os.remove(output)
    return df

# Initialize Data
raw_data = download_csv(drive_id)

if raw_data is None:
    st.error("❌ DRIVE ID missing in Secrets.")
    st.stop()
elif isinstance(raw_data, str) and raw_data == "AUTH_ERROR":
    st.error("❌ Access Denied. Check Google Drive sharing permissions (Anyone with link).")
    st.stop()

# --- VALIDATION ENGINE ---
def run_validation(df, start_num, limit, include_trolls):
    pattern = re.compile(r'^bruh\s+(\d+)', re.IGNORECASE)
    
    mistakes = []
    valid_logs = []
    valid_count = 0
    is_active = False
    current_target = None
    last_valid_num = None
    recent_authors = [] 

    # We use .values for faster iteration
    for i, row in df.iterrows():
        try:
            line_id = i  # The index from the sliced dataframe
            author = str(row.iloc[1])
            raw_msg = str(row.iloc[3]).strip()
            
            match = pattern.match(raw_msg)
            if not match: continue
                
            found_num = int(match.group(1))

            if not is_active:
                if found_num == start_num:
                    is_active = True
                    current_target = found_num + 1
                    last_valid_num = found_num
                    recent_authors = [author]
                    valid_logs.append({"Line": line_id, "Author": author, "Message": raw_msg, "Status": "START", "Expected": start_num, "Found": found_num})
                continue

            if found_num == last_valid_num:
                continue 

            is_breaking_rule = author in recent_authors

            if found_num == current_target:
                if is_breaking_rule:
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
                elif include_trolls:
                    mistakes.append({"Line": line_id, "Author": author, "Message": raw_msg, "Reason": "Invalid/Troll", "Expected": current_target, "Found": found_num})
        except:
            continue

    return pd.DataFrame(mistakes), pd.DataFrame(valid_logs), valid_count

# --- USER INTERFACE FORM ---
with st.sidebar.form("config_form"):
    st.header("2. Settings")
    s_line = st.number_input("Start Line Index", value=0)
    e_line = st.number_input("End Line Index", value=len(raw_data))
    s_num = st.number_input("Starting Bruh #", value=311925)
    j_lim = st.number_input("Jump Limit", value=500)
    
    st.divider()
    show_v = st.checkbox("Show Success Log", value=False)
    show_t = st.checkbox("Include Trolls", value=False)
    
    submit = st.form_submit_button("🚀 Run Analysis")

# --- RESULTS DISPLAY ---
if submit:
    # Slice data based on form input
    sliced_df = raw_data.iloc[int(s_line):int(e_line)]
    
    df_mistakes, df_valid, total_valid = run_validation(sliced_df, s_num, j_lim, show_t)
    
    col_raw, col_results = st.columns([1, 1])

    with col_raw:
        st.subheader("📄 Raw CSV Slice")
        st.dataframe(sliced_df, use_container_width=True, height=600)

    with col_results:
        st.subheader("📊 Analysis")
        m1, m2 = st.columns(2)
        m1.metric("Valid Count", total_valid)
        m2.metric("Mistakes", len(df_mistakes))
        
        tab1, tab2 = st.tabs(["❌ Mistakes", "✅ Valid Log"])
        
        with tab1:
            if not df_mistakes.empty:
                st.dataframe(df_mistakes, use_container_width=True)
                st.download_button("📥 Download Mistakes", df_mistakes.to_csv(index=False), "mistakes.csv")
            else:
                st.success("No mistakes found!")

        with tab2:
            if show_v:
                if not df_valid.empty:
                    st.dataframe(df_valid, use_container_width=True)
                else:
                    st.info("No valid messages found in this range. Check your 'Starting Bruh #' or line range.")
            else:
                st.warning("Success log is hidden. Enable 'Show Success Log' in sidebar.")
