import pandas as pd
import re

def run_botcheck_logic(df, start_num, end_num=0):
    pattern = re.compile(r'^bruh\s+(\d+)', re.IGNORECASE)
    cols_m = ["Line", "Author", "Msg", "Reason"]
    cols_s = ["Line", "Author", "Msg", "Status"]

    # Global Scan to find all 'bruh' messages
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
        except:
            continue

    all_mistakes, all_successes = [], []
    active_status, current_target, last_valid_num = False, None, None
    recent_authors = []

    for idx, item in enumerate(bruh_rows):
        i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
        
        # Stop if we have reached the user-defined ending bruh
        if end_num != 0 and found_num > end_num:
            break
            
        # Skip duplicate numbers
        if last_valid_num is not None and found_num == last_valid_num:
            continue

        # Logic to find the Secure Anchor
        if not active_status:
            if found_num == start_num:
                past_nums = set(r["num"] for r in bruh_rows[:idx])
                required = set(range(start_num - 10, start_num))
                if required.issubset(past_nums):
                    active_status, last_valid_num, current_target = True, found_num, found_num + 1
                    recent_authors = [author]
                    all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "ANCHOR"})
            continue

        # Logic for Valid Sequence
        if found_num == current_target:
            if author in recent_authors:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule"})
            else:
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "VALID"})
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = (recent_authors + [author])[-2:]
        else:
            # Consensus Pivot Check (Looking ahead 3 steps)
            lookahead = bruh_rows[idx+1 : idx+4]
            is_consensus = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
            
            if is_consensus:
                diff = found_num - last_valid_num
                label = "Jump" if diff > 0 else "Correction"
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Confirmed {label} ({diff:+} from {last_valid_num})"})
                last_valid_num, current_target, recent_authors = found_num, found_num + 1, [author]
            else:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Invalid / No Consensus"})

    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    return res_m, res_s, active_status, last_valid_num
