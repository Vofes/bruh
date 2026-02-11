import streamlit as st
import plotly.express as px
from app import load_data
from src.timeline_logic import get_timeline_data
from src.guide_loader import render_markdown_guide

# Page Config
st.set_page_config(page_title="Evolution", page_icon="📈", layout="wide")

st.title("📈 Community Evolution")
df = load_data()

# Create Tabs
tab_raw, tab_valid = st.tabs(["🥇 Raw Evolution", "⚖️ Valid Evolution"])

with tab_raw:
    # 1. Guide
    with st.expander("📖 Evolution Guide"):
        render_markdown_guide("Raw_Community_Evolution_Guide.md")

    # 2. Controls in 4 columns
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        top_n = st.number_input("Track Top X People", 0, 50, 10)
    with c2:
        time_grain = st.selectbox("Time Grain", ["Daily", "Weekly"])
    with c3:
        chart_type = st.selectbox("Calculation", ["Cumulative (Running Total)", "Incremental (Volume)"])
    with c4:
        stack_mode = st.toggle("100% Stacked Share", value=False)

    st.divider()

    # 3. Data Processing
    freq_map = {"Daily": "D", "Weekly": "W"}
    inc_df, cum_df, display_names = get_timeline_data(df, top_x=top_n, freq=freq_map[time_grain])
    
    if not inc_df.empty:
        plot_df = cum_df if "Cumulative" in chart_type else inc_df
        group_norm = 'percent' if stack_mode else None

        # Prepare for Plotly
        melted_df = plot_df.melt(id_vars='Timestamp', value_vars=display_names, var_name='User', value_name='Bruhs')

        # 4. Charting
        fig = px.area(
            melted_df, 
            x='Timestamp', 
            y='Bruhs', 
            color='User',
            groupnorm=group_norm,
            title=f"The History of the Chain ({time_grain} Grain)",
            color_discrete_sequence=px.colors.qualitative.Prism
        )

        fig.update_layout(
            hovermode="x unified",
            xaxis_title="Time (Sorted by Join Date)",
            yaxis_title="Share %" if stack_mode else "Bruh Count",
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data found to display. Check your 'bruh_log.csv'!")

with tab_valid:
    st.info("🏗️ Under Development")
