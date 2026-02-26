import uuid
import streamlit as st
from lib.database import get_all_documents, register_document
from lib.rag_utils import collection, process_memory_file
from lib.rag_utils import remove_document_completely


col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.header("Local Knowledge Base")

# Initialize a uploader key if it doesn't exist
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())

st.subheader("Add New Documents")

# Standard file uploader for the RAG page
new_files = st.file_uploader(
    "Select files to add to the AI's memory",
    accept_multiple_files=True,
    type=[
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
    key=st.session_state.uploader_key,
)

if new_files:
    if st.button("Process and Index Files", use_container_width=True):
        with st.status("Indexing documents...", expanded=True) as status:
            for uploaded_file in new_files:
                status.write(f"Reading {uploaded_file.name}...")

                # 1. Chunk in memory
                chunks, _ = process_memory_file(uploaded_file)

                # 2. Add to ChromaDB
                status.write(
                    f"Generating embeddings for {len(chunks)} chunks...")

                # 3. Save to SQLite tracker
                register_document(uploaded_file.name, len(chunks))
                status.write(f"{uploaded_file.name} finished.")

            status.update(label="Knowledge base updated!", state="complete")

        st.session_state.uploader_key = str(uuid.uuid4())
        st.rerun()

st.divider()

st.subheader("Current Library")

# Check if collection is empty
if collection.count() == 0:
    st.info("Your library is empty. Upload files above to begin.")
else:
    docs = get_all_documents()
    h1, h2, h3 = st.columns([3, 1, 1])
    h1.caption("FILENAME")
    h2.caption("CHUNKS")
    h3.caption("ACTIONS")

    for filename, count, date in docs:
        col1, col2, col3 = st.columns([3, 1, 1])

        col1.write(f"**{filename}**")
        col2.write(str(count))

        with col3.popover("️:material/delete:"):
            st.write("Delete this file?")
            if st.button("Confirm", key=f"del_{filename}"):
                remove_document_completely(filename)
                st.toast(f"Deleted {filename}")
                st.rerun()
