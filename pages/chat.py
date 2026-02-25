import threading
import time
import streamlit as st
from client_tasks import update_title_task
from lib.database import create_session, register_document, save_message
from lib.ollama_client import fetch_models, stream_response
from lib.rag_utils import collection, get_vector_context, process_memory_file


# Sidebar
if st.sidebar.button("New chat", use_container_width=True):
    st.session_state.messages = []
    st.session_state.current_session_id = None
    st.rerun()

st.sidebar.subheader("Model options")
model = st.sidebar.selectbox("Select model", fetch_models())

st.sidebar.subheader("RAG options")
use_full_rag = st.sidebar.checkbox("Use entire knowledge database")

# rag_options = [None]
# rag_options.extend(fetch_models())
# rag_items = []
# if not use_full_rag:
#     rag_items = st.sidebar.multiselect("Select context", rag_options)

# Centered title
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.subheader("What can I help you with?")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# Chat input
prompt = st.chat_input(
    placeholder="Ask anything...",
    accept_file="multiple",
    file_type=[
        "csv",
        "txt",
        "md",
        "json",
        "py",
        "js",
        "go",
        "c",
        "cpp",
        "sh",
        "sql",
        "sm",
        "vue",
        "yaml",
        "toml",
        "yml",
        "html",
        "ts",
        "pdf",
    ],
)


if prompt:
    file_context = ""
    # Handle File Uploads
    if prompt.files:
        use_full_rag = True
        for uploaded_file in prompt.files:
            with st.spinner(f"Indexing {uploaded_file.name}..."):
                chunks, content = process_memory_file(uploaded_file)
                if chunks:
                    register_document(uploaded_file.name, len(chunks))
                    file_context = content
        st.toast(f"Indexed {len(prompt.files)} files to memory.")

    # Create a session in DB if it's a brand new conversation
    if st.session_state.current_session_id is None:
        # Use first 25 chars of prompt as title
        title = prompt.text[:25] + "..."
        st.session_state.current_session_id = create_session(title)

    full_prompt = prompt.text

    # Get Context from RAG
    if use_full_rag and collection.count() > 0:
        context = get_vector_context(prompt.text)
        full_prompt = f"""You are a helpful assistant. Use the provided context
to answer the user's question. Always mention the filename you are referencing
in your answer.

SNIPPET CONTEXT:
{context}

UPLOADED FILE CONTEXT:
{file_context}

USER QUESTION:
{prompt.text}
"""
    st.chat_message("user").markdown(prompt.text)
    st.session_state.messages.append({"role": "user", "content": full_prompt})

    # Save user message to DB
    save_message(st.session_state.current_session_id, "user", prompt.text)

    # generate a title based on first 3 messages
    if len(st.session_state.messages) == 3:
        thread = threading.Thread(
            target=update_title_task.run,
            args=(
                st.session_state.messages.copy(),
                st.session_state.current_session_id,
                model,
            ),
        )
        thread.start()

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        start_time = time.perf_counter()
        with st.status("Thinking...", expanded=False) as status:
            response_stream = stream_response(
                messages=st.session_state.messages, model=model,
                use_rag=use_full_rag
            )

            # This consumes the first token while the status is still "Running"
            try:
                first_token = next(response_stream)
                full_response += first_token
            except StopIteration:
                pass

            total_time = time.perf_counter() - start_time
            status.update(
                label=f"Generated in {total_time:.2f}s", state="complete")

        # 3. Now show the text and stream the rest
        placeholder.markdown(full_response + "▌")
        for token in response_stream:
            full_response += token
            placeholder.markdown(full_response + "▌")

        placeholder.markdown(full_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": full_response})

    # Save assistant message to DB after stream completes
    save_message(st.session_state.current_session_id,
                 "assistant", full_response)
