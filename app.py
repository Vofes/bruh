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
    gdown.download(url, output, quiet=True)
    df = pd.read_csv(output, on_bad_lines='skip', engine='python', encoding='utf-8-sig')
    if os.path.exists(output): os.remove(output)
    return df

# --- UI & INPUTS ---
drive_id = st.secrets.get("DRIVE", "")
full_df = load_full_data(drive_id)

if full_df is not None:
    with st.sidebar:
        st.header("🔍 Viewport Settings")
        st.info("These lines control what you SEE, not where the bot starts.")
        view_start = st.number_input("View Start Line", value=0)
        view_end = st.number_input("View End Line", value=len(full_df))
        
        st.header("⚙️ Bot Logic")
        anchor_num = st.number_input("Starting Bruh #", value=311925)
        jump_limit = st.number_input("Jump Limit", value=500)
        
        st.divider()
        show_v = st.checkbox("Show Success Log", value=True)
        run_check = st.button("🚀 Run Full Validation", use_container_width=True)

    # --- THE ENGINE (Always runs on full_df) ---
    def validate_entire_file(df, start_num, limit):
        pattern = re.compile(r'^bruh\s+(\d+)', re.IGNORECASE)
        all_mistakes = []
        all_successes = []
        
        is_active = False
        current_target = None
        last_valid_num = None
        recent_authors = []

        for i, row in df.iterrows():
            try:
                author = str(row.iloc[1])
                raw_msg = str(row.iloc[3]).strip()
                match = pattern.match(raw_msg)
                if not match: continue
                
                found_num = int(match.group(1))

                # Phase 1: Finding the Anchor anywhere in the file
                if not is_active:
                    if found_num == start_num:
                        is_active = True
                        current_target = found_num + 1
                        last_valid_num = found_num
                        recent_authors = [author]
                        all_successes.append({"Line": i, "Author": author, "Msg": raw_msg, "Status": "ANCHOR"})
                    continue

                # Phase 2: Sequential Validation
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
            except: continue
        
        return pd.DataFrame(all_mistakes), pd.DataFrame(all_successes)

    # --- MAIN EXECUTION ---
    if run_check:
        df_m_all, df_v_all = validate_entire_file(full_df, anchor_num, jump_limit)

        # Filter the results based on the User's Viewport
        df_m_filtered = df_m_all[(df_m_all['Line'] >= view_start) & (df_m_all['Line'] <= view_end)]
        df_v_filtered = df_v_all[(df_v_all['Line'] >= view_start) & (df_v_all['Line'] <= view_end)]

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader(f"📄 Raw Data (Lines {view_start}-{view_end})")
            st.dataframe(full_df.iloc[view_start:view_end], use_container_width=True, height=600)

        with col2:
            st.subheader("📊 Validation Results (Filtered)")
            st.write(f"Results shown only for lines **{view_start}** to **{view_end}**")
            
            t_err, t_ok = st.tabs(["❌ Mistakes Found", "✅ Valid Chain"])
            
            with t_err:
                st.metric("Mistakes in view", len(df_m_filtered))
                st.dataframe(df_m_filtered, use_container_width=True)
            
            with t_ok:
                if show_v:
                    st.metric("Valid bruhs in view", len(df_v_filtered))
                    st.dataframe(df_v_filtered, use_container_width=True)
                else:
                    st.info("Success log is hidden.")

else:
    st.warning("Please check your Drive ID and Secrets.")
