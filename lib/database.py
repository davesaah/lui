import sqlite3
from datetime import datetime

DB_NAME = "chat_history.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Table for sessions (the "folders" for chats)
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  created_at DATETIME)''')
    # Table for individual messages
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id INTEGER,
                  role TEXT,
                  content TEXT,
                  timestamp DATETIME,
                  FOREIGN KEY (session_id) REFERENCES sessions (id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT UNIQUE,
                  chunk_count INTEGER,
                  uploaded_at DATETIME)''')
    conn.commit()
    conn.close()


def create_session(title="New Chat"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)",
              (title, datetime.now()))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id


def save_message(session_id, role, content):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
              (session_id, role, content, datetime.now()))
    conn.commit()
    conn.close()


def get_all_sessions():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, title, created_at FROM sessions ORDER BY created_at DESC")
    data = c.fetchall()
    conn.close()
    return data


def get_messages(session_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
    data = [{"role": row[0], "content": row[1]} for row in c.fetchall()]
    conn.close()
    return data


def update_session_title(session_id, new_title):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE sessions SET title = ? WHERE id = ?",
              (new_title, session_id))
    conn.commit()
    conn.close()


def delete_session(session_id):
    """
    Deletes a specific session and all its related messages.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # Delete messages first (Foreign Key cleanup)
        c.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        # Delete the session metadata
        c.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting session: {e}")
        conn.rollback()
    finally:
        conn.close()


def register_document(filename, chunk_count):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO documents (filename, chunk_count, uploaded_at) VALUES (?, ?, ?)",
              (filename, chunk_count, datetime.now()))
    conn.commit()
    conn.close()


def get_all_documents():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT filename, chunk_count, uploaded_at FROM documents")
    rows = c.fetchall()
    conn.close()
    return rows


def delete_document_from_db(filename):
    """Removes the document record from the tracker."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM documents WHERE filename = ?", (filename,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting doc from DB: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
