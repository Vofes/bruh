import streamlit as st

def render_raw_csv_view(df, start_row, end_row):
    st.subheader(f"📄 Raw CSV Data (Rows {start_row} - {end_row})")
    # Using column indices 1 (Author) and 3 (Message)
    view_data = df.iloc[start_row:end_row, [1, 3]]
    st.dataframe(view_data, use_container_width=True, height=500)
