import streamlit as st
from src.data_loader import get_botcheck_data

st.set_page_config(page_title="Bruh-BotCheck Hub", page_icon="🤖", layout="wide")

st.title("🤖 Bruh-BotCheck Hub")

if 'df' not in st.session_state:
    with st.status("🔗 Connecting to sequence database...", expanded=True) as status:
        df = get_botcheck_data()
        if df is not None:
            st.session_state['df'] = df
            status.update(label="✅ Database Sync Complete", state="complete", expanded=False)
        else:
            status.update(label="❌ Sync Failed", state="error")

if 'df' in st.session_state:
    df = st.session_state['df']
    
    st.subheader("📊 CSV Status")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total Rows in File", f"{len(df):,}")
    with c2:
        try:
            # We look at the last row, and try to find a column that looks like a date/time
            # Usually index 2 or 4 in these Discord exports
            last_row = df.iloc[-1]
            date_val = "Not Found"
            for val in last_row:
                if any(char in str(val) for char in ['-', ':', '/']) and len(str(val)) > 5:
                    date_val = str(val)
                    break
            st.metric("Latest Update (CSV Date)", date_val)
        except:
            st.metric("Latest Update", "N/A")

    st.info("👈 Open the sidebar and select **1 Bruh BotCheck** to begin.")
