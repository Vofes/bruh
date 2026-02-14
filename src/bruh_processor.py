import pandas as pd
import re

def process_bruh_logic(df, start_num, end_num=0, max_jump=1500, filter_mode=1):
    pattern = re.compile(r'(?i)^bruh\s+(\d+)')
    cols_m = ["Line", "Author", "Msg", "Reason", "Status", "Debug"]
    cols_s = ["Line", "Author", "Msg", "Status"]

    # --- PRE-FILTER ---
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
    last_valid_num = None
    current_target = None
    
    # Advanced Memory Tracking
    recent_authors = [] 
    anchor_author = None # The "Golden Author" from BEFORE the mess
    target_to_line_map = {} 

    for idx, item in enumerate(bruh_rows):
        i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
        
        if end_num != 0 and found_num > end_num: break

        # 1. INITIALIZATION
        if not active_status:
            if found_num == start_num:
                active_status, last_valid_num, current_target = True, found_num, found_num + 1
                anchor_author, recent_authors = author, [author]
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            continue

        # 2. CONSENSUS CHECK
        lookahead = bruh_rows[idx+1 : idx+4]
        is_verified = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
        diff = found_num - last_valid_num

        # --- PRIORITY 1: THE FIXER (Timeline Recovery) ---
        if is_verified and found_num in target_to_line_map:
            origin_line = target_to_line_map[found_num]
            
            # THE STITCH: Force memory to [Anchor, Current Fixer]
            # This deletes "jumper" authors from memory completely.
            if anchor_author and anchor_author != author:
                recent_authors = [anchor_author, author]
            else:
                recent_authors = [author]
            
            label = "Fixer (RB)" if diff < 0 else "Fixer (JP)"
            all_mistakes.append({
                "Line": i, "Author": author, "Msg": msg, 
                "Reason": f"{label} ({diff:+})", "Status": "Fixer", 
                "Debug": f"STITCHED:{anchor_author}->{author}"
            })
            
            # Surgical Fix: Mark mistakes within this specific gap as fixed
            for m in all_mistakes:
                if m["Status"] == "Active" and origin_line <= m["Line"] < i:
                    m["Status"] = f"Fixed (by {i})"
            
            target_to_line_map = {t: l for t
