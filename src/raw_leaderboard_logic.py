import pandas as pd
import re
import plotly.express as px

def get_static_raw_leaderboard(df):
    """
    Calculates the primary stats for the community.
    """
    total_db_messages = len(df)
    df['Content'] = df['Content'].astype(str)
    
    # 1. Regex Pattern: Starts with 'bruh', a space, and at least one digit
    cmd_pattern = r'(?i)^bruh\s+(\d+)'
    df['is_cmd'] = df['Content'].str.contains(cmd_pattern, na=False, regex=True)
    
    # 2. General Mention: Any 'bruh' anywhere
    df['is_mention'] = df['Content'].str.contains('bruh', case=False, na=False)

    # 3. Aggregate by Author
    stats = df.groupby('Author').agg(
        Command_Count=('is_cmd', 'sum'),
        Total_Mentions=('is_mention', 'sum')
    ).reset_index()
    
    # 4. Calculate Density (3 decimal places)
    if total_db_messages > 0:
        stats['Bruh_Percentage'] = (stats['Command_Count'] / total_db_messages) * 100
        stats['Bruh_Percentage'] = stats['Bruh_Percentage'].round(3)
    else:
        stats['Bruh_Percentage'] = 0.0
    
    return stats.sort_values(by='Command_Count', ascending=False)

def get_bruh_pie_chart(lb_df):
    """Generates an interactive donut chart of Bruh distribution."""
    # Take the top 10 and group the rest into 'Others' to keep the chart clean
    top_10 = lb_df.head(10).copy()
    if len(lb_df) > 10:
        others_count = lb_df.iloc[10:]['Command_Count'].sum()
        others_row = pd.DataFrame({'Author': ['Others'], 'Command_Count': [others_count]})
        chart_data = pd.concat([top_10, others_row], ignore_index=True)
    else:
        chart_data = top_10

    fig = px.pie(
        chart_data, 
        values='Command_Count', 
        names='Author',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
    return fig

def run_debug_audit(df, target_user, exclude_str, include_str, show_counted):
    """Strict auditor for debugging specific users."""
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
