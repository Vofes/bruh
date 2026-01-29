import streamlit as st
from src.data_loader import get_botcheck_data

st.set_page_config(page_title="Bruh-BotCheck Hub", page_icon="🤖", layout="wide")

st.title("🤖 Bruh-BotCheck Hub")
st.write("Welcome to the central command for Bruh sequence validation.")


if 'df' in st.session_state:
    df = st.session_state['df']
    st.success(f"File loaded with {len(df):,} rows of history.")
    
    # --- NEW: STATS SECTION ---
    st.subheader("📊 CSV Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Messages", f"{len(df):,}")
    
    with col2:
        # Assuming the date is in the first column (index 0)
        try:
            last_date = df.iloc[-1, 0] 
            st.metric("Latest Update", str(last_date))
        except:
            st.metric("Latest Update", "Unknown")
            
    with col3:
        # Check for the last user to post
        try:
            last_author = df.iloc[-1, 1]
            st.write(f"**Last active user:** {last_author}")
        except:
            pass

    st.success(f"File loaded with {len(st.session_state['df']):,} rows of history.")
    st.info("👈 Open the sidebar and select **Bruh BotCheck** to begin validation.")
