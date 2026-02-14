import pandas as pd
import re

def process_bruh_logic(df, start_num, end_num=0, max_jump=1500, filter_mode=1):
    pattern = re.compile(r'(?i)^bruh\s+(\d+)')
    cols_m = ["Line", "Author", "Msg", "Reason", "Status", "Debug"]
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
    anchor_author = None # This is the "Golden Author" from BEFORE the mess
    target_to_line_map = {} 

    for idx, item in enumerate(bruh_rows):
        i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
        if end_num != 0 and found_num > end_num: break

        if not active_status:
            if found_num == start_num:
                active_status, last_valid_num, current_target = True, found_num, found_num + 1
                anchor_author, recent_authors = author, [author]
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            continue

        lookahead = bruh_rows[idx+1 : idx+4]
        is_verified = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
        diff = found_num - last_valid_num
        
        # --- PRIORITY 1: THE FIXER ---
        if is_verified and found_num in target_to_line_map:
            origin_line = target_to_line_map[found_num]
            
            # STITCH: Use the Anchor (pre-jump) and the current Fixer
            recent_authors = [anchor_author, author] if anchor_author else [author]
            
            label = "Fixer (RB)" if diff < 0 else "Fixer (JP)"
            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"{label} ({diff:+})", "Status": "Fixer", "Debug": f"RECOVERED:{recent_authors}"})
            
            for m in all_mistakes:
                # FIX: Only mark as fixed if the mistake happened AFTER the jump started
                if m["Status"] == "Active" and origin_line <= m["Line"] < i:
                    m["Status"] = f"Fixed (by {i})"
            
            target_to_line_map = {t: l for t, l in target_to_line_map.items() if l < origin_line}
            last_valid_num, current_target = found_num, found_num + 1
            anchor_author = author # Fixer becomes the new anchor
            continue 

        # --- PRIORITY 2: REPETITIONS & SWAPS ---
        if found_num == last_valid_num:
            fixed_via_swap = False
            # Swap window limited to 3 to prevent "Time Travel" fixes
            for m in reversed(all_mistakes[-3:]):
                if m["Reason"] == "2-Person Rule" and m["Status"] == "Active":
                    if author != m["Author"]:
                        m["Status"] = f"Fixed (Swap by {i})"
                        all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
                        recent_authors = [recent_authors[0], author] if len(recent_authors) > 1 else [author]
                        fixed_via_swap = True
                        break
            if not fixed_via_swap:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Repetition", "Status": "N/A", "Debug": f"Auths:{recent_authors}"})
            continue

        # --- PRIORITY 3: TARGET MATCH ---
        if found_num == current_target:
            if author in recent_authors:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule", "Status": "Active", "Debug": f"BlockedBy:{recent_authors}"})
                if not is_verified: continue 
            
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            anchor_author = author # Update anchor on valid progression
            recent_authors = (recent_authors + [author])[-2:]
            continue

        # --- PRIORITY 4: JUMPS ---
        if is_verified:
            # We save the "Golden Anchor" before we enter the messy jump timeline
            target_to_line_map[current_target] = i
            label = "Jump" if diff > 0 else "Rollback"
            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"{label} ({diff:+})", "Status": "Active", "Debug": f"AnchorSaved:{anchor_author}"})
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            # Note: We do NOT update anchor_author here. It stays at the pre-jump person.
            recent_authors = [author] 
            continue

        # --- PRIORITY 5: INVALID ---
        all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Invalid ({diff:+})", "Status": "N/A", "Debug": f"Targ:{current_target}"})

    # (Return logic stays the same...)
    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    if filter_mode == 2: res_m = res_m[res_m["Status"] != "N/A"]
    elif filter_mode == 3: res_m = res_m[res_m["Status"] == "Active"]
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    return res_m, res_s, active_status, last_valid_num, len(res_s[res_s["Status"] == "CORRECT"])
