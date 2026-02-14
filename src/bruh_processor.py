import pandas as pd
import re

def process_bruh_logic(df, start_num, end_num=0, max_jump=1500, filter_mode=1):
    pattern = re.compile(r'(?i)^bruh\s+(\d+)')
    cols_m = ["Line", "Author", "Msg", "Reason", "Status", "Debug"]
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
    last_known_good_author = None 
    target_to_line_map = {} 

    for idx, item in enumerate(bruh_rows):
        i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
        if end_num != 0 and found_num > end_num: break

        if not active_status:
            if found_num == start_num:
                active_status, last_valid_num, current_target = True, found_num, found_num + 1
                last_known_good_author, recent_authors = author, [author]
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            continue

        lookahead = bruh_rows[idx+1 : idx+4]
        is_verified = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
        diff = found_num - last_valid_num
        debug_info = f"Targ:{current_target}|Auths:{recent_authors}"

        # --- PRIORITY 1: TIMELINE RECOVERY (The Fixer) ---
        if is_verified and found_num in target_to_line_map:
            origin_line = target_to_line_map[found_num]
            recent_authors = [last_known_good_author, author] if last_known_good_author else [author]
            
            # Restore the descriptive labels (Jump vs Rollback)
            label = "Fixer (RB)" if diff < 0 else "Fixer (JP)"
            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"{label} ({diff:+})", "Status": "Fixer", "Debug": debug_info})
            
            for m in all_mistakes:
                if m["Status"] == "Active" and origin_line <= m["Line"] < i:
                    m["Status"] = f"Fixed (by {i})"
            
            target_to_line_map = {t: l for t, l in target_to_line_map.items() if l < origin_line}
            last_valid_num, current_target = found_num, found_num + 1
            last_known_good_author = author
            continue 

# --- PRIORITY 2: REPETITIONS & IMMEDIATE SWAPS ---
        if found_num == last_valid_num:
            fixed_via_swap = False
            
            # IMPROVED SWAP: Only look at the most recent mistake to avoid "Time Travel" fixes
            if all_mistakes:
                last_m = all_mistakes[-1]
                if last_m["Reason"] == "2-Person Rule" and last_m["Status"] == "Active":
                    # Check if this person is different from the one who messed up
                    if author != last_m["Author"]:
                        last_m["Status"] = f"Fixed (Swap by {i})"
                        all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                        # Update memory: The new valid author replaces the rule-breaker
                        recent_authors = [recent_authors[0], author] if len(recent_authors) > 1 else [author]
                        fixed_via_swap = True
            
            if not fixed_via_swap:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Repetition", "Status": "N/A", "Debug": debug_info})
            continue

        
        # --- PRIORITY 3: TARGET MATCH (Normal Chain) ---
        if found_num == current_target:
            if author in recent_authors:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule", "Status": "Active", "Debug": debug_info})
                if not is_verified: continue 
            
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            last_known_good_author = author
            recent_authors = (recent_authors + [author])[-2:]
            continue

        # --- PRIORITY 4: JUMPS/ROLLBACKS (Verified Breaks) ---
        if is_verified:
            target_to_line_map[current_target] = i
            label = "Jump" if diff > 0 else "Rollback"
            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"{label} ({diff:+})", "Status": "Active", "Debug": debug_info})
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = [author]
            continue

        # --- PRIORITY 5: INVALID ---
        all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Invalid ({diff:+})", "Status": "N/A", "Debug": debug_info})

    # Filtering logic remains the same
    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    if filter_mode == 2: res_m = res_m[res_m["Status"] != "N/A"]
    elif filter_mode == 3: res_m = res_m[res_m["Status"] == "Active"]
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    return res_m, res_s, active_status, last_valid_num, len(res_s[res_s["Status"] == "CORRECT"])
