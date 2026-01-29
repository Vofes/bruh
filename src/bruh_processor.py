import pandas as pd
import re

def process_bruh_logic(df, start_num, end_num=0, max_jump=1500, hide_invalid=False):
    pattern = re.compile(r'^bruh\s+(\d+)', re.IGNORECASE)
    
    # 1. Fast extraction of ALL bruh attempts
    all_attempts = []
    for i, row in df.iterrows():
        try:
            msg = str(row.iloc[3]).strip()
            match = pattern.match(msg)
            if match:
                all_attempts.append({
                    "Line": int(i), 
                    "Author": str(row.iloc[1]), 
                    "Num": int(match.group(1)), 
                    "Msg": msg
                })
        except: continue

    all_mistakes, winners = [], []
    active_status, last_valid_num, current_target = False, None, None
    recent_authors = []

    # 2. Validation Loop
    for idx, item in enumerate(all_attempts):
        line, author, found_num, msg = item["Line"], item["Author"], item["Num"], item["Msg"]
        
        if end_num != 0 and found_num > end_num: break
        if last_valid_num is not None and found_num == last_valid_num: continue

        if not active_status:
            if found_num == start_num:
                # Optimized anchor check
                lookback = {a["Num"] for a in all_attempts[max(0, idx-20):idx]}
                if set(range(start_num - 5, start_num)).issubset(lookback):
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
            lookahead = all_attempts[idx+1 : idx+4]
            is_consensus = len(lookahead) == 3 and all(lookahead[k]["Num"] == found_num + k + 1 for k in range(3))
            
            if is_consensus and abs(found_num - last_valid_num) <= max_jump:
                diff = found_num - last_valid_num
                if diff < 0: # Rollback logic
                    winners = [s for s in winners if s["Num"] < found_num]
                    winners.append({"Line": line, "Author": author, "Num": found_num, "Msg": msg})
                
                all_mistakes.append({"Line": line, "Author": author, "Num": found_num, "Msg": msg, "Reason": f"Jump ({diff:+})"})
                last_valid_num, current_target, recent_authors = found_num, found_num + 1, [author]
            elif not hide_invalid:
                all_mistakes.append({"Line": line, "Author": author, "Num": found_num, "Msg": msg, "Reason": "No Consensus"})

    # 3. SET-BASED LOST LOGIC (Strict Type Casting)
    df_winners = pd.DataFrame(winners).astype({"Line": int, "Author": str, "Num": int, "Msg": str}) if winners else pd.DataFrame(columns=["Line", "Author", "Num", "Msg"])
    winner_nums = set(df_winners["Num"])
    
    lost_data = []
    seen_lost = set()
    for item in all_attempts:
        n = item["Num"]
        if n >= start_num and n not in winner_nums:
            if n not in seen_lost:
                lost_data.append(item)
                seen_lost.add(n)

    df_lost = pd.DataFrame(lost_data).astype({"Line": int, "Author": str, "Num": int, "Msg": str}) if lost_data else pd.DataFrame(columns=["Line", "Author", "Num", "Msg"])
    df_mistakes = pd.DataFrame(all_mistakes)
    
    return df_winners, df_lost, df_mistakes, last_valid_num
