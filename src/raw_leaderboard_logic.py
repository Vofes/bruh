import pandas as pd
import re

def get_static_raw_leaderboard(df):
    """Calculates both the specific command count and the general mention count."""
    df['Content'] = df['Content'].astype(str)
    
    # 1. Specific Pattern: 'bruh [number]'
    cmd_pattern = r'(?i)^bruh\s+(\d+)'
    df['is_cmd'] = df['Content'].str.contains(cmd_pattern, na=False, regex=True)
    
    # 2. General Pattern: Any message containing 'bruh'
    df['is_mention'] = df['Content'].str.contains('bruh', case=False, na=False)

    # Aggregate
    stats = df.groupby('Author').agg(
        Command_Count=('is_cmd', 'sum'),
        Total_Mentions=('is_mention', 'sum')
    ).reset_index()
    
    return stats.sort_values(by='Command_Count', ascending=False)

def run_debug_audit(df, target_user, exclude_str, include_str, show_counted):
    """Filters the user data based on strict inclusion/exclusion and count status."""
    # Filter user first to save memory
    user_df = df[df['Author'] == target_user].copy()
    user_df['Content'] = user_df['Content'].astype(str)
    
    cmd_pattern = r'(?i)^bruh\s+(\d+)'
    user_df['Matches Pattern'] = user_df['Content'].str.contains(cmd_pattern, na=False, regex=True)

    # Strict Filters
    if include_str:
        user_df = user_df[user_df['Content'].str.contains(include_str, case=False, na=False)]
    if exclude_str:
        user_df = user_df[~user_df['Content'].str.contains(exclude_str, case=False, na=False)]

    # Counted vs Not Counted Filter
    if not show_counted:
        user_df = user_df[user_df['Matches Pattern'] == False]
    
    # Return limited results to prevent browser freeze (Latest 500)
    return user_df.tail(500)
