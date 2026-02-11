import pandas as pd

def get_timeline_data(df, top_x=5):
    # 1. Clean Data
    df = df.copy()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Date'] = df['Timestamp'].dt.date
    
    # 2. Identify Top X Bruh-ers (overall) to keep the chart clean
    cmd_pattern = r'(?i)^bruh\s+(\d+)'
    df['is_cmd'] = df['Content'].str.contains(cmd_pattern, na=False, regex=True)
    
    top_authors = df[df['is_cmd']].groupby('Author')['is_cmd'].sum().nlargest(top_x).index.tolist()
    
    # 3. Filter for only these authors and group by date
    timeline = df[df['is_cmd'] & df['Author'].isin(top_authors)]
    daily_counts = timeline.groupby(['Date', 'Author']).size().unstack(fill_value=0).reset_index()
    
    # Ensure all dates are present (fill gaps)
    all_dates = pd.date_range(start=daily_counts['Date'].min(), end=daily_counts['Date'].max()).date
    daily_counts = daily_counts.set_index('Date').reindex(all_dates, fill_value=0).rename_axis('Date').reset_index()
    
    # 4. Calculate Cumulative
    cumulative_counts = daily_counts.set_index('Date').cumsum().reset_index()
    
    return daily_counts, cumulative_counts, top_authors
