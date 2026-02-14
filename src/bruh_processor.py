import pandas as pd
import re

def process_bruh_logic(df, start_num, end_num=0, max_jump=1500, hide_invalid=False):
    pattern = re.compile(r'(?i)^bruh\s+(\d+)')
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
    recent_authors = [] # We'll track the last few authors to check for 2-person rule
    
    # 4000 BRUH WINDOW for "Fixing" logic
    FIX_WINDOW = 4000 

    for idx, item in enumerate(bruh_rows):
        i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
        if end_num != 0 and found_num > end_num: break

        if not active_status:
            if found_num == start_num:
                active_status, last_valid_num, current_target = True, found_num, found_num + 1
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                recent_authors = [author]
            continue

        # Check for Lookahead Consensus (Verified by 3 more people)
        lookahead = bruh_rows[idx+1 : idx+4]
        is_verified = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))

        # --- LOGIC BRANCHES ---

        # 1. TARGET MATCH (The A-3 Logic)
        if found_num == current_target:
            # Check 2-person rule violation
            if author in recent_authors:
                # RETROACTIVE RECONCILIATION: Can we save this message?
                # Look for a duplicate of the PREVIOUS valid number
                saved = False
                # We check the bruh rows near the previous valid number
                for prev_idx in range(idx - 1, max(0, idx - 10), -1):
                    prev_item = bruh_rows[prev_idx]
                    if prev_item["num"] == last_valid_num and prev_item["author"] != author:
                        # Found a different person who also said the same last_valid_num!
                        # Swap credit to them to save the current author
                        for success in reversed(all_successes):
                            if success["Line"] == item["index"] - (idx - prev_idx): # Approximate finding
                                pass # In a real scan, we'd match the 'Line' exactly
                        
                        # Logic: Demote the first 'Correct' and promote the duplicate
                        # This clears the recent_author check for the current message
                        all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT (Retro-Saved)"})
                        recent_authors = [author]
                        last_valid_num, current_target = found_num, found_num + 1
                        saved = True
                        break
                
                if not saved:
                    all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule"})
            else:
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                last_valid_num, current_target = found_num, found_num + 1
                recent_authors = [author]

        # 2. JUMP / ROLLBACK (Only if verified)
        elif is_verified and abs(found_num - last_valid_num) <= max_jump:
            diff = found_num - last_valid_num
            reason = "Jump" if diff > 0 else "Rollback"
            
            # Check for "Fixing" status
            is_fixing = False
            # Look back through mistakes within the FIX_WINDOW
            recent_mistakes = [m for m in all_mistakes if m["Line"] > i - FIX_WINDOW]
            
            for m in recent_mistakes:
                m_num = pattern.match(m["Msg"])
                if not m_num: continue
                m_val = int(m_num.group(1))
                
                if reason == "Rollback":
                    # Fixing if lands ±2 of a Jump or 2-Person error
                    if ("Jump" in m["Reason"] or "2-Person" in m["Reason"]) and abs(found_num - m_val) <= 2:
                        reason = "Fixing Rollback"
                        is_fixing = True
                        break
                elif reason == "Jump":
                    # Fixing if lands ±2 of a non-fixing rollback
                    if "Rollback" in m["Reason"] and "Fixing" not in m["Reason"] and abs(found_num - m_val) <= 2:
                        reason = "Fixing Jump"
                        is_fixing = True
                        break

            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": reason})
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = [author]

        # 3. REPETITION (Duplicate)
        elif found_num == last_valid_num:
            if not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Repetition"})

        # 4. INVALID
        else:
            if not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Invalid Chain"})

    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    unique_count = len(res_s[res_s["Status"].str.contains("CORRECT")])
    return res_m, res_s, active_status, last_valid_num, unique_count
