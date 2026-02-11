import pandas as pd

def get_timeline_data(df, top_x=10, freq='D'):
    """
    freq: 'D' for Daily, 'W' for Weekly
    """
    df = df.copy()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    cmd_pattern = r'(?i)^bruh\s+(\d+)'
    df['is_cmd'] = df['Content'].str.contains(cmd_pattern, na=False, regex=True)
    
    # 1. Filter only valid commands
    bruh_df = df[df['is_cmd']].copy()
    
    # 2. Identify Top X authors globally
    top_authors = bruh_df.groupby('Author').size().nlargest(top_x).index.tolist()
    
    # 3. Create a helper column to group 'Others'
    bruh_df['Chart_Group'] = bruh_df['Author'].apply(lambda x: x if x in top_authors else 'Others')
    
    # 4. Resample by Date and Group
    # Set timestamp as index for resampling
    bruh_df = bruh_df.set_index('Timestamp')
    
    # Group by Frequency ('D' or 'W') and the Chart_Group
    timeline = bruh_df.groupby([pd.Grouper(freq=freq), 'Chart_Group']).size().unstack(fill_value=0)
    
    # 5. Ensure 'Others' exists as a column even if Top X covers everyone
    if 'Others' not in timeline.columns:
        timeline['Others'] = 0

    # 6. Sort columns: Top Authors first, then Others
    ordered_cols = top_authors + ['Others']
    timeline = timeline[ordered_cols]
    
    # 7. Calculate Cumulative
    incremental_df = timeline.reset_index()
    cumulative_df = timeline.cumsum().reset_index()
    
    return incremental_df, cumulative_df, ordered_cols
