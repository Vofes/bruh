import pandas as pd
import re

def process_bruh_data(df, exclude_str="", include_str=""):
    """
    Handles all the logic: Filtering, Regex Matching, and Leaderboard Generation.
    """
    # 1. Clean data
    processed_df = df.copy()
    processed_df['Content'] = processed_df['Content'].astype(str)

    # 2. Apply Inclusion/Exclusion Filters
    if exclude_str:
        processed_df = processed_df[~processed_df['Content'].str.contains(exclude_str, regex=False)]
    if include_str:
        processed_df = processed_df[processed_df['Content'].str.contains(include_str, regex=False)]

    # 3. Define Regex: Starts with 'bruh' + space + number (allows text after)
    pattern = r'(?i)^bruh\s+(\d+)'

    # 4. Filter for Raw Bruhs
    is_bruh_mask = processed_df['Content'].str.contains(pattern, na=False, regex=True)
    raw_bruhs = processed_df[is_bruh_mask].copy()

    # 5. Generate Leaderboard
    leaderboard = raw_bruhs.groupby('Author').size().reset_index(name='Bruh Count')
    leaderboard = leaderboard.sort_values(by='Bruh Count', ascending=False)

    return leaderboard, processed_df, pattern

def audit_user_messages(df, target_user, pattern, exclude_str, include_str):
    """
    Returns a styled dataframe showing exactly why messages were or weren't counted.
    """
    user_df = df[df['Author'] == target_user].copy()
    
    # Check regex match
    user_df['Matches Pattern'] = user_df['Content'].str.contains(pattern, na=False, regex=True)
    
    # Check filters
    passed_ex = ~user_df['Content'].str.contains(exclude_str, regex=False) if exclude_str else True
    passed_in = user_df['Content'].str.contains(include_str, regex=False) if include_str else True
    user_df['Passed Filters'] = passed_ex & passed_in
    
    # Final Verdict
    user_df['COUNTED?'] = user_df['Matches Pattern'] & user_df['Passed Filters']
    
    return user_df
