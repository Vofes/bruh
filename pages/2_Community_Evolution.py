import streamlit as st
import plotly.express as px
from app import load_data
from src.timeline_logic import get_timeline_data

st.set_page_config(page_title="Evolution", page_icon="📈", layout="wide")

st.title("📈 Community Evolution")
df = load_data()

# --- Controls ---
with st.sidebar:
    st.header("Chart Settings")
    top_n = st.slider("Number of Legends to track", 3, 15, 5)
    chart_type = st.radio("Calculation Type", ["Cumulative (Running Total)", "Incremental (Daily Volume)"])
    stack_mode = st.checkbox("100% Stacked (Relative Share)", value=False)

# --- Process Data ---
daily, cumulative, top_authors = get_timeline_data(df, top_x=top_n)
plot_df = cumulative if "Cumulative" in chart_type else daily

# --- Logic for 100% Stacked ---
# Plotly uses 'groupnorm' to turn a normal stacked chart into a 100% stacked one.
group_norm = 'percent' if stack_mode else None

# --- Visualization ---
st.subheader(f"{chart_type} for Top {top_n} Users")

# We need to melt the dataframe for Plotly Express
melted_df = plot_df.melt(id_vars='Date', value_vars=top_authors, var_name='User', value_name='Bruhs')

fig = px.area(
    melted_df, 
    x='Date', 
    y='Bruhs', 
    color='User',
    line_group='User',
    groupnorm=group_norm,
    title=f"Bruh Dominance Over Time ({'Percentage Share' if stack_mode else 'Counts'})",
    color_discrete_sequence=px.colors.qualitative.Bold
)

fig.update_layout(hovermode="x unified", yaxis_title="Share %" if stack_mode else "Count")
st.plotly_chart(fig, use_container_width=True)

# --- Summary Stats ---
c1, c2 = st.columns(2)
with c1:
    st.info("💡 **Cumulative** shows who has the biggest 'Legacy'.")
with c2:
    st.info("💡 **100% Stacked** shows who was the most active during specific eras of the server.")
