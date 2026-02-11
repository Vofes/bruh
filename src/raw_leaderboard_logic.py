import pandas as pd
import re
import plotly.express as px

def get_static_raw_leaderboard(df):
    """
    Calculates:
    - Command_Count: Valid 'bruh [number]'
    - Total_Channel_Messages: Total rows for this user in the CSV
    - Bruh_Purity: (Valid Bruhs / Total Channel Messages) * 100
    - Bruh_Percentage: Share of the total community bruh-pot.
    """
    df['Content'] = df['Content'].astype(str)
    
    # 1. Regex Pattern for valid commands
    cmd_pattern = r'(?i)^bruh\s+(\d+)'
    df['is_cmd'] = df['Content'].str.contains(cmd_pattern, na=False, regex=True)

    # 2. Aggregate counts per Author
    # We count 'is_cmd' (the Trues) and 'Content' (size of all rows)
    stats = df.groupby('Author').agg(
        Raw_Bruhs=('is_cmd', 'sum'),
        Total_Messages=('Content', 'count')
    ).reset_index()
    
    # 3. Calculate "Bruh Purity" (User's Bruhs / User's Total Messages in this file)
    stats['Bruh_Purity'] = (stats['Raw_Bruhs'] / stats['Total_Messages']) * 100
    stats['Bruh_Purity'] = stats['Bruh_Purity'].round(2)
    
    # 4. Calculate "Global Share" (User's Bruhs / Total Bruhs in community)
    total_community_bruhs = stats['Raw_Bruhs'].sum()
    if total_community_bruhs > 0:
        stats['Bruh_Share'] = (stats['Raw_Bruhs'] / total_community_bruhs) * 100
        stats['Bruh_Share'] = stats['Bruh_Share'].round(3)
    else:
        stats['Bruh_Share'] = 0.0

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
