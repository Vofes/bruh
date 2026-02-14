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
    
    # MEMORY MANAGEMENT
    recent_authors = [] 
    last_known_good_author = None 
    target_to_line_map = {} 

    for idx, item in enumerate(bruh_rows):
        i, author, msg, found_num = item["index"], item["author"], item["msg"], item["num"]
        if end_num != 0 and found_num > end_num: break

        # 1. INITIALIZATION
        if not active_status:
            if found_num == start_num:
                active_status, last_valid_num, current_target = True, found_num, found_num + 1
                last_known_good_author = author
                recent_authors = [author]
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            continue

        # 2. CONSENSUS & DEBUG
        lookahead = bruh_rows[idx+1 : idx+4]
        is_verified = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
        diff = found_num - last_valid_num
        
        # Show exactly who the bot remembers in the Debug column
        debug_info = f"Targ:{current_target}|Auths:{recent_authors}"

        # --- STEP 1: FIXER LOGIC (The Rescue) ---
        if is_verified and found_num in target_to_line_map:
            if found_num != current_target:
                origin_line = target_to_line_map[found_num]
                
                # RECOVERY STITCH: Force-reset the memory.
                # We only allow the person who was valid BEFORE the mess and the FIXER.
                if last_known_good_author and last_known_good_author != author:
                    recent_authors = [last_known_good_author, author]
                else:
                    recent_authors = [author]
                
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Fixer ({diff:+})", "Status": "Fixer", "Debug": debug_info})
                for m in all_mistakes:
                    if m["Status"] == "Active" and origin_line <= m["Line"] < i:
                        m["Status"] = f"Fixed (by {i})"
                
                target_to_line_map = {t: l for t, l in target_to_line_map.items() if l < origin_line}
                
                # Update current state to the fixed point
                last_valid_num, current_target = found_num, found_num + 1
                last_known_good_author = author
                continue

        # --- STEP 2: TARGET MATCH (Normal Flow) ---
        if found_num == current_target:
            if author in recent_authors:
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule", "Status": "Active", "Debug": debug_info})
                # If they broke the rule, we only continue if the chain is verified anyway
                if not is_verified: continue 
            
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            last_known_good_author = author
            recent_authors = (recent_authors + [author])[-2:]
            continue

        # --- STEP 3: JUMP/ROLLBACK (The Break) ---
        if is_verified:
            # IMPORTANT: We store the CURRENT target to history before we jump
            target_to_line_map[current_target] = i
            
            reason = "Jump" if diff > 0 else "Rollback"
            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"{reason} ({diff:+})", "Status": "Active", "Debug": debug_info})
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            
            # We move to the new timeline
            last_valid_num, current_target = found_num, found_num + 1
            
            # During a jump, we update recent_authors for the 'bad' timeline, 
            # BUT we don't update last_known_good_author!
            recent_authors = [author] 
            continue

        # --- STEP 4: CATCH-ALL (Invalid) ---
        all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Invalid ({diff:+})", "Status": "N/A", "Debug": debug_info})

    # (Filtering and return code remains same...)
    res_m = pd.DataFrame(all_mistakes) if all_mistakes else pd.DataFrame(columns=cols_m)
    if filter_mode == 2: res_m = res_m[res_m["Status"] != "N/A"]
    elif filter_mode == 3: res_m = res_m[res_m["Status"] == "Active"]
    res_s = pd.DataFrame(all_successes) if all_successes else pd.DataFrame(columns=cols_s)
    return res_m, res_s, active_status, last_valid_num, len(res_s[res_s["Status"] == "CORRECT"])
