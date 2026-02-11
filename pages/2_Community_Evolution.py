import streamlit as st
import plotly.express as px
from app import load_data
from src.timeline_logic import get_timeline_data
from src.guide_loader import render_markdown_guide

st.set_page_config(page_title="Evolution", page_icon="📈", layout="wide")

st.title("📈 Community Evolution")
df = load_data()

tab_raw, tab_valid = st.tabs(["🥇 Raw Evolution", "⚖️ Valid Evolution"])

# ... (Imports and load_data remain the same) ...

    freq_map = {"Daily": "D", "Weekly": "W"}
    daily, cumulative, display_names = get_timeline_data(df, top_x=top_n, freq=freq_map[time_grain])
    
    plot_df = cumulative if "Cumulative" in chart_type else daily
    group_norm = 'percent' if stack_mode else None

    # Melt for Plotly
    melted_df = plot_df.melt(id_vars='Timestamp', value_vars=display_names, var_name='User', value_name='Bruhs')

    # --- VISUALIZATION ---
    fig = px.area(
        melted_df, 
        x='Timestamp', 
        y='Bruhs', 
        color='User',
        groupnorm=group_norm,
        title=f"The Bruh Timeline: OG Members to New Challengers ({time_grain} View)",
        # We use a color sequence that helps distinguish the layers
        color_discrete_sequence=px.colors.qualitative.Prism 
    )

    fig.update_layout(
        hovermode="x unified",
        xaxis_title="Timeline (Sorted by Join Date)",
        yaxis_title="Share %" if stack_mode else "Bruh Count",
        # Putting legend at the bottom since we might have 50+ names
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
    )
    
    st.plotly_chart(fig, use_container_width=True)


with tab_valid:
    st.info("🏗️ Under Development")
