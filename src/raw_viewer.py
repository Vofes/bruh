import streamlit as st

def render_raw_csv_view(df, start_row, end_row):
    st.subheader(f"📄 Raw CSV Snapshot")
    # Column 1 is Author, Column 3 is Message
    view_data = df.iloc[start_row:end_row, [1, 3]]
    st.dataframe(view_data, use_container_width=True, height=500
