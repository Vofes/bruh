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
        # Load the entire file immediately
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
    # Prepare Raw View: Only Author (1) and Message (3)
    display_df = full_df.copy()
    if len(display_df.columns) >= 4:
        # Keep Author and Message columns for the viewer
        viewable_df = display_df[[display_df.columns[1], display_df.columns[3]]]
    else:
        viewable_df = display_df

    with st.sidebar:
        st.header("🔍 Viewport (UI Only)")
        st.info("These lines do NOT affect the bot check. They only control what you see on screen.")
        view_start = st.number_input("Display Start Row", value=0, min_value=0)
        view_end = st.number_input("Display End Row", value=len(full_df), min_value=0)
        
        st.header("⚙️ Bot Logic (Global)")
        st.info("The bot will scan the WHOLE file starting from this number.")
        anchor_num = st.number_input("Starting Bruh #", value=311925)
        jump_limit = st.number_input("Jump Limit", value=500)
        
        st.divider()
        show_v = st.checkbox("Show Success Log", value=True)
        run_check = st.button("🚀 Run Full Validation", width='stretch')

    # --- THE ENGINE (Always runs on the TOTAL dataframe) ---
    def validate_entire_file(df, start_num, limit):
        pattern = re.compile(r'^bruh\s+(\d+)', re.IGNORECASE)
        all_mistakes, all_successes = [], []
        
        active_status = False
        current_target = None
        last_valid_num = None
        recent_authors = []

        # We iterate over the FULL dataframe regardless of viewport
        for i, row in df.iterrows():
            try:
                author = str(row.iloc[1])
                raw_msg = str(row.iloc[3]).strip()
                match = pattern.match(raw_msg)
                if not match: continue
                
                found_num = int(match.group(1))

                # Logic: Find the anchor anywhere in the file
                if not active_status:
                    if found_num == start_num:
                        active_status = True
                        current_target = found_num + 1
                        last_valid_num = found_num
                        recent_authors = [author]
                        all_successes.append({"Line": i, "Author": author, "Msg": raw_msg, "Status": "ANCHOR"})
                    continue

                # Normal Validation Sequence
                if found_num == last_valid_num: continue

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
        
        # Return global results
        cols_m = ["Line", "Author", "Msg", "Reason"]
        cols_s = ["Line", "Author", "Msg", "Status"]
        res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
        res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
        
        return res_m, res_s, active_status

    # --- MAIN EXECUTION ---
    if run_check:
        # Step 1: Run Global Validation
        df_m_all, df_v_all, anchor_found = validate_entire_file(full_df, anchor_num, jump_limit)

        # Step 2: Filter results based ONLY on the User's Viewport lines
        # This keeps the math global but the view local.
        df_m_view = df_m_all[(df_m_all['Line'] >= view_start) & (df_m_all['Line'] <= view_end)]
        df_v_view = df_v_all[(df_v_all['Line'] >= view_start) & (df_v_all['Line'] <= view_end)]

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📄 Raw Data View")
            # The viewport only slices the UI here
            st.dataframe(viewable_df.iloc[view_start:view_end], width='stretch', height=600)

        with col2:
            st.subheader("📊 Results in View")
            
            if not anchor_found:
                st.error(f"❌ Anchor Bruh #{anchor_num} not found in the entire file.")
            else:
                st.success(f"✅ Global Scan Complete. Results below are filtered to lines {view_start}-{view_end}.")
            
            t_err, t_ok = st.tabs(["❌ Mistakes", "✅ Success Log"])
            
            with t_err:
                st.metric("Mistakes in View", len(df_m_view))
                st.dataframe(df_m_view, width='stretch')
            
            with t_ok:
                if show_v:
                    st.metric("Valid Bruhs in View", len(df_v_view))
                    st.dataframe(df_v_view, width='stretch')
                else:
                    st.info("Success log hidden.")

else:
    st.info("Awaiting CSV data. Check your Streamlit Secrets.")
