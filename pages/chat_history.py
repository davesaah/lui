import streamlit as st
from lib.database import delete_session, get_all_sessions, get_messages


col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.subheader("Chat history")

sessions = get_all_sessions()

if not sessions:
    st.info("No saved chats yet. Start a conversation in the new chat window!")

for session_id, title, date in sessions:
    # Format the date nicely
    clean_date = date[:16]  # YYYY-MM-DD HH:MM

    col1, col2 = st.columns([4, 1])
    with col1:
        if st.button(
            f"{title} ({clean_date})", key=f"btn_{session_id}",
            use_container_width=True
        ):
            # 1. Load messages into session state
            st.session_state.messages = get_messages(session_id)
            # 2. Store current session ID to continue saving here
            st.session_state.current_session_id = session_id

            # 3. Redirect automatically
            # Note: The path must match the filename of your chat page exactly
            st.switch_page("pages/chat.py")
    with col2:
        # You could add a delete button here later
        with st.popover(":material/delete:"):
            st.warning("Delete this chat?")
            if st.button("Confirm", key=f"del_{session_id}"):
                delete_session(session_id)
                # If the deleted chat is the one currently loaded,
                # reset the state
                if st.session_state.get("current_session_id") == session_id:
                    st.session_state.messages = []
                    st.session_state.current_session_id = None
                st.rerun()
