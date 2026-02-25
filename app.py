import streamlit as st
from lib.database import init_db


# Initialize DB
init_db()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

pg = st.navigation([
    st.Page("pages/chat.py", title="Chat", icon=":material/edit_square:"),
    st.Page("pages/rag.py", title="Manage RAG", icon=":material/database:"),
    st.Page("pages/chat_history.py", title="Chat history",
            icon=":material/history:"),
])

pg.run()
