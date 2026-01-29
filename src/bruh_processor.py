import pandas as pd
import re

def process_bruh_logic(df, start_num, end_num=0, max_jump=1500, hide_invalid=False):
    pattern = re.compile(r'^bruh\s+(\d+)', re.IGNORECASE)
    
    # 1. Extraction with zero-risk typing
    all_attempts = []
    for i, row in df.iterrows():
        try:
            msg = str(row.iloc[3]).strip()
            match = pattern.match(msg)
            if match:
                all_attempts.append({
                    "Line": i, 
                    "Author": str(row.iloc[1]), 
                    "Num": int(match.group(1)), 
                    "Msg": msg
                })
        except: continue

    winners = []
    all_mistakes = []
    active_status = False
    last_valid_num = None
    current_target = None
    recent_authors = []

    # 2. Logic Loop
    for idx, item in enumerate(all_attempts):
        line, author, found_num, msg = item["Line"], item["Author"], item["Num"], item["Msg"]
        
        if end_num != 0 and found_num > end_num: break
        if last_valid_num is not None and found_num == last_valid_num: continue

        if not active_status:
            if found_num == start_num:
                # Simple lookback check
                lookback = {a["Num"] for a in all_attempts[max(0, idx-15):idx]}
                if any(n in lookback for n in range(start_num-5, start_num)):
                    active_status, last_valid_num, current_target = True, found_num, found_num + 1
                    winners.append({"Line": line, "Author": author, "Num": found_num, "Msg": msg})
                    recent_authors = [author]
            continue

        if found_num == current_target:
            if author in recent_authors:
                all_mistakes.append({"Line": line, "Author": author, "Num": found_num, "Msg": msg, "Reason": "2-Person Rule"})
            else:
                winners.append({"Line": line, "Author": author, "Num": found_num, "Msg": msg})
                last_valid_num, current_target = found_num, found_num + 1
                recent_authors = (recent_authors + [author])[-2:]
        else:
            # Consensus check
            lookahead = all_attempts[idx+1 : idx+4]
            is_consensus = len(lookahead) == 3 and all(lookahead[k]["Num"] == found_num + k + 1 for k in range(3))
            
            if is_consensus and abs(found_num - last_valid_num) <= max_jump:
                diff = found_num - last_valid_num
                if diff < 0: # Rollback
                    winners = [s for s in winners if s["Num"] < found_num]
                
                # Jumps go to mistakes list
                all_mistakes.append({"Line": line, "Author": author, "Num": found_num, "Msg": msg, "Reason": f"Jump/Rollback ({diff:+})"})
                winners.append({"Line": line, "Author": author, "Num": found_num, "Msg": msg})
                last_valid_num, current_target, recent_authors = found_num, found_num + 1, [author]
            elif not hide_invalid:
                all_mistakes.append({"Line": line, "Author": author, "Num": found_num, "Msg": msg, "Reason": "No Consensus"})

    # 3. Final Selection Logic (The "Lost" List)
    # We use basic Python dictionaries to avoid Pandas/Arrow overflow errors
    winner_nums = {s["Num"] for s in winners}
    
    lost_data = []
    seen_lost = set()
    for item in all_attempts:
        n = item["Num"]
        if n >= start_num and n not in winner_nums:
            if n not in seen_lost:
                lost_data.append(item)
                seen_lost.add(n)

    return pd.DataFrame(winners), pd.DataFrame(lost_data), pd.DataFrame(all_mistakes), last_valid_num
