import streamlit as st

def render_raw_csv_view(df, start_row, end_row):
    """
    Renders a specific slice of the CSV data for manual inspection.
    """
    st.subheader(f"📄 Raw CSV Data (Rows {start_row} - {end_row})")
    # Column 1 is Author, Column 3 is Message
    view_data = df.iloc[start_row:end_row, [1, 3]]
    st.dataframe(view_data, use_container_width=True, height=500)
