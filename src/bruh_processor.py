import pandas as pd
import re

def process_bruh_logic(df, start_num, end_num=0, max_jump=1500, filter_mode=1):
    """
    filter_mode: 
    1 = Show All (Audit Mode)
    2 = No Consensus (Hide N/A)
    3 = Only Active (High Priority)
    """
    pattern = re.compile(r'(?i)^bruh\s+(\d+)')
    cols_m = ["Line", "Author", "Msg", "Reason", "Status", "Debug"]
    cols_s = ["Line", "Author", "Msg", "Status"]

    # --- PRE-FILTER: Noise-Resistant Processing ---
    # We strip out chat messages immediately so the lookahead only sees bruhs
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
    
    # Author Tracking
    recent_authors = [] 
    last_valid_author = None # The person who was correct BEFORE a jump
    
    # Gap Tracking
    target_to_line_map = {} 

    for idx, item in enumerate(bruh_rows):
        i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
        
        # Stop if we hit the user-defined end number
        if end_num != 0 and found_num > end_num: break

        # --- INITIALIZATION ---
        if not active_status:
            if found_num == start_num:
                active_status, last_valid_num, current_target = True, found_num, found_num + 1
                last_valid_author = author
                recent_authors = [author]
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            continue

        # --- CONSENSUS CHECK ---
        lookahead = bruh_rows[idx+1 : idx+4]
        is_verified = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
        diff = found_num - last_valid_num
        
        history_list = sorted(list(target_to_line_map.keys()))
        recovery_anchor = history_list[0] if history_list else current_target
        debug_info = f"Targ:{current_target}|Anch:{recovery_anchor}|Verif:{is_verified}"

        # --- STEP 1: SURGICAL FIXER (Timeline Stitching) ---
        if is_verified and found_num in target_to_line_map:
            if found_num != current_target:
                origin_line = target_to_line_map[found_num]
                
                # RECOVERY STITCH: Combine the person from before the mess with the person fixing it
                recent_authors = [last_valid_author, author] if last_valid_author else [author]
                
                reason = "Fixer (RB)" if diff < 0 else "Fixer (JP)"
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"{reason} ({diff:+})", "Status": "Fixer", "Debug": debug_info})
                
                # Surgical Wipe: Only mark mistakes from this specific timeline as fixed
                for m in all_mistakes:
                    if m["Status"] == "Active" and origin_line <= m["Line"] < i:
                        m["Status"] = f"Fixed (by {i})"
                
                # Clean up history map
                target_to_line_map = {t: l for t, l in target_to_line_map.items() if l < origin_line}
            else:
                # This was a target match that happened to be in history (rare)
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                if found_num in target_to_line_map: del target_to_line_map[found_num]
                recent_authors = (recent_authors + [author])[-2:]

            last_valid_num, current_target = found_num, found_num + 1
            last_valid_author = author
            continue

        # --- STEP 2: REPETITION CHECK (-0) ---
        if found_num == last_valid_num:
            fixed_via_swap = False
            for m in reversed(all_mistakes):
                if m["Reason"] == "2-Person Rule" and m["Status"] == "Active":
                    if author != m["Author"]:
                        m["Status"] = f"Fixed (Swap by {i})"
                        all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                        recent_authors = (recent_authors[:-1] + [author])[-2:]
                        fixed_via_swap = True
                        break
            if not fixed_via_swap:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Repetition", "Status": "N/A", "Debug": debug_info})
            continue

        # --- STEP 3: TARGET MATCH (Normal Flow) ---
        if found_num == current_target:
            if author in recent_authors:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule", "Status": "Active", "Debug": debug_info})
                if not is_verified: continue 
            
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            last_valid_author = author
            recent_authors = (recent_authors + [author])[-2:]

# --- STEP 1: SURGICAL FIXER (Timeline Stitching) ---
        is_fixer_step = False
        if is_verified and found_num in target_to_line_map:
            is_fixer_step = True
            if found_num != current_target:
                origin_line = target_to_line_map[found_num]
                recent_authors = [last_valid_author, author] if last_valid_author else [author]
                
                reason = "Fixer (RB)" if diff < 0 else "Fixer (JP)"
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"{reason} ({diff:+})", "Status": "Fixer", "Debug": debug_info})
                
                for m in all_mistakes:
                    if m["Status"] == "Active" and origin_line <= m["Line"] < i:
                        m["Status"] = f"Fixed (by {i})"
                
                target_to_line_map = {t: l for t, l in target_to_line_map.items() if l < origin_line}
            else:
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                if found_num in target_to_line_map: del target_to_line_map[found_num]
                recent_authors = (recent_authors + [author])[-2:]

            last_valid_num, current_target = found_num, found_num + 1
            last_valid_author = author
            continue

        # --- STEP 2: REPETITION CHECK ---
        # Added 'and not is_fixer_step' to prevent Fixers being called Repetitions
        if found_num == last_valid_num and not is_fixer_step:
            fixed_via_swap = False
            # Only attempt a swap if there's an active 2-Person Rule mistake to fix
            for m in reversed(all_mistakes):
                if m["Reason"] == "2-Person Rule" and m["Status"] == "Active":
                    # Ensure the person swapping isn't the same person who made the mistake
                    if author != m["Author"]:
                        m["Status"] = f"Fixed (Swap by {i})"
                        all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                        recent_authors = (recent_authors[:-1] + [author])[-2:]
                        fixed_via_swap = True
                        break
            
            if not fixed_via_swap:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Repetition", "Status": "N/A", "Debug": debug_info})
            continue
        # --- STEP 5: INVALID / NO CONSENSUS ---
        else:
            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Invalid ({diff:+})", "Status": "N/A", "Debug": debug_info})

    # --- FINAL FILTERING ---
    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    
    if filter_mode == 2:
        res_m = res_m[res_m["Status"] != "N/A"]
    elif filter_mode == 3:
        res_m = res_m[res_m["Status"] == "Active"]
        
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    
    # Calculate unique successful counts (CORRECT rows only)
    unique_successful = len(res_s[res_s["Status"] == "CORRECT"])
    
    return res_m, res_s, active_status, last_valid_num, unique_successful
