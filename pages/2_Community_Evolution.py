import streamlit as st
import plotly.express as px
from app import load_data
from src.timeline_logic import get_timeline_data
from src.guide_loader import render_markdown_guide

st.set_page_config(page_title="Evolution", page_icon="📈", layout="wide")

st.title("📈 Community Evolution")
df = load_data()

tab_raw, tab_valid = st.tabs(["🥇 Raw Evolution", "⚖️ Valid Evolution"])

with tab_raw:
    with st.expander("📖 Evolution Guide"):
        render_markdown_guide("Raw_Community_Evolution_Guide.md")

    # --- UPDATED CONTROLS ---
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    with c1:
        top_n = st.number_input("Track Top X People", 0, 50, 10)
    with c2:
        # Added Weekly option
        time_grain = st.selectbox("Time Grain", ["Daily", "Weekly"])
    with c3:
        chart_type = st.selectbox("Calculation", ["Cumulative (Running Total)", "Incremental (Volume)"])
    with c4:
        stack_mode = st.toggle("100% Stacked", value=False)

    st.divider()

    # --- PROCESS ---
    freq_map = {"Daily": "D", "Weekly": "W"}
    daily, cumulative, display_names = get_timeline_data(df, top_x=top_n, freq=freq_map[time_grain])
    
    plot_df = cumulative if "Cumulative" in chart_type else daily
    group_norm = 'percent' if stack_mode else None

    # Use 'Timestamp' because that's what the resampler returns
    melted_df = plot_df.melt(id_vars='Timestamp', value_vars=display_names, var_name='User', value_name='Bruhs')

    # --- VISUALIZATION ---
    fig = px.area(
        melted_df, 
        x='Timestamp', 
        y='Bruhs', 
        color='User',
        groupnorm=group_norm,
        title=f"Evolution of the Bruh Meta ({time_grain} View)",
        color_discrete_sequence=px.colors.qualitative.Alphabet
    )

    fig.update_layout(
        hovermode="x unified",
        xaxis_title="Timeline",
        yaxis_title="Share %" if stack_mode else "Bruh Count",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab_valid:
    st.info("🏗️ Under Development")
