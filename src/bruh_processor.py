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
                    "Line": i, 
                    "Author": str(row.iloc[1]), 
                    "Num": int(match.group(1)), 
                    "Msg": msg
                })
        except: continue

    all_mistakes, winners = [], []
    active_status, last_valid_num, current_target = False, None, None
    recent_authors = []

    # 2. Optimized Validation Loop
    for idx, item in enumerate(all_attempts):
        i, author, found_num, msg = item["Line"], item["Author"], item["Num"], item["Msg"]
        
        if end_num != 0 and found_num > end_num: break
        if last_valid_num is not None and found_num == last_valid_num: continue

        if not active_status:
            if found_num == start_num:
                # Check for anchor in the immediate vicinity
                lookback = [a["Num"] for a in all_attempts[max(0, idx-20):idx]]
                if set(range(start_num - 5, start_num)).issubset(set(lookback)):
                    active_status, last_valid_num, current_target = True, found_num, found_num + 1
                    winners.append({"Line": i, "Author": author, "Num": found_num, "Msg": msg})
                    recent_authors = [author]
            continue

        if found_num == current_target:
            if author in recent_authors:
                all_mistakes.append({"Line": i, "Author": author, "Num": found_num, "Msg": msg, "Reason": "2-Person Rule"})
            else:
                winners.append({"Line": i, "Author": author, "Num": found_num, "Msg": msg})
                last_valid_num, current_target = found_num, found_num + 1
                recent_authors = (recent_authors + [author])[-2:]
        else:
            # Consensus Lookahead
            lookahead = all_attempts[idx+1 : idx+4]
            is_consensus = len(lookahead) == 3 and all(lookahead[k]["Num"] == found_num + k + 1 for k in range(3))
            
            if is_consensus and abs(found_num - last_valid_num) <= max_jump:
                diff = found_num - last_valid_num
                if diff < 0: # Rollback
                    winners = [s for s in winners if s["Num"] < found_num]
                    winners.append({"Line": i, "Author": author, "Num": found_num, "Msg": msg})
                
                all_mistakes.append({"Line": i, "Author": author, "Num": found_num, "Msg": msg, "Reason": f"Jump ({diff:+})"})
                last_valid_num, current_target, recent_authors = found_num, found_num + 1, [author]
            elif not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Num": found_num, "Msg": msg, "Reason": "No Consensus"})

    # 3. SET-BASED LOST BRUH LOGIC (Fixes the Overflow)
    df_winners = pd.DataFrame(winners)
    winner_nums = set(df_winners["Num"]) if not df_winners.empty else set()
    
    # We use a dictionary to keep only the FIRST time a lost bruh was seen (prevents duplicates)
    lost_dict = {}
    for item in all_attempts:
        n = item["Num"]
        if n >= start_num and n not in winner_nums:
            if n not in lost_dict:
                lost_dict[n] = item

    df_lost = pd.DataFrame(list(lost_dict.values()))
    df_mistakes = pd.DataFrame(all_mistakes)
    
    return df_winners, df_lost, df_mistakes, last_valid_num
