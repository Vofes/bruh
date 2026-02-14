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

        # --- 1. REPETITION & SWAP LOGIC ---
        if found_num == last_valid_num:
            # ONLY attempt a swap if the current winner is a 2-person violator
            # Check the most recent "Mistake" to see if it was a 2-person rule on THIS number
            can_fix_2p = False
            for m in reversed(all_mistakes):
                if m["Reason"] == "2-Person Rule" and m["Status"] == "Active":
                    m_val = pattern.match(m["Msg"])
                    if m_val and int(m_val.group(1)) == found_num:
                        # Found a 2-person error on this number! 
                        # If THIS new person (author) is different from the person who caused the error...
                        if author != m["Author"]:
                            m["Status"] = f"Fixed (Swap by {i})"
                            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                            recent_authors = [author]
                            can_fix_2p = True
                        break
                # Only check back a few mistakes to keep it relevant
                if len(all_mistakes) - all_mistakes.index(m) > 5: break
            
            if not can_fix_2p and not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Repetition (0)", "Status": "Active"})
            continue

        # --- 2. TARGET MATCH ---
        if found_num == current_target:
            if author in recent_authors:
                # This is the 2-Person Rule. We mark it as a mistake.
                # It stays "Active" unless a Repetition (above) fixes it.
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule", "Status": "Active"})
            else:
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                last_valid_num, current_target = found_num, found_num + 1
                recent_authors = [author]

        # --- 3. JUMPS/ROLLBACKS ---
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
