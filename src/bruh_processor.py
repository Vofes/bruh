import pandas as pd
import re

def process_bruh_logic(df, start_num, end_num=0, max_jump=1500, hide_invalid=False):
    pattern = re.compile(r'(?i)^bruh\s+(\d+)')
    cols_m = ["Line", "Author", "Msg", "Reason", "Status"]
    cols_s = ["Line", "Author", "Msg", "Status"]

    # --- 1. PRE-PROCESS ---
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

        # Lookahead: Verified by 3-person consensus
        lookahead = bruh_rows[idx+1 : idx+4]
        is_verified = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
        diff = found_num - last_valid_num

        # --- BRANCH A: TARGET MATCH ---
        if found_num == current_target:
            if author in recent_authors:
                # 2-Person Rule Violations are "Active" until fixed/verified
                if is_verified:
                    all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule", "Status": f"Fixed (Consensus by {lookahead[-1]['index']})"})
                    all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                else:
                    all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule", "Status": "Active"})
                    continue # Wait for someone else to bruh
            else:
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = (recent_authors + [author])[-2:]

        # --- BRANCH B: REPETITION ---
        elif found_num == last_valid_num:
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
                # MARK AS STATIC (Not Active)
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Repetition", "Status": "N/A (Static)"})

        # --- BRANCH C: JUMPS / ROLLBACKS ---
        elif is_verified:
            # Verified anomalies are mistakes, but they are technically 'Fixed' because the chain moved on
            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Jump/Rollback ({diff:+})", "Status": "Fixed (Consensus)"})
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = [author]

        # --- BRANCH D: INVALID ---
        else:
            if not hide_invalid:
                # MARK AS STATIC (Not Active)
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Invalid", "Status": "N/A (Static)"})

    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    
    return res_m, res_s, active_status, last_valid_num, len(res_s[res_s["Status"] == "CORRECT"])
