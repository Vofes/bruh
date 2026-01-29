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
        df = pd.read_csv(output, on_bad_lines='skip', engine='python', encoding='utf-8-sig')
        if os.path.exists(output): os.remove(output)
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None

drive_id = st.secrets.get("DRIVE", "")
full_df = load_full_data(drive_id)

if full_df is not None:
    # Prepare Raw View: Only Author (1) and Message (3)
    display_df = full_df.copy()
    if len(display_df.columns) >= 4:
        viewable_df = display_df[[display_df.columns[1], display_df.columns[3]]]
    else:
        viewable_df = display_df

    with st.sidebar:
        st.header("🔍 Viewport (UI Only)")
        view_start = st.number_input("Display Start Row", value=0, min_value=0)
        view_end = st.number_input("Display End Row", value=len(full_df), min_value=0)
        
        st.header("⚙️ Bot Logic (Global)")
        anchor_num = st.number_input("Starting Bruh #", value=311925)
        jump_limit = st.number_input("Jump Limit", value=500)
        
        st.divider()
        show_v = st.checkbox("Show Success Log", value=True)
        run_check = st.button("🚀 Run Full Validation", width='stretch')

    def validate_with_consensus(df, start_num, limit):
        pattern = re.compile(r'^bruh\s+(\d+)', re.IGNORECASE)
        
        # Pre-filter all "bruh" messages to make "looking ahead" easier
        bruh_rows = []
        for i, row in df.iterrows():
            try:
                msg = str(row.iloc[3]).strip()
                match = pattern.match(msg)
                if match:
                    bruh_rows.append({
                        "index": i,
                        "author": str(row.iloc[1]),
                        "msg": msg,
                        "num": int(match.group(1))
                    })
            except: continue

        all_mistakes, all_successes = [], []
        active_status = False
        current_target = None
        last_valid_num = None
        recent_authors = []

        # Iterate through our filtered list of bruh messages
        for idx, item in enumerate(bruh_rows):
            i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]

            if not active_status:
                if found_num == start_num:
                    active_status = True
                    current_target = found_num + 1
                    last_valid_num = found_num
                    recent_authors = [author]
                    all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "ANCHOR"})
                continue

            if found_num == last_valid_num: continue

            # CASE 1: PERFECT MATCH
            if found_num == current_target:
                if author in recent_authors:
                    all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule"})
                else:
                    all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "VALID"})
                
                last_valid_num = found_num
                current_target += 1
                recent_authors = (recent_authors + [author])[-2:]

            # CASE 2: POTENTIAL SKIP
            else:
                diff = found_num - current_target
                
                # Check for consensus (look at next 3 bruhs)
                is_consensus = False
                if 0 < diff <= limit:
                    lookahead = bruh_rows[idx+1 : idx+4]
                    if len(lookahead) == 3:
                        # If the next 3 follow the NEW sequence: found_num+1, +2, +3
                        if (lookahead[0]["num"] == found_num + 1 and 
                            lookahead[1]["num"] == found_num + 2 and 
                            lookahead[2]["num"] == found_num + 3):
                            is_consensus = True

                if is_consensus:
                    all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Confirmed Skip (+{diff})"})
                    current_target = found_num + 1
                    last_valid_num = found_num
                    recent_authors = [author] # Reset rules on confirmed skip
                else:
                    # Not consensus or massive jump = Skip Attempt (Invalid)
                    all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Invalid/Skip Attempt"})

        return pd.DataFrame(all_mistakes), pd.DataFrame(all_successes), active_status

    if run_check:
        df_m_all, df_v_all, anchor_found = validate_with_consensus(full_df, anchor_num, jump_limit)

        df_m_view = df_m_all[(df_m_all['Line'] >= view_start) & (df_m_all['Line'] <= view_end)]
        df_v_view = df_v_all[(df_v_all['Line'] >= view_start) & (df_v_all['Line'] <= view_end)]

        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("📄 Raw Data View")
            st.dataframe(viewable_df.iloc[view_start:view_end], width='stretch', height=600)

        with col2:
            st.subheader("📊 Results in View")
            if not anchor_found:
                st.error(f"❌ Anchor Bruh #{anchor_num} not found.")
            
            t_err, t_ok = st.tabs(["❌ Mistakes", "✅ Success Log"])
            with t_err:
                st.metric("Mistakes in View", len(df_m_view))
                st.dataframe(df_m_view, width='stretch')
            with t_ok:
                if show_v:
                    st.metric("Valid Bruhs in View", len(df_v_view))
                    st.dataframe(df_v_view, width='stretch')
