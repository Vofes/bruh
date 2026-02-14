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

    for idx, item in enumerate(bruh_rows):
        i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
        if end_num != 0 and found_num > end_num: break

        if not active_status:
            if found_num == start_num:
                active_status, last_valid_num, current_target = True, found_num, found_num + 1
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                recent_authors = [author]
            continue

        lookahead = bruh_rows[idx+1 : idx+4]
        is_verified = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
        diff = found_num - last_valid_num

        # --- 1. THE DUPLICATE SWAP (Your A-3, B-3 Logic) ---
        if found_num == last_valid_num:
            # Check if the PREVIOUS person (who got the credit) caused a 2-person rule issue
            # Or if swapping to THIS person helps the chain flow better
            swapped = False
            for prev_s in reversed(all_successes):
                if prev_s["Status"] == "CORRECT" and prev_s["Line"] < i:
                    m_prev = pattern.match(prev_s["Msg"])
                    if m_prev and int(m_prev.group(1)) == found_num:
                        # We found the guy who currently has credit for this number.
                        # If the NEW person (current 'author') is different, we swap!
                        if author != prev_s["Author"]:
                            prev_s["Status"] = f"Fixed (Overwritten by Line {i})"
                            # Move the old success to mistakes so you can see it
                            all_mistakes.append({
                                "Line": prev_s["Line"], 
                                "Author": prev_s["Author"], 
                                "Msg": prev_s["Msg"], 
                                "Reason": "Overwritten for 2-Person Rule Flow",
                                "Status": f"Fixed (by {i})"
                            })
                            
                            # Give credit to the new guy
                            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                            recent_authors = [author]
                            swapped = True
                        break
            
            if swapped: continue
            
            if not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Repetition (0)", "Status": "Active"})
            continue

        # --- 2. TARGET MATCH ---
        if found_num == current_target:
            if author in recent_authors:
                # Flag it, but we might 'Fix' it later if a duplicate B-target appears
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule", "Status": "Active"})
            else:
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                last_valid_num, current_target = found_num, found_num + 1
                recent_authors = [author]

        # --- 3. JUMPS/ROLLBACKS (Basic) ---
        elif is_verified and abs(diff) <= max_jump:
            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Jump/Rollback ({diff:+})", "Status": "Active"})
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = [author]

        # --- 4. INVALID ---
        else:
            if not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Invalid ({diff:+})", "Status": "Active"})

    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    
    unique_count = len(res_s[res_s["Status"] == "CORRECT"])
    return res_m, res_s, active_status, last_valid_num, unique_count
