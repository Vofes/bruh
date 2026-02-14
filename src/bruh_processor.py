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
    recent_authors = [] # This will now store the last 2 unique authors

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

        # --- 1. REPETITION & RETRO-FIXING ---
        if found_num == last_valid_num:
            fixed_via_swap = False
            # Check if there is an ACTIVE 2-person mistake for this same number
            for m in reversed(all_mistakes):
                if m["Reason"] == "2-Person Rule" and m["Status"] == "Active":
                    m_val_match = pattern.match(m["Msg"])
                    if m_val_match and int(m_val_match.group(1)) == found_num:
                        # If THIS new person (author) doesn't break the gap rule, swap them in!
                        if author not in recent_authors[:-1]: # Check against the sequence before that mistake
                            m["Status"] = f"Fixed (Swap by {i})"
                            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                            # Update recent authors: remove the "bad" one and add the "good" one
                            recent_authors = (recent_authors[:-1] + [author])[-2:]
                            fixed_via_swap = True
                        break
                if len(all_mistakes) - all_mistakes.index(m) > 10: break
            
            if not fixed_via_swap and not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Repetition (0)", "Status": "Active"})
            continue

        # --- 2. TARGET MATCH ---
        if found_num == current_target:
            # THE 2-PERSON GAP RULE: Must be at least 2 people between your bruhs
            # If your name is in the last 2 successful bruhers, you failed.
            if author in recent_authors:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule", "Status": "Active"})
            else:
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                last_valid_num, current_target = found_num, found_num + 1
                # Maintain the last 2 unique authors
                recent_authors = (recent_authors + [author])[-2:]

        # --- 3. JUMPS/ROLLBACKS ---
        elif is_verified and abs(found_num - last_valid_num) <= max_jump:
            diff = found_num - last_valid_num
            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Jump/Rollback ({diff:+})", "Status": "Active"})
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = [author]

        # --- 4. INVALID ---
        else:
            if not hide_invalid:
                diff = found_num - last_valid_num
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Invalid ({diff:+})", "Status": "Active"})

    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    
    unique_count = len(res_s[res_s["Status"] == "CORRECT"])
    return res_m, res_s, active_status, last_valid_num, unique_count
