import os
import tempfile
import uuid
import chromadb
import pymupdf.layout  # activate PyMuPDF-Layout in pymupdf
import pymupdf4llm
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from lib.database import delete_document_from_db


# Setup Chroma + Ollama Embedding Function
chroma_client = chromadb.PersistentClient(path="chroma_db")
ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    model_name="nomic-embed-text",
    url="http://localhost:11434/api/embeddings",
)

collection = chroma_client.get_or_create_collection(
    name="local_rag", embedding_function=ollama_ef
)


def process_memory_file(uploaded_file):
    """Processes file buffer, chunks it, and adds to Chroma in batches."""
    # process pdf with pymupdf4llm to preserve layout and extract text
    content = ""
    if uploaded_file.name.lower().endswith(".pdf"):
        # 1. Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name  # example: '/tmp/xyz.pdf'
        try:
            # 2. Pass the PATH to the library
            content = pymupdf4llm.to_text(tmp_path)
        finally:
            # 3. Clean up the file after reading
            os.remove(tmp_path)
    else:
        content = uploaded_file.getvalue().decode("utf-8", errors="ignore")

    filename = uploaded_file.name
    ext = filename.split(".")[-1].lower()

    # 1. Define Splitting Logic
    if ext in ["py", "js", "ts", "go", "cpp", "c", "sql", "html", "vue"]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=150,
            separators=["\nclass ", "\ndef ", "\nfunc ", "\n\n", "\n", " "],
        )
    else:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200)

    chunks = splitter.split_text(content)

    # 2. Add to Collection using Batches
    if chunks:
        add_to_collection_in_batches(chunks, filename)

    return chunks, content


def add_to_collection_in_batches(chunks, filename, batch_size=16):
    """Helper to push chunks to ChromaDB in manageable slices."""
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]

        # Generate unique IDs for this batch
        # Using a combination of filename and index to prevent collisions
        ids = [f"{filename}_{i + j}_{str(uuid.uuid4())[:8]}"
               for j in range(len(batch))]

        # Metadata must match the length of the batch
        metadatas = [{"source": filename} for _ in range(len(batch))]

        collection.add(documents=batch, ids=ids, metadatas=metadatas)
    print(f"Successfully indexed {len(chunks)} chunks for {filename}")


def get_vector_context(query):
    """Retrieves relevant text and its source filename from ChromaDB."""
    results = collection.query(
        query_texts=[query],
        n_results=3,
        include=["documents", "metadatas"],  # Explicitly include metadata
    )

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    context_chunks = []
    for doc, meta in zip(docs, metas):
        source_file = meta.get("source", "Unknown File")
        # Format each chunk with its filename header
        context_chunks.append(f"--- SOURCE: {source_file} ---\n{doc}")

    return "\n\n".join(context_chunks) if context_chunks else ""


def remove_document_completely(filename):
    # 1. Remove from ChromaDB
    # This deletes all chunks where the metadata 'source' matches the filename
    try:
        collection.delete(where={"source": filename})
    except Exception as e:
        print(f"Failed to remove vectors for {filename}: {e}")

    # 2. Remove from SQLite tracker
    delete_document_from_db(filename)
