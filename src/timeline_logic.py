import pandas as pd

def get_timeline_data(df, top_x=10):
    df = df.copy()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Date'] = df['Timestamp'].dt.date
    
    cmd_pattern = r'(?i)^bruh\s+(\d+)'
    df['is_cmd'] = df['Content'].str.contains(cmd_pattern, na=False, regex=True)
    
    # 1. Identify Top X authors
    full_counts = df[df['is_cmd']].groupby('Author')['is_cmd'].sum()
    top_authors = full_counts.nlargest(top_x).index.tolist()
    
    # 2. Create daily stats for EVERYONE
    daily_all = df[df['is_cmd']].groupby(['Date', 'Author']).size().unstack(fill_value=0)
    
    # 3. Split into Top X and Others
    main_df = daily_all[top_authors].copy()
    others_cols = [c for c in daily_all.columns if c not in top_authors]
    
    if others_cols:
        main_df['Others'] = daily_all[others_cols].sum(axis=1)
    
    # 4. Reindex to fill missing dates
    all_dates = pd.date_range(start=main_df.index.min(), end=main_df.index.max()).date
    main_df = main_df.reindex(all_dates, fill_value=0).rename_axis('Date').reset_index()
    
    # 5. Calculate Cumulative version
    cumulative_df = main_df.set_index('Date').cumsum().reset_index()
    
    # Return Top X + 'Others' in the name list
    display_names = top_authors + (['Others'] if others_cols else [])
    
    return main_df, cumulative_df, display_names
