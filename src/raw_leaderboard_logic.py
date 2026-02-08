import pandas as pd
import re

def get_static_raw_leaderboard(df):
    """The official, unfiltered leaderboard logic."""
    processed_df = df.copy()
    processed_df['Content'] = processed_df['Content'].astype(str)
    
    # Static Pattern: Starts with 'bruh' + space + number
    pattern = r'(?i)^bruh\s+(\d+)'
    
    is_bruh_mask = processed_df['Content'].str.contains(pattern, na=False, regex=True)
    raw_bruhs = processed_df[is_bruh_mask].copy()

    leaderboard = raw_bruhs.groupby('Author').size().reset_index(name='Bruh Count')
    return leaderboard.sort_values(by='Bruh Count', ascending=False)

def run_debug_audit(df, target_user, exclude_str, include_str):
    """The dynamic logic used only in the debug section."""
    user_df = df[df['Author'] == target_user].copy()
    user_df['Content'] = user_df['Content'].astype(str)
    
    pattern = r'(?i)^bruh\s+(\d+)'
    
    # 1. Check Pattern Match
    user_df['Matches Pattern'] = user_df['Content'].str.contains(pattern, na=False, regex=True)
    
    # 2. Check Debug Filters
    passed_ex = ~user_df['Content'].str.contains(exclude_str, regex=False) if exclude_str else True
    passed_in = user_df['Content'].str.contains(include_str, regex=False) if include_str else True
    user_df['Passed Filters'] = passed_ex & passed_in
    
    # 3. Final Result
    user_df['COUNTED?'] = user_df['Matches Pattern'] & user_df['Passed Filters']
    
    return user_df
