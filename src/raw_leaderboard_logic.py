import pandas as pd
import re
import plotly.express as px

def get_static_raw_leaderboard(df):
    """Calculates counts and the % density relative to all messages in the DB."""
    total_db_messages = len(df)
    df['Content'] = df['Content'].astype(str)
    
    # 1. Regex Pattern: Starts with 'bruh [number]'
    cmd_pattern = r'(?i)^bruh\s+(\d+)'
    df['is_cmd'] = df['Content'].str.contains(cmd_pattern, na=False, regex=True)
    
    # 2. General Mention: Any 'bruh' anywhere
    df['is_mention'] = df['Content'].str.contains('bruh', case=False, na=False)

    # 3. Aggregate by Author
    stats = df.groupby('Author').agg(
        Command_Count=('is_cmd', 'sum'),
        Total_Mentions=('is_mention', 'sum')
    ).reset_index()
    
    # 4. Calculate Density (%)
    if total_db_messages > 0:
        stats['Bruh_Percentage'] = (stats['Command_Count'] / total_db_messages) * 100
        stats['Bruh_Percentage'] = stats['Bruh_Percentage'].round(3)
    else:
        stats['Bruh_Percentage'] = 0.0

    return stats.sort_values(by='Command_Count', ascending=False)

def get_bruh_pie_chart(lb_df, threshold):
    """Generates an interactive donut chart filtered by the user's slider threshold."""
    # Apply the slider filter only for the chart
    chart_data = lb_df[lb_df['Bruh_Percentage'] >= threshold].copy()
    
    # If the filter leaves too many people, we still group tiny slices into 'Others' 
    # for visual clarity, but only after the user's threshold is met.
    if len(chart_data) > 15:
        top_slice = chart_data.head(15).copy()
        others_count = chart_data.iloc[15:]['Command_Count'].sum()
        others_row = pd.DataFrame({'Author': ['Others'], 'Command_Count': [others_count]})
        chart_data = pd.concat([top_slice, others_row], ignore_index=True)

    fig = px.pie(
        chart_data, 
        values='Command_Count', 
        names='Author',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title=f"Community Distribution (Users > {threshold}% Density)"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(margin=dict(t=40, b=0, l=0, r=0))
    return fig

def run_debug_audit(df, target_user, exclude_str, include_str, show_counted):
    user_df = df[df['Author'] == target_user].copy()
    user_df['Content'] = user_df['Content'].astype(str)
    cmd_pattern = r'(?i)^bruh\s+(\d+)'
    user_df['Matches Pattern'] = user_df['Content'].str.contains(cmd_pattern, na=False, regex=True)

    if include_str:
        user_df = user_df[user_df['Content'].str.contains(include_str, case=False, na=False)]
    if exclude_str:
        user_df = user_df[~user_df['Content'].str.contains(exclude_str, case=False, na=False)]

    if not show_counted:
        user_df = user_df[user_df['Matches Pattern'] == False]
    
    return user_df.tail(500)
