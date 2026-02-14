import pandas as pd
import re

def process_bruh_logic(df, start_num, end_num=0, max_jump=1500, hide_invalid=False):
    pattern = re.compile(r'(?i)^bruh\s+(\d+)')
    cols_m = ["Line", "Author", "Msg", "Reason"]
    cols_s = ["Line", "Author", "Msg", "Status"]

    # 1. PRE-PROCESS: Get all potential bruhs first
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
    active_status, last_valid_num, current_target = False, None, None
    recent_authors = [] # Track the 2-person rule

    for idx, item in enumerate(bruh_rows):
        i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
        
        if end_num != 0 and found_num > end_num: break

        # --- INITIALIZATION ---
        if not active_status:
            if found_num == start_num:
                active_status, last_valid_num, current_target = True, found_num, found_num + 1
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                recent_authors = [author]
            continue

        # --- THE HEALING LOGIC (Lookahead) ---
        # Look at the next 3 messages to see if the community "fixed" a mistake
        lookahead = bruh_rows[idx+1 : idx+4]
        is_recovery = len(lookahead) >= 2 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(len(lookahead)))

        # --- LOGIC BRANCHES ---
        
        # 1. Perfect Match
        if found_num == current_target:
            if author in recent_authors:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule Violator"})
            else:
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                last_valid_num, current_target = found_num, found_num + 1
                recent_authors = (recent_authors + [author])[-1:] # Track only the last person

        # 2. Duplicate Check (A-1, B-1)
        elif found_num == last_valid_num:
            # If THIS duplicate is the one followed by a correct sequence, we might need to invalidate the previous one
            if is_recovery:
                # Find the previous correct version of this number and demote it
                for prev in reversed(all_successes):
                    if "Status" in prev and prev["Status"] == "CORRECT":
                        m = pattern.match(prev["Msg"])
                        if m and int(m.group(1)) == found_num:
                            prev["Status"] = "OVERWRITTEN (Duplicate Chain)"
                            all_mistakes.append({"Line": prev["Line"], "Author": prev["Author"], "Msg": prev["Msg"], "Reason": "Overwritten by later Consensus"})
                            break
                
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                last_valid_num, current_target = found_num, found_num + 1
                recent_authors = [author]
            else:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Duplicate/Stale Number"})

        # 3. The "Recovery" Jump (The solution to your A-1, B-1, C-2 problem)
        elif is_recovery and abs(found_num - last_valid_num) <= max_jump:
            reason = "Rollback" if found_num <= last_valid_num else f"Jump ({found_num - last_valid_num:+})"
            
            # If rolling back, invalidate the "future" that shouldn't have happened
            if found_num <= last_valid_num:
                for entry in all_successes:
                    m = pattern.match(entry["Msg"])
                    if m and int(m.group(1)) >= found_num:
                        entry["Status"] = "INVALIDATED (Rollback)"

            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Chain Healed: {reason}"})
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = [author]

        # 4. Total Failure
        elif not hide_invalid:
            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Broken Chain / No Consensus"})

    # --- FINAL PREP ---
    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    
    # Filter only actual CORRECT ones for the metric
    unique_count = len(res_s[res_s["Status"] == "CORRECT"])
    
    return res_m, res_s, active_status, last_valid_num, unique_count
