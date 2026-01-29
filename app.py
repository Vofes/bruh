import streamlit as st
import pandas as pd
import re
import gdown
import os
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Bruh Bot Check", page_icon="🤖", layout="wide")

@st.cache_data(show_spinner="Connecting to Google Drive...")
def load_full_data(d_id):
    if not d_id: return None
    url = f'https://drive.google.com/uc?export=download&id={d_id}'
    output = "temp_data.csv"
    try:
        gdown.download(url, output, quiet=True)
        df = pd.read_csv(output, on_bad_lines='skip', engine='python', encoding='utf-8-sig')
        if os.path.exists(output): os.remove(output)
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None

# --- UI & DATA LOADING ---
drive_id = st.secrets.get("DRIVE", "")
full_df = load_full_data(drive_id)

if full_df is not None:
    with st.sidebar:
        st.header("📂 View Settings")
        show_raw_view = st.checkbox("Show Raw CSV View", value=True)
        view_start = st.number_input("Display Start Row", value=0, min_value=0)
        view_end = st.number_input("Display End Row", value=len(full_df), min_value=0)
        
        st.header("⚙️ Bot Logic (Global)")
        anchor_num = st.number_input("Starting Bruh #", value=311925)
        
        st.divider()
        show_v = st.checkbox("Show Success Log", value=True)
        run_check = st.button("🚀 Run Full Validation", width='stretch')

    def validate_final(df, start_num):
        pattern = re.compile(r'^bruh\s+(\d+)', re.IGNORECASE)
        cols_m = ["Line", "Author", "Msg", "Reason"]
        cols_s = ["Line", "Author", "Msg", "Status"]

        # 1. Pre-filtering with progress bar
        bruh_rows = []
        progress_text = "Scanning messages for 'bruh' patterns..."
        my_bar = st.progress(0, text=progress_text)
        
        total_rows = len(df)
        for i, row in df.iterrows():
            # Update progress every 500 rows to save performance
            if i % 500 == 0:
                my_bar.progress(i / total_rows, text=progress_text)
            
            try:
                msg = str(row.iloc[3]).strip()
                match = pattern.match(msg)
                if match:
                    bruh_rows.append({
                        "index": i, "author": str(row.iloc[1]),
                        "msg": msg, "num": int(match.group(1))
                    })
            except: continue
        
        my_bar.empty() # Clear the bar after pre-filtering

        all_mistakes, all_successes = [], []
        active_status = False
        current_target, last_valid_num = None, None
        recent_authors = []

        # 2. Validation Loop
        status_box = st.empty()
        total_bruhs = len(bruh_rows)
        
        for idx, item in enumerate(bruh_rows):
            i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
            
            # Engagement: Show the user which number is being checked
            if idx % 10 == 0:
                status_box.caption(f"Validating sequence... currently at Bruh #{found_num}")

            if last_valid_num is not None and found_num == last_valid_num:
                continue

            if not active_status:
                if found_num == start_num:
                    past_nums = set(r["num"] for r in bruh_rows[:idx])
                    required = set(range(start_num - 10, start_num))
                    if required.issubset(past_nums):
                        active_status = True
                        current_target, last_valid_num = found_num + 1, found_num
                        recent_authors = [author]
                        all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "ANCHOR"})
                continue

            if found_num == current_target:
                if author in recent_authors:
                    all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule"})
                else:
                    all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "VALID"})
                last_valid_num, current_target = found_num, found_num + 1
                recent_authors = (recent_authors + [author])[-2:]
            else:
                lookahead = bruh_rows[idx+1 : idx+4]
                is_consensus = False
                if len(lookahead) == 3:
                    if (lookahead[0]["num"] == found_num + 1 and 
                        lookahead[1]["num"] == found_num + 2 and 
                        lookahead[2]["num"] == found_num + 3):
                        is_consensus = True

                if is_consensus:
                    diff = found_num - last_valid_num
                    label = "Jump" if diff > 0 else "Correction"
                    all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Confirmed {label} ({diff:+} from {last_valid_num})"})
                    last_valid_num, current_target = found_num, found_num + 1
                    recent_authors = [author]
                else:
                    all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Invalid / No Consensus"})

        status_box.empty()
        res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
        res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
        return res_m, res_s, active_status, last_valid_num

    if run_check:
        with st.spinner("Crunching numbers and verifying history..."):
            df_m_all, df_v_all, anchor_found, final_val = validate_final(full_df, anchor_num)

        # Filtering
        df_m_view = df_m_all[(df_m_all['Line'] >= view_start) & (df_m_all['Line'] <= view_end)] if not df_m_all.empty else df_m_all
        df_v_view = df_v_all[(df_v_all['Line'] >= view_start) & (df_v_all['Line'] <= view_end)] if not df_v_all.empty else df_v_all

        # --- SUMMARY DISPLAY ---
        st.divider()
        sum_col1, sum_col2 = st.columns(2)
        with sum_col1:
            if anchor_found:
                st.success(f"✅ Last Successfully Validated Bruh: **{final_val}**")
            else:
                st.error(f"❌ Anchor #{anchor_num} could not be verified.")
        
        # --- MAIN UI LAYOUT ---
        if show_raw_view:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.subheader("📄 Raw Data View")
                raw_display = full_df.iloc[view_start:view_end]
                if len(raw_display.columns) >= 4:
                    raw_display = raw_display[[raw_display.columns[1], raw_display.columns[3]]]
                st.dataframe(raw_display, width='stretch', height=600)
            res_col = col2
        else:
            res_col = st.container()

        with res_col:
            st.subheader("📊 Validation Results")
            t_err, t_ok = st.tabs(["❌ Mistakes", "✅ Success Log"])
            with t_err:
                st.metric("Mistakes in View", len(df_m_view))
                st.dataframe(df_m_view, width='stretch')
            with t_ok:
                if show_v:
                    st.metric("Valid Bruhs in View", len(df_v_view))
                    st.dataframe(df_v_view, width='stretch')
