import pandas as pd

def get_timeline_data(df, top_x=10, freq='D'):
    df = df.copy()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    cmd_pattern = r'(?i)^bruh\s+(\d+)'
    df['is_cmd'] = df['Content'].str.contains(cmd_pattern, na=False, regex=True)
    
    # 1. Filter only valid commands
    bruh_df = df[df['is_cmd']].copy()
    
    # 2. Identify Top X authors globally
    top_authors_list = bruh_df.groupby('Author').size().nlargest(top_x).index.tolist()
    
    # 3. Determine Chronological Order (When did they first bruh?)
    # We only care about the top_authors for this sorting
    first_appearances = bruh_df[bruh_df['Author'].isin(top_authors_list)].groupby('Author')['Timestamp'].min()
    chrono_top_authors = first_appearances.sort_values().index.tolist()
    
    # 4. Create a helper column to group 'Others'
    bruh_df['Chart_Group'] = bruh_df['Author'].apply(lambda x: x if x in top_authors_list else 'Others')
    
    # 5. Resample
    bruh_df = bruh_df.set_index('Timestamp')
    timeline = bruh_df.groupby([pd.Grouper(freq=freq), 'Chart_Group']).size().unstack(fill_value=0)
    
    if 'Others' not in timeline.columns:
        timeline['Others'] = 0

    # 6. Sorting the Columns: 
    # 'Others' first (bottom of the stack), then Top Authors in order of joining
    ordered_cols = ['Others'] + chrono_top_authors
    
    # Filter timeline to only include these columns (and handle cases with 0 users)
    timeline = timeline.reindex(columns=ordered_cols, fill_value=0)
    
    incremental_df = timeline.reset_index()
    cumulative_df = timeline.cumsum().reset_index()
    
    return incremental_df, cumulative_df, ordered_cols
