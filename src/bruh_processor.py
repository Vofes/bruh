import pandas as pd
import re

def process_bruh_logic(df, start_num, end_num=0, max_jump=1500, hide_invalid=False):
    pattern = re.compile(r'^bruh\s+(\d+)', re.IGNORECASE)
    
    # 1. Gather all bruh attempts
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

    # 2. Validation Loop
    for idx, item in enumerate(bruh_rows):
        i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
        if end_num != 0 and found_num > end_num: break
        if last_valid_num is not None and found_num == last_valid_num: continue

        if not active_status:
            if found_num == start_num:
                # Anchor check
                past_nums = set(r["num"] for r in bruh_rows[:idx])
                if set(range(start_num - 10, start_num)).issubset(past_nums):
                    active_status, last_valid_num, current_target = True, found_num, found_num + 1
                    all_successes.append({"Line": i, "Author": author, "Num": found_num, "Msg": msg})
                    recent_authors = [author]
            continue

        if found_num == current_target:
            if author in recent_authors:
                all_mistakes.append({"Line": i, "Author": author, "Num": found_num, "Msg": msg, "Reason": "2-Person Rule"})
            else:
                all_successes.append({"Line": i, "Author": author, "Num": found_num, "Msg": msg})
                last_valid_num, current_target = found_num, found_num + 1
                recent_authors = (recent_authors + [author])[-2:]
        else:
            lookahead = bruh_rows[idx+1 : idx+4]
            is_consensus = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
            
            if is_consensus and abs(found_num - last_valid_num) <= max_jump:
                diff = found_num - last_valid_num
                if diff < 0: # Rollback
                    # Remove any "Winners" that are now invalidated by the rollback
                    all_successes = [s for s in all_successes if s["Num"] < found_num]
                    all_successes.append({"Line": i, "Author": author, "Num": found_num, "Msg": msg})
                    all_mistakes.append({"Line": i, "Author": author, "Num": found_num, "Msg": msg, "Reason": f"Rollback ({diff:+})"})
                else: # Jump
                    all_mistakes.append({"Line": i, "Author": author, "Num": found_num, "Msg": msg, "Reason": f"Jump ({diff:+})"})
                
                last_valid_num, current_target, recent_authors = found_num, found_num + 1, [author]
            elif not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Num": found_num, "Msg": msg, "Reason": "Invalid/No Consensus"})

    # Convert to DataFrames
    df_winners = pd.DataFrame(all_successes)
    df_mistakes = pd.DataFrame(all_mistakes)
    
    # --- LOST BRUHS LOGIC ---
    # Find every number that was attempted but IS NOT in the Winner list
    winner_nums = set(df_winners["Num"]) if not df_winners.empty else set()
    
    lost_list = []
    for item in bruh_rows:
        # If the number used in this message never made it to the final Winners list
        if item["num"] not in winner_nums and item["num"] >= start_num:
            # Avoid duplicates in the lost list itself
            if not any(l["Num"] == item["num"] for l in lost_list):
                lost_list.append({"Line": item["index"], "Author": item["author"], "Num": item["num"], "Msg": item["msg"]})
    
    df_lost = pd.DataFrame(lost_list)
    
    return df_winners, df_lost, df_mistakes, last_valid_num
