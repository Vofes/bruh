import streamlit as st
import plotly.express as px
from app import load_data
from src.timeline_logic import get_timeline_data
from src.guide_loader import render_markdown_guide

st.set_page_config(page_title="Evolution", page_icon="📈", layout="wide")

st.title("📈 Community Evolution")
df = load_data()

# --- 2. MAIN TABS ---
tab_raw, tab_valid = st.tabs(["🥇 Raw Evolution", "⚖️ Valid Evolution"])

with tab_raw:
    # Load Guide
    with st.expander("📖 Evolution Guide"):
        render_markdown_guide("Raw_Community_Evolution_Guide.md")

    # --- Controls (Now in Main Page) ---
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        top_n = st.number_input("Track Top X People", min_value=0, max_value=50, value=10)
    with c2:
        chart_type = st.selectbox("Calculation Type", ["Cumulative (Running Total)", "Incremental (Daily Volume)"])
    with c3:
        stack_mode = st.toggle("100% Stacked (Relative Share)", value=False)

    st.divider()

    # --- Process Data ---
    daily, cumulative, display_names = get_timeline_data(df, top_x=top_n)
    plot_df = cumulative if "Cumulative" in chart_type else daily

    # Plotly Stack Logic
    group_norm = 'percent' if stack_mode else None

    # Melt data for Plotly
    melted_df = plot_df.melt(id_vars='Date', value_vars=display_names, var_name='User', value_name='Bruhs')

    # --- Visualization ---
    fig = px.area(
        melted_df, 
        x='Date', 
        y='Bruhs', 
        color='User',
        groupnorm=group_norm,
        title=f"The Rise and Fall of Bruh Dynasties",
        color_discrete_sequence=px.colors.qualitative.Alphabet # Alphabet is better for up to 50 colors
    )

    fig.update_layout(
        hovermode="x unified", 
        yaxis_title="Share %" if stack_mode else "Count",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab_valid:
    st.info("🏗️ Under Development - The Council is still verifying the historical archives.")

st.divider()
