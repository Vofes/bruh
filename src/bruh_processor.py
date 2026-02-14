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

        # --- BRANCH 1: REPETITION ---
        if found_num == last_valid_num:
            if not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Repetition (0)"})
            continue

        # --- BRANCH 2: TARGET MATCH (A-3 Logic) ---
        if found_num == current_target:
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
                    all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule"})
            else:
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                last_valid_num, current_target = found_num, found_num + 1
                recent_authors = [author]

        # --- BRANCH 3: VERIFIED JUMP / ROLLBACK (The Fixing Logic) ---
        elif is_verified and abs(diff) <= max_jump:
            base_reason = "Jump" if diff > 0 else "Rollback"
            final_reason = f"{base_reason} ({diff:+})"
            
            # Search for a mistake to "Fix"
            recent_mistakes = [m for m in all_mistakes if m["Line"] > i - FIX_WINDOW]
            
            for m in reversed(recent_mistakes):
                m_num_match = pattern.match(m["Msg"])
                if not m_num_match: continue
                m_val = int(m_num_match.group(1))
                
                fix_detected = False
                # RULE: Rollback fixes Jump or 2-Person
                if diff < 0 and ("Jump" in m["Reason"] or "2-Person" in m["Reason"]) and abs(found_num - m_val) <= 2:
                    final_reason = f"Fixing Rollback ({diff:+})"
                    fix_detected = True
                # RULE: Jump fixes a standard Rollback
                elif diff > 0 and "Rollback" in m["Reason"] and "Fixing" not in m["Reason"] and abs(found_num - m_val) <= 2:
                    final_reason = f"Fixing Jump ({diff:+})"
                    fix_detected = True

                if fix_detected:
                    # HEALING: Mark all mistakes between that error and now as "Fixed"
                    error_line = m["Line"]
                    for mistake_entry in all_mistakes:
                        if error_line <= mistake_entry["Line"] < i:
                            if "Fixed" not in mistake_entry["Reason"]:
                                mistake_entry["Reason"] = f"Fixed (by Line {i})"
                    break # Stop searching once fix is applied

            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": final_reason})
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = [author]

        # --- BRANCH 4: INVALID ---
        else:
            if not hide_invalid:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Invalid ({diff:+})"})

    # Clean up results
    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    unique_count = len(res_s[res_s["Status"].str.contains("CORRECT")])
    return res_m, res_s, active_status, last_valid_num, unique_count
