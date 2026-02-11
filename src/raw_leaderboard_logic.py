import pandas as pd
import re
import plotly.express as px


import pandas as pd
import re
import plotly.express as px

def get_static_raw_leaderboard(df):
    """
    Calculates:
    - Raw_Bruhs: Valid 'bruh [number]'
    - Total_Mentions: Any message containing 'bruh'
    - Total_Messages: Every row for this user
    - Bruh_Purity: (Raw_Bruhs / Total_Messages) * 100
    - Global_Share: (Raw_Bruhs / Total_Bruhs_In_Server) * 100
    """
    df['Content'] = df['Content'].astype(str)
    
    # 1. Regex & Mentions logic
    cmd_pattern = r'(?i)^bruh\s+(\d+)'
    df['is_cmd'] = df['Content'].str.contains(cmd_pattern, na=False, regex=True)
    df['is_mention'] = df['Content'].str.contains('bruh', case=False, na=False)

    # 2. Aggregate
    stats = df.groupby('Author').agg(
        Raw_Bruhs=('is_cmd', 'sum'),
        Total_Mentions=('is_mention', 'sum'),
        Total_Messages=('Content', 'count')
    ).reset_index()
    
    # 3. Math
    stats['Bruh_Purity'] = (stats['Raw_Bruhs'] / stats['Total_Messages'] * 100).round(2)
    
    total_raw = stats['Raw_Bruhs'].sum()
    stats['Global_Share'] = (stats['Raw_Bruhs'] / total_raw * 100).round(3) if total_raw > 0 else 0.0

    return stats.sort_values(by='Raw_Bruhs', ascending=False)

def get_bruh_pie_chart(lb_df, threshold):
    """Generates an interactive donut chart based on Bruh_Share threshold."""
    # Note: We use Bruh_Share (market share) for the pie chart as it makes more sense for a "pie"
    above_thresh = lb_df[lb_df['Bruh_Share'] >= threshold].copy()
    below_thresh = lb_df[lb_df['Bruh_Share'] < threshold].copy()
    
    others_count = below_thresh['Raw_Bruhs'].sum()
    
    if others_count > 0:
        others_row = pd.DataFrame({
            'Author': ['Others (Below Threshold)'], 
            'Raw_Bruhs': [others_count],
            'Bruh_Share': [below_thresh['Bruh_Share'].sum()]
        })
        chart_data = pd.concat([above_thresh, others_row], ignore_index=True)
    else:
        chart_data = above_thresh

    fig = px.pie(
        chart_data, 
        values='Raw_Bruhs', 
        names='Author',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title=f"Community Share (Users > {threshold}% Share)"
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
