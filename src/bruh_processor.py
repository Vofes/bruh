import pandas as pd
import re

def process_bruh_logic(df, start_num, end_num=0, max_jump=1500, hide_invalid=False):
    pattern = re.compile(r'(?i)^bruh\s+(\d+)')
    cols_m = ["Line", "Author", "Msg", "Reason", "Status"]
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

        lookahead = bruh_rows[idx+1 : idx+4]
        is_verified = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
        diff = found_num - last_valid_num

        # --- 1. REPETITION ---
        if found_num == last_valid_num:
            if not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Repetition (0)", "Status": "Active"})
            continue

        # --- 2. TARGET MATCH (A-3/Retro-Save Logic) ---
        if found_num == current_target:
            # 2-Person Rule Check
            if author in recent_authors:
                saved = False
                for prev_idx in range(idx - 1, max(0, idx - 10), -1):
                    prev_item = bruh_rows[prev_idx]
                    if prev_item["num"] == last_valid_num and prev_item["author"] != author:
                        all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT (Saved)"})
                        recent_authors = [author]
                        last_valid_num, current_target = found_num, found_num + 1
                        saved = True
                        break
                if not saved:
                    all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule", "Status": "Active"})
            else:
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                last_valid_num, current_target = found_num, found_num + 1
                recent_authors = [author]

        # --- 3. VERIFIED JUMP / ROLLBACK (The Global Healer) ---
        elif is_verified and abs(diff) <= max_jump:
            base_reason = "Jump" if diff > 0 else "Rollback"
            final_reason = f"{base_reason} ({diff:+})"
            
            # THE SEARCH: Is this move fixing a specific previous error?
            is_fixing_move = False
            fix_anchor_line = None

            for m in reversed(all_mistakes):
                if m["Line"] < i - FIX_WINDOW: break
                if m["Status"] != "Active": continue
                
                m_match = pattern.match(m["Msg"])
                if not m_match: continue
                m_val = int(m_match.group(1))

                # Logic: Rollback fixes Jump/2-Person | Jump fixes Rollback
                check_fix_rb = (diff < 0 and ("Jump" in m["Reason"] or "2-Person" in m["Reason"]) and abs(found_num - m_val) <= 2)
                check_fix_jp = (diff > 0 and "Rollback" in m["Reason"] and "Fixing" not in m["Reason"] and abs(found_num - m_val) <= 2)

                if check_fix_rb or check_fix_jp:
                    is_fixing_move = True
                    fix_anchor_line = m["Line"]
                    final_reason = f"Fixing {base_reason} ({diff:+})"
                    break
            
            # THE SWEEP: If it's a fix, mark EVERYTHING between the anchor and now as Fixed
            if is_fixing_move:
                for mistake in all_mistakes:
                    if fix_anchor_line <= mistake["Line"] < i:
                        mistake["Status"] = f"Fixed (by {i})"

            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": final_reason, "Status": "Active"})
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = [author]

        # --- 4. INVALID ---
        else:
            if not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Invalid ({diff:+})", "Status": "Active"})

    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    unique_count = len(res_s[res_s["Status"].str.contains("CORRECT")])
    return res_m, res_s, active_status, last_valid_num, unique_count
