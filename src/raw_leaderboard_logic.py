import pandas as pd
import re

def get_static_raw_leaderboard(df):
    """
    Calculates:
    1. Command_Count: Starts with 'bruh [number]'
    2. Total_Mentions: Contains 'bruh' anywhere
    3. Bruh_Percentage: (Command_Count / Total DB Messages) * 100
    """
    total_db_messages = len(df)
    df['Content'] = df['Content'].astype(str)
    
    # 1. Regex Pattern: Starts with 'bruh', a space, and at least one digit
    # Removed $ to allow extra text after the number
    cmd_pattern = r'(?i)^bruh\s+(\d+)'
    df['is_cmd'] = df['Content'].str.contains(cmd_pattern, na=False, regex=True)
    
    # 2. General Mention: Any 'bruh' anywhere
    df['is_mention'] = df['Content'].str.contains('bruh', case=False, na=False)

    # 3. Aggregate by Author
    stats = df.groupby('Author').agg(
        Command_Count=('is_cmd', 'sum'),
        Total_Mentions=('is_mention', 'sum')
    ).reset_index()
    
    # 4. Calculate Density (Accuracy: 3 decimal places)
    if total_db_messages > 0:
        stats['Bruh_Percentage'] = (stats['Command_Count'] / total_db_messages) * 100
        stats['Bruh_Percentage'] = stats['Bruh_Percentage'].round(3)
    else:
        stats['Bruh_Percentage'] = 0.0
    
    return stats.sort_values(by='Command_Count', ascending=False)

def run_debug_audit(df, target_user, exclude_str, include_str, show_counted):
    """
    Strict auditor for debugging specific users.
    Includes performance capping (tail 500) to prevent browser freezing.
    """
    # Filter by user first to keep the dataframe small in memory
    user_df = df[df['Author'] == target_user].copy()
    user_df['Content'] = user_df['Content'].astype(str)
    
    cmd_pattern = r'(?i)^bruh\s+(\d+)'
    user_df['Matches Pattern'] = user_df['Content'].str.contains(cmd_pattern, na=False, regex=True)

    # Apply Inclusion Filter (Check if word exists ANYWHERE in message)
    if include_str:
        user_df = user_df[user_df['Content'].str.contains(include_str, case=False, na=False)]
    
    # Apply Exclusion Filter (Remove if word exists ANYWHERE in message)
    if exclude_str:
        user_df = user_df[~user_df['Content'].str.contains(exclude_str, case=False, na=False)]

    # Filter by 'Counted' status
    # If show_counted is False, we only show what FAILED the regex
    if not show_counted:
        user_df = user_df[user_df['Matches Pattern'] == False]
    
    # Return limited results (Latest 500) for performance
    return user_df.tail(500)
