import streamlit as st
from src.data_loader import get_botcheck_data

st.set_page_config(page_title="Bruh-BotCheck Hub", page_icon="🤖", layout="wide")

st.title("🤖 Bruh-BotCheck Hub")
st.write("Welcome to the central command for Bruh sequence validation.")

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
            # Assuming Date is Column 0 and Author is Column 1
            last_time = df.iloc[-1, 0]
            st.metric("Latest Update (CSV Date)", str(last_time))
        except:
            st.metric("Latest Update", "N/A")

    st.success("Data is ready for analysis.")
    st.info("👈 Open the sidebar and select **1 Bruh BotCheck** to begin.")
