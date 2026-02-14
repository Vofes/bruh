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
        
        # 1. INITIALIZATION
        if not active_status:
            if found_num == start_num:
                active_status, last_valid_num, current_target = True, found_num, found_num + 1
                last_known_good_author = author
                recent_authors = [author]
                all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            continue

        lookahead = bruh_rows[idx+1 : idx+4]
        is_verified = len(lookahead) == 3 and all(lookahead[k]["num"] == found_num + k + 1 for k in range(3))
        diff = found_num - last_valid_num
        debug_info = f"Targ:{current_target}|Auths:{recent_authors}"

        # --- MANDATORY MOVE: FIXER CHECK MUST BE FIRST ---
        # This ensures that if 333400 is a fixer, we process it as a fixer 
        # IMMEDIATELY, even if the bot thinks it's a 'target match' or 'invalid'.
        if is_verified and found_num in target_to_line_map:
            # Check if this is a fix for a PREVIOUS jump (not just the current target)
            if found_num != current_target or "Jump" in str(all_mistakes[-1:]):
                origin_line = target_to_line_map[found_num]
                
                # RESET MEMORY HERE
                recent_authors = [last_known_good_author, author] if last_known_good_author else [author]
                
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Fixer ({diff:+})", "Status": "Fixer", "Debug": debug_info})
                for m in all_mistakes:
                    if m["Status"] == "Active" and origin_line <= m["Line"] < i:
                        m["Status"] = f"Fixed (by {i})"
                
                target_to_line_map = {t: l for t, l in target_to_line_map.items() if l < origin_line}
                last_valid_num, current_target = found_num, found_num + 1
                last_known_good_author = author
                continue # Skip all other checks for this message

        # --- STEP 2: REPETITION ---
        if found_num == last_valid_num:
            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "Repetition", "Status": "N/A", "Debug": debug_info})
            continue

        # --- STEP 3: TARGET MATCH ---
        if found_num == current_target:
            if author in recent_authors:
                # WE ARE HERE: If the Fixer didn't clear recent_authors yet, this fails.
                all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": "2-Person Rule", "Status": "Active", "Debug": debug_info})
                if not is_verified: continue 
            
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            last_known_good_author = author
            recent_authors = (recent_authors + [author])[-2:]
            continue

        # --- STEP 4: JUMP ---
        if is_verified:
            target_to_line_map[current_target] = i
            all_mistakes.append({"Line": i, "Author": author, "Msg": msg, "Reason": f"Jump ({diff:+})", "Status": "Active", "Debug": debug_info})
            all_successes.append({"Line": i, "Author": author, "Msg": msg, "Status": "CORRECT"})
            last_valid_num, current_target = found_num, found_num + 1
            recent_authors = [author]
            continue
