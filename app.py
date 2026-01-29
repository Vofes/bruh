import streamlit as st
from src.data_loader import get_botcheck_data

st.set_page_config(page_title="Bruh-BotCheck Hub", page_icon="🤖", layout="wide")

st.title("🤖 Bruh-BotCheck Hub")
st.write("Welcome to the central command for Bruh sequence validation.")

# Load data once and store in session_state
if 'df' not in st.session_state:
    with st.status("🔗 Connecting to sequence database...", expanded=True) as status:
        df = get_botcheck_data()
        if df is not None:
            st.session_state['df'] = df
            status.update(label="✅ Database Sync Complete", state="complete", expanded=False)
        else:
            status.update(label="❌ Sync Failed", state="error")

if 'df' in st.session_state:
    st.success(f"File loaded with {len(st.session_state['df']):,} rows of history.")
    st.info("👈 Open the sidebar and select **1 Bruh BotCheck** to begin validation.")
