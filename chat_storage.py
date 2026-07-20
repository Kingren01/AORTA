import json
import sqlite3
import uuid
from typing import Any
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "chat_history.db"

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the SQLite schema if it doesn't exist."""
    with _get_conn() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                tool_traces TEXT,
                sources_enabled TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        ''')
        
        # Add new columns for session state persistence (idempotent)
        new_columns = [
            ("doc", "TEXT"),
            ("entities", "TEXT"),
            ("graph_json", "TEXT"),
            ("graph_xml", "TEXT"),
            ("vector_chunks", "TEXT"),
            ("updated_at", "TIMESTAMP"),
        ]
        for col, col_type in new_columns:
            try:
                conn.execute(f"ALTER TABLE conversations ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass # Column already exists

        # Backfill updated_at for rows that pre-date the column
        conn.execute(
            "UPDATE conversations SET updated_at = created_at WHERE updated_at IS NULL"
        )
                
        conn.commit()

# Ensure DB is initialized when module is loaded
init_db()

def create_conversation(title: str = "New Conversation") -> str:
    """Create a new conversation and return its UUID."""
    conv_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conv_id, title, now, now)
        )
        conn.commit()
    return conv_id

def list_conversations() -> list[dict[str, Any]]:
    """List all conversations ordered by most recently active (newest first).
    
    Includes a message_count for each conversation.
    """
    with _get_conn() as conn:
        cursor = conn.execute('''
            SELECT c.id, c.title, c.created_at,
                   COALESCE(c.updated_at, c.created_at) AS updated_at,
                   COUNT(m.id) AS message_count
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
            GROUP BY c.id
            ORDER BY COALESCE(c.updated_at, c.created_at) DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

def search_conversations(query: str) -> list[dict[str, Any]]:
    """Search conversations by title (case-insensitive LIKE match)."""
    with _get_conn() as conn:
        pattern = f"%{query}%"
        cursor = conn.execute('''
            SELECT c.id, c.title, c.created_at,
                   COALESCE(c.updated_at, c.created_at) AS updated_at,
                   COUNT(m.id) AS message_count
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
            WHERE c.title LIKE ? COLLATE NOCASE
            GROUP BY c.id
            ORDER BY COALESCE(c.updated_at, c.created_at) DESC
        ''', (pattern,))
        return [dict(row) for row in cursor.fetchall()]

def add_message(
    conversation_id: str, 
    role: str, 
    content: str, 
    tool_traces: list[dict] | None = None,
    sources_enabled: list[str] | None = None
) -> str:
    """Add a message to a conversation. Returns the message ID."""
    msg_id = str(uuid.uuid4())
    traces_json = json.dumps(tool_traces) if tool_traces else None
    sources_json = json.dumps(sources_enabled) if sources_enabled else None
    now = datetime.utcnow().isoformat()
    
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, tool_traces, sources_enabled) VALUES (?, ?, ?, ?, ?, ?)",
            (msg_id, conversation_id, role, content, traces_json, sources_json)
        )
        # Update updated_at timestamp
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id)
        )
        # Auto-title from first user message if still default
        if role == "user":
            cursor = conn.execute("SELECT title FROM conversations WHERE id = ?", (conversation_id,))
            row = cursor.fetchone()
            if row and row["title"] == "New Conversation":
                # Clean up: collapse whitespace, take first 50 chars at word boundary
                clean = " ".join(content.split())
                if len(clean) > 50:
                    truncated = clean[:50].rsplit(" ", 1)[0]
                    new_title = truncated + "…"
                else:
                    new_title = clean
                conn.execute("UPDATE conversations SET title = ? WHERE id = ?", (new_title, conversation_id))
        conn.commit()
    return msg_id

def get_conversation_messages(conversation_id: str) -> list[dict[str, Any]]:
    """Get all messages for a specific conversation in chronological order."""
    with _get_conn() as conn:
        cursor = conn.execute(
            "SELECT id, role, content, tool_traces, sources_enabled, timestamp FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
            (conversation_id,)
        )
        messages = []
        for row in cursor.fetchall():
            msg = dict(row)
            msg["tool_traces"] = json.loads(msg["tool_traces"]) if msg["tool_traces"] else []
            msg["sources_enabled"] = json.loads(msg["sources_enabled"]) if msg["sources_enabled"] else []
            messages.append(msg)
        return messages

def update_conversation_title(conversation_id: str, new_title: str):
    """Update the title of an existing conversation."""
    with _get_conn() as conn:
        conn.execute("UPDATE conversations SET title = ? WHERE id = ?", (new_title, conversation_id))
        conn.commit()

def delete_conversation(conversation_id: str):
    """Delete a conversation and all its messages."""
    with _get_conn() as conn:
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        conn.commit()

def clear_all():
    """Clear all data (for testing purposes)."""
    with _get_conn() as conn:
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM conversations")
        conn.commit()

def update_conversation_run_data(
    conversation_id: str,
    doc: dict | None,
    entities: list | None,
    graph_json: dict | None,
    graph_xml: str | None,
    vector_chunks: list | None
):
    """Save the document extraction state into the conversation."""
    now = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        conn.execute('''
            UPDATE conversations 
            SET doc = ?, entities = ?, graph_json = ?, graph_xml = ?, vector_chunks = ?, updated_at = ?
            WHERE id = ?
        ''', (
            json.dumps(doc) if doc else None,
            json.dumps(entities) if entities else None,
            json.dumps(graph_json) if graph_json else None,
            graph_xml,
            json.dumps(vector_chunks) if vector_chunks else None,
            now,
            conversation_id
        ))
        conn.commit()

def get_conversation_state(conversation_id: str) -> dict[str, Any]:
    """Get the extraction state for a conversation."""
    with _get_conn() as conn:
        cursor = conn.execute(
            "SELECT doc, entities, graph_json, graph_xml, vector_chunks FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        row = cursor.fetchone()
        if not row:
            return {}
        
        return {
            "doc": json.loads(row["doc"]) if row["doc"] else None,
            "entities": json.loads(row["entities"]) if row["entities"] else [],
            "graph_json": json.loads(row["graph_json"]) if row["graph_json"] else None,
            "graph_xml": row["graph_xml"],
            "vector_chunks": json.loads(row["vector_chunks"]) if row["vector_chunks"] else []
        }
