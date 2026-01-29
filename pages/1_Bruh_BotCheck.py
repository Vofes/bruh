import streamlit as st
import os
import sys
import pandas as pd
import re

# Ensure the app can find the 'src' folder
sys.path.append(os.getcwd())

from src.bruh_processor import process_bruh_logic
from src.raw_viewer import render_raw_csv_view

# ... [Sidebar logic remains the same] ...

if run:
    # 1. BRAIN: Global Analysis
    res_m, res_s, found, last_val, unique_count = process_bruh_logic(df, start_bruh, end_bruh, jump_limit, hide_invalid)
    
    # 2. EXTRACTION LOGIC: Find every bruh NOT in 'Unique'
    # Category A: Those marked as CORRECT-FIX (Successes that got rolled back)
    excluded_fixes = res_s[res_s["Status"] == "CORRECT-FIX"].copy()
    excluded_fixes["Exclusion Reason"] = "Overwritten by Rollback"

    # Category B: Those marked as Jumps in Mistakes (Jump starters)
    excluded_jumps = res_m[res_m["Reason"].str.contains("Jump", na=False)].copy()
    excluded_jumps["Exclusion Reason"] = "Jump Entry (No Credit)"

    # Combine them into one "Lost Bruhs" list
    lost_bruhs = pd.concat([excluded_fixes, excluded_jumps], ignore_index=True)
    
    # Extract just the number for easier reading
    def extract_num(msg):
        match = re.search(r'bruh\s+(\d+)', str(msg), re.IGNORECASE)
        return int(match.group(1)) if match else 0
    
    if not lost_bruhs.empty:
        lost_bruhs["Bruh #"] = lost_bruhs["Msg"].apply(extract_num)
        lost_bruhs = lost_bruhs[["Line", "Author", "Bruh #", "Exclusion Reason"]].sort_values("Line")

    # 3. UI DISPLAY
    st.header("📊 Global Analysis")
    m1, m2, m3 = st.columns(3)
    m1.metric("Unique Successful", unique_count)
    m2.metric("Total Excluded", len(lost_bruhs))
    m3.metric("Final Chain Num", last_val if found else "N/A")

    st.divider()

    t1, t2, t3 = st.tabs(["✅ Unique (Credited)", "🔍 Excluded Bruh List", "❌ All Mistakes"])
    
    with t1:
        st.dataframe(res_s[res_s["Status"] == "CORRECT"], use_container_width=True)
        
    with t2:
        st.subheader("Numbers that didn't make the Unique cut")
        if not lost_bruhs.empty:
            st.info("The list below contains every bruh number that was detected but denied credit either because it was part of a jump or was fixed later.")
            st.dataframe(lost_bruhs, use_container_width=True)
        else:
            st.success("No excluded bruhs found! Every valid bruh got credit.")

    with t3:
        st.dataframe(res_m, use_container_width=True)
