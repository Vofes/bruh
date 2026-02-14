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
    target_to_line_map = {} 

    for idx, item in enumerate(bruh_rows):
        i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
        if end_num != 0 and found_num > end_num: break

        if not active_status:
            if found_num == start_num:
                active_status, last_valid_num, current_target = True, found_num, found_num + 1
                recent_authors = [author]
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            continue

        lookahead = bruh_rows[idx+1 : idx+4]
        is_verified = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
        diff = found_num - last_valid_num
        
        # --- PRIORITY 1: TARGET MATCH ---
        if found_num == current_target:
            if author in recent_authors:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule", "Status": "Active"})
                if not is_verified: continue 
            
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = (recent_authors + [author])[-2:]
            if found_num in target_to_line_map: del target_to_line_map[found_num]
            continue

        # --- PRIORITY 2: REPETITIONS & SWAPS ---
        if found_num == last_valid_num:
            fixed_via_swap = False
            for m in reversed(all_mistakes[-5:]):
                if m["Reason"] == "2-Person Rule" and m["Status"] == "Active":
                    if author != m["Author"]:
                        m["Status"] = f"Fixed (Swap by {i})"
                        all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                        recent_authors = (recent_authors + [author])[-2:]
                        fixed_via_swap = True
                        break
            if not fixed_via_swap:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Repetition", "Status": "N/A"})
            continue

        # --- PRIORITY 3: VERIFIED JUMP/FIXER ---
        if is_verified:
            if found_num in target_to_line_map:
                origin_line = target_to_line_map[found_num]
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Fixer", "Status": "Fixer"})
                for m in all_mistakes:
                    if m["Status"] == "Active" and origin_line <= m["Line"] < i:
                        m["Status"] = f"Fixed (by {i})"
                target_to_line_map = {t: l for t, l in target_to_line_map.items() if l < origin_line}
            else:
                target_to_line_map[current_target] = i
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Jump", "Status": "Active"})
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = (recent_authors + [author])[-2:]
            continue

        # --- PRIORITY 4: INVALID ---
        all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Invalid ({diff:+})", "Status": "N/A"})

    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    if filter_mode == 2: res_m = res_m[res_m["Status"] != "N/A"]
    elif filter_mode == 3: res_m = res_m[res_m["Status"] == "Active"]
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    
    return res_m, res_s, active_status, last_valid_num, len(res_s[res_s["Status"] == "CORRECT"])
