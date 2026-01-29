import pandas as pd
import re

def process_bruh_logic(df, start_num, end_num=0, max_jump=1500, hide_invalid=False):
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
    active_status, last_valid_num, current_target = False, None, None
    recent_authors = []

    for idx, item in enumerate(bruh_rows):
        i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
        if end_num != 0 and found_num > end_num: break
        if last_valid_num is not None and found_num == last_valid_num: continue

        if not active_status:
            if found_num == start_num:
                past_nums = set(r["num"] for r in bruh_rows[:idx])
                if set(range(start_num - 10, start_num)).issubset(past_nums):
                    active_status, last_valid_num, current_target = True, found_num, found_num + 1
                    all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                    recent_authors = [author]
            continue

        if found_num == current_target:
            if author in recent_authors:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule"})
            else:
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = (recent_authors + [author])[-2:]
        else:
            lookahead = bruh_rows[idx+1 : idx+4]
            is_consensus = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
            diff = found_num - last_valid_num
            
            if is_consensus and abs(diff) <= max_jump:
                if diff < 0:
                    for entry in all_successes:
                        m = pattern.match(entry["Msg"])
                        if m and int(m.group(1)) >= found_num:
                            entry["Status"] = "CORRECT-FIX"
                    all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                    all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Rollback ({diff:+})"})
                else:
                    all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Jump ({diff:+})"})
                last_valid_num, current_target, recent_authors = found_num, found_num + 1, [author]
            elif not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Invalid/No Consensus"})

    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    unique_count = len(res_s[res_s["Status"] == "CORRECT"])
    return res_m, res_s, active_status, last_valid_num, unique_count
