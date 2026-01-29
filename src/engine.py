import pandas as pd
import re

def run_botcheck_logic(df, start_num, end_num=0, max_jump=1500, hide_invalid=False):
    pattern = re.compile(r'^bruh\s+(\d+)', re.IGNORECASE)
    cols_m = ["Line", "Author", "Msg", "Reason"]
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
    active_status, current_target, last_valid_num = False, None, None
    recent_authors = []

    for idx, item in enumerate(bruh_rows):
        i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
        if end_num != 0 and found_num > end_num: break
        if last_valid_num is not None and found_num == last_valid_num: continue

        if not active_status:
            if found_num == start_num:
                past_nums = set(r["num"] for r in bruh_rows[:idx])
                required = set(range(start_num - 10, start_num))
                if required.issubset(past_nums):
                    active_status, last_valid_num, current_target = True, found_num, found_num + 1
                    recent_authors = [author]
                    all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "ANCHOR"})
            continue

        if found_num == current_target:
            if author in recent_authors:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule"})
            else:
                # Perfect sequence gets "VALID" status
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "VALID"})
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = (recent_authors + [author])[-2:]
        else:
            lookahead = bruh_rows[idx+1 : idx+4]
            is_consensus = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
            diff = found_num - last_valid_num
            
            if is_consensus and abs(diff) <= max_jump:
                label = "Jump" if diff > 0 else "Correction"
                # If it's a correction, we put it in SUCCESS as a 'PIVOT'
                # If it's a bad jump, we still log it as a mistake but update the counter
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Confirmed {label} ({diff:+} from {last_valid_num})"})
                
                # Only give "Success" credit for Corrections, not for illegal Jumps
                if diff < 0:
                    all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECTION"})
                
                last_valid_num, current_target, recent_authors = found_num, found_num + 1, [author]
            else:
                # Check if we should hide these based on user setting
                if not hide_invalid:
                    reason = f"Illegal Jump ({diff:+})" if is_consensus else "Invalid / No Consensus"
                    all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": reason})

    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    return res_m, res_s, active_status, last_valid_num
