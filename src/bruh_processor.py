import pandas as pd
import re

def process_bruh_logic(df, start_num, end_num=0, max_jump=1500, hide_invalid=False):
    pattern = re.compile(r'(?i)^bruh\s+(\d+)')
    cols_m = ["Line", "Author", "Msg", "Reason", "Status"]
    cols_s = ["Line", "Author", "Msg", "Status"]

    bruh_rows = []
    for i, row in df.iterrows():
        try:
            msg = str(row.iloc[3]).strip()
            match = pattern.match(msg)
            if match:
                bruh_rows.append({"index": i, "author": str(row.iloc[1]), "msg": msg, "num": int(match.group(1))})
        except: continue

    all_mistakes, all_successes = [], []
    active_status, last_valid_num, current_target = False, None, None
    recent_authors = []
    FIX_WINDOW = 4000 
    
    # We track what the target WAS before the chain went off the rails
    pre_mistake_target = None 

    for idx, item in enumerate(bruh_rows):
        i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
        if end_num != 0 and found_num > end_num: break

        if not active_status:
            if found_num == start_num:
                active_status, last_valid_num, current_target = True, found_num, found_num + 1
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                recent_authors = [author]
                pre_mistake_target = current_target
            continue

        lookahead = bruh_rows[idx+1 : idx+4]
        is_verified = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
        diff = found_num - last_valid_num

        # --- 1. REPETITION ---
        if found_num == last_valid_num:
            if not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Repetition (0)", "Status": "Active"})
            continue

        # --- 2. TARGET MATCH (Normal or Fix) ---
        if found_num == current_target or (is_verified and found_num == pre_mistake_target):
            
            # If it's the pre_mistake_target, it's a FIX
            is_fixing_move = (found_num == pre_mistake_target and found_num != current_target)
            
            if author in recent_authors:
                saved = False
                for prev_idx in range(idx - 1, max(0, idx - 10), -1):
                    prev_item = bruh_rows[prev_idx]
                    if prev_item["num"] == last_valid_num and prev_item["author"] != author:
                        all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT (Saved)"})
                        recent_authors = [author]
                        last_valid_num, current_target = found_num, found_num + 1
                        if not is_fixing_move: pre_mistake_target = current_target
                        saved = True
                        break
                if not saved:
                    all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule", "Status": "Active"})
                    continue # Don't update target if blocked by 2-person rule
            
            # Successful Move
            if is_fixing_move:
                # MARK PREVIOUS AS FIXED
                fix_reason = "Fixing Rollback" if diff < 0 else "Fixing Jump"
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"{fix_reason} ({diff:+})", "Status": "Active"})
                
                # Sweep: Find the first Active mistake and mark everything from there to here as Fixed
                for m in all_mistakes:
                    if m["Status"] == "Active" and m["Line"] < i:
                        m["Status"] = f"Fixed (by {i})"
            
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            pre_mistake_target = current_target # Reset the anchor
            recent_authors = [author]

        # --- 3. VERIFIED JUMP / ROLLBACK (Non-Fixing) ---
        elif is_verified and abs(diff) <= max_jump:
            # If this is the FIRST mistake in a while, remember what the target SHOULD have been
            if pre_mistake_target == current_target:
                pre_mistake_target = current_target 
            
            base_reason = "Jump" if diff > 0 else "Rollback"
            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"{base_reason} ({diff:+})", "Status": "Active"})
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = [author]

        # --- 4. INVALID ---
        else:
            if not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Invalid ({diff:+})", "Status": "Active"})

    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    unique_count = len(res_s[res_s["Status"].str.contains("CORRECT")])
    return res_m, res_s, active_status, last_valid_num, unique_count
