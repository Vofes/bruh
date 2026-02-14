import pandas as pd
import re

def process_bruh_logic(df, start_num, end_num=0, max_jump=1500, hide_invalid=False):
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
    target_history = [] 

    for idx, item in enumerate(bruh_rows):
        i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
        if end_num != 0 and found_num > end_num: break

        if not active_status:
            if found_num == start_num:
                active_status, last_valid_num, current_target = True, found_num, found_num + 1
                target_history = [current_target]
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                recent_authors = [author]
            continue

        lookahead = bruh_rows[idx+1 : idx+4]
        is_verified = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
        diff = found_num - last_valid_num
        
        # PRE-PROCESS DEBUG: What did the bot think BEFORE reading this message?
        recovery_anchor = target_history[0] if target_history else current_target
        debug_info = f"Targ:{current_target}|Anch:{recovery_anchor}|Hist:{target_history[:2]}|Verif:{is_verified}"

        # --- STEP 1: FIXER CHECK (PRIORITY) ---
        # We check if this number is in our history BEFORE updating targets
        if is_verified and found_num in target_history:
            # If it matches a historical target but NOT the current one, it's a Fixer
            if found_num != current_target:
                reason = "Fixer (RB)" if diff < 0 else "Fixer (JP)"
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"{reason} ({diff:+})", "Status": "Fixer", "Debug": debug_info})
                for m in all_mistakes:
                    if m["Status"] == "Active" and m["Line"] < i:
                        m["Status"] = f"Fixed (by {i})"
            else:
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})

            last_valid_num, current_target = found_num, found_num + 1
            target_history = [current_target] # Reset history to the clean path
            recent_authors = (recent_authors + [author])[-2:]
            continue

        # --- STEP 2: REPETITION ---
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
            if not fixed_via_swap and not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Repetition", "Status": "N/A", "Debug": debug_info})
            continue

        # --- STEP 3: REGULAR TARGET MATCH ---
        if found_num == current_target:
            if author in recent_authors:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule", "Status": "Active", "Debug": debug_info})
                if not is_verified: continue 
            
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            target_history = [current_target] 
            recent_authors = (recent_authors + [author])[-2:]

        # --- STEP 4: NEW BREAKS (JUMP/ROLLBACK) ---
        elif is_verified:
            reason = "Jump" if diff > 0 else "Rollback"
            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"{reason} ({diff:+})", "Status": "Active", "Debug": debug_info})
            
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            # Save the target we SHOULD have had before moving on
            if current_target not in target_history:
                target_history.append(current_target)
            
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = [author]

        # --- STEP 5: INVALID ---
        else:
            if not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Invalid ({diff:+})", "Status": "N/A", "Debug": debug_info})

    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    if hide_invalid:
        res_m = res_m[res_m["Status"] != "N/A"]
        
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    return res_m, res_s, active_status, last_valid_num, len(res_s[res_s["Status"] == "CORRECT"])
