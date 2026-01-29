import streamlit as st

def render_raw_csv_view(df, start_row, end_row):
    st.subheader(f"📄 Raw CSV Data (Rows {start_row} - {end_row})")

    try:
        view_data = df.iloc[start_row:end_row][['Author', 'Content']]
        st.dataframe(view_data, use_container_width=True, height=500)
    except KeyError:
        # Fallback in case column names aren't set yet
        st.error("Column names 'Author' or 'Content' not found. Displaying by index instead.")
        view_data = df.iloc[start_row:end_row, [1, 3]]
        st.dataframe(view_data, use_container_width=True, height=500)
