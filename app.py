import streamlit as st
import pandas as pd
import re
import gdown
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Bruh Bot Check", page_icon="🤖", layout="wide")
st.title("🤖 Bruh Chain Bot Check")

# --- DATA FETCHING (CACHED) ---
drive_id = st.secrets.get("DRIVE", "")

@st.cache_data(show_spinner="Fetching CSV...")
def get_data(d_id):
    if not d_id: return None
    url = f'https://drive.google.com/uc?export=download&id={d_id}'
    output = "temp.csv"
    try:
        gdown.download(url, output, quiet=True)
        df = pd.read_csv(output, on_bad_lines='skip', engine='python', encoding='utf-8-sig')
        if os.path.exists(output): os.remove(output)
        return df
    except:
        return None

raw_data = get_data(drive_id)

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.header("Settings")
    if raw_data is not None:
        total_rows = len(raw_data)
        s_line = st.number_input("Start Line Index", 0, total_rows, 0)
        e_line = st.number_input("End Line Index", 0, total_rows, min(500000, total_rows))
    
    st.divider()
    s_num = st.number_input("Starting Bruh #", value=311925)
    j_lim = st.number_input("Jump Limit", value=500)
    
    st.divider()
    show_v = st.checkbox("Show Success Log", value=True)
    force_start = st.checkbox("Auto-Anchor (Start at first bruh found)", value=True)
    
    run_btn = st.button("🚀 Run Analysis", use_container_width=True)

# --- VALIDATION ENGINE ---
def run_validation(df, target_start, limit, auto_anchor):
    pattern = re.compile(r'^bruh\s+(\d+)', re.IGNORECASE)
    mistakes, valid_logs = [], []
    valid_count = 0
    
    is_active = False
    current_target = target_start
    last_valid_num = None
    recent_authors = []

    for i, row in df.iterrows():
        try:
            author = str(row.iloc[1])
            raw_msg = str(row.iloc[3]).strip()
            match = pattern.match(raw_msg)
            if not match: continue
            
            found_num = int(match.group(1))

            # --- ACTIVATION LOGIC ---
            if not is_active:
                # Option A: Find specific number | Option B: Just take the first bruh found
                if (auto_anchor) or (found_num == target_start):
                    is_active = True
                    current_target = found_num + 1
                    last_valid_num = found_num
                    recent_authors = [author]
                    valid_logs.append({"Line": i, "Author": author, "Msg": raw_msg, "Status": "START"})
                continue

            # --- VALIDATION LOGIC ---
            if found_num == last_valid_num: continue

            if found_num == current_target:
                if author in recent_authors:
                    mistakes.append({"Line": i, "Author": author, "Msg": raw_msg, "Reason": "2-Person Rule"})
                else:
                    valid_count += 1
                    valid_logs.append({"Line": i, "Author": author, "Msg": raw_msg, "Status": "VALID"})
                
                last_valid_num = found_num
                current_target += 1
                recent_authors = (recent_authors + [author])[-2:]

            else:
                diff = found_num - current_target
                if 0 < diff <= limit:
                    mistakes.append({"Line": i, "Author": author, "Msg": raw_msg, "Reason": f"Skip (+{diff})"})
                    current_target = found_num + 1
                    last_valid_num = found_num
                    recent_authors = [author]
                else:
                    mistakes.append({"Line": i, "Author": author, "Msg": raw_msg, "Reason": "Troll/Invalid"})

        except: continue
    return pd.DataFrame(mistakes), pd.DataFrame(valid_logs), valid_count

# --- MAIN DISPLAY ---
if raw_data is not None:
    if run_btn:
        # 1. Independent Slice
        sliced_df = raw_data.iloc[int(s_line):int(e_line)]
        
        # 2. Run Validation
        df_m, df_v, count = run_validation(sliced_df, s_num, j_lim, force_start)
        
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader("📄 Raw CSV Data")
            st.dataframe(sliced_df, use_container_width=True, height=500)
            
        with col_right:
            st.subheader("📊 Analysis Results")
            st.metric("Total Valid", count)
            
            tab_err, tab_ok = st.tabs(["❌ Mistakes", "✅ Success Log"])
            with tab_err:
                if not df_m.empty:
                    st.dataframe(df_m, use_container_width=True)
                else:
                    st.success("Perfect chain in this range!")
            with tab_ok:
                if not df_v.empty:
                    st.dataframe(df_v, use_container_width=True)
                else:
                    st.warning("No valid bruhs found. Ensure the slice contains 'bruh' messages.")
else:
    st.info("Please verify your Google Drive ID in Streamlit Secrets.")

