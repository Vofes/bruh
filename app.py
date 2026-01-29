import streamlit as st
import pandas as pd
import re
import gdown
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Bruh Bot Check", page_icon="🤖", layout="wide")

@st.cache_data(show_spinner="Loading Data...")
def load_full_data(d_id):
    if not d_id: return None
    url = f'https://drive.google.com/uc?export=download&id={d_id}'
    output = "temp_data.csv"
    try:
        gdown.download(url, output, quiet=True)
        # Using python engine for better compatibility with messy CSVs
        df = pd.read_csv(output, on_bad_lines='skip', engine='python', encoding='utf-8-sig')
        if os.path.exists(output): os.remove(output)
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None

# --- UI & INPUTS ---
drive_id = st.secrets.get("DRIVE", "")
full_df = load_full_data(drive_id)

if full_df is not None:
    with st.sidebar:
        st.header("🔍 Viewport Settings")
        st.info("These limits filter your VIEW, not the validation math.")
        view_start = st.number_input("View Start (Row Index)", value=0, min_value=0)
        view_end = st.number_input("View End (Row Index)", value=len(full_df), min_value=0)
        
        st.header("⚙️ Bot Logic")
        anchor_num = st.number_input("Starting Bruh # (Scan Anchor)", value=311925)
        jump_limit = st.number_input("Jump Limit", value=500)
        
        st.divider()
        show_v = st.checkbox("Show Success Log", value=True)
        run_check = st.button("🚀 Run Full Validation", use_container_width=True)

    # --- THE ENGINE (Always runs on full_df) ---
    def validate_entire_file(df, start_num, limit):
        pattern = re.compile(r'^bruh\s+(\d+)', re.IGNORECASE)
        
        # Initialize lists to avoid empty DataFrames without columns
        all_mistakes = []
        all_successes = []
        
        is_active = False
        current_target = None
        last_valid_num = None
        recent_authors = []

        for i, row in df.iterrows():
            try:
                # Basic validation that row has enough columns
                if len(row) < 4: continue
                
                author = str(row.iloc[1])
                raw_msg = str(row.iloc[3]).strip()
                match = pattern.match(raw_msg)
                if not match: continue
                
                found_num = int(match.group(1))

                # Phase 1: Search for the anchor anywhere in the file
                if not is_active:
                    if found_num == start_num:
                        is_active = True
                        current_target = found_num + 1
                        last_valid_num = found_num
                        recent_authors = [author]
                        all_successes.append({"Line": i, "Author": author, "Msg": raw_msg, "Status": "ANCHOR"})
                    continue

                # Phase 2: Sequential Validation
                if found_num == last_valid_num: 
                    continue

                if found_num == current_target:
                    if author in recent_authors:
                        all_mistakes.append({"Line": i, "Author": author, "Msg": raw_msg, "Reason": "2-Person Rule"})
                    else:
                        all_successes.append({"Line": i, "Author": author, "Msg": raw_msg, "Status": "VALID"})
                    
                    last_valid_num = found_num
                    current_target += 1
                    recent_authors = (recent_authors + [author])[-2:]
                else:
                    diff = found_num - current_target
                    if 0 < diff <= limit:
                        all_mistakes.append({"Line": i, "Author": author, "Msg": raw_msg, "Reason": f"Skip (+{diff})"})
                        current_target = found_num + 1
                        last_valid_num = found_num
                        recent_authors = [author]
                    else:
                        all_mistakes.append({"Line": i, "Author": author, "Msg": raw_msg, "Reason": "Troll/Invalid"})
            except:
                continue
        
        # Ensure we return DataFrames with consistent columns even if empty
        cols_m = ["Line", "Author", "Msg", "Reason"]
        cols_s = ["Line", "Author", "Msg", "Status"]
        
        res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
        res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
        
        return res_m, res_s

    # --- MAIN EXECUTION ---
    if run_check:
        df_m_all, df_v_all = validate_entire_file(full_df, anchor_num, jump_limit)

        # Safety Check: Only filter if 'Line' exists (DataFrame is not empty)
        df_m_filtered = df_m_all[(df_m_all['Line'] >= view_start) & (df_m_all['Line'] <= view_end)] if not df_m_all.empty else df_m_all
        df_v_filtered = df_v_all[(df_v_all['Line'] >= view_start) & (df_v_all['Line'] <= view_end)] if not df_v_all.empty else df_v_all

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader(f"📄 Raw Data View")
            st.caption(f"Displaying Row {view_start} to {view_end}")
            st.dataframe(full_df.iloc[view_start:view_end], use_container_width=True, height=600)

        with col2:
            st.subheader("📊 Validation Results")
            st.caption(f"Context: Full file scanned. Filters applied for view.")
            
            t_err, t_ok = st.tabs(["❌ Mistakes Found", "✅ Success Log"])
            
            with t_err:
                st.metric("Mistakes in View", len(df_m_filtered))
                st.dataframe(df_m_filtered, use_container_width=True)
            
            with t_ok:
                if show_v:
                    st.metric("Valid Bruhs in View", len(df_v_filtered))
                    st.dataframe(df_v_filtered, use_container_width=True)
                else:
                    st.info("Success log is disabled in settings.")

else:
    st.info("Waiting for CSV data... Please ensure your Google Drive ID is in Streamlit Secrets.")

