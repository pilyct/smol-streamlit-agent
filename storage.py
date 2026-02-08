"""
Storage and retrieval layer for the document agent.

Uses SQLite for persistence and stores BM25-compatible tokens as TEXT.
Provides:
- document storage
- chunk storage
- retrieval helpers
- summary cache
- Q&A cache
"""

import os
import sqlite3
import re
import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Tuple

DB_PATH = os.getenv("DOC_AGENT_DB", "doc_agent.db")

# -------------------------
# Tokenization + chunking
# -------------------------

_WORD_RE = re.compile(r"[A-Za-z0-9_]+", re.UNICODE)

def tokenize(text: str) -> List[str]:
    """Simple tokenizer for BM25."""
    return [t.lower() for t in _WORD_RE.findall(text)]

def chunk_text(text: str, max_chars: int = 2200, overlap: int = 250) -> List[str]:
    """
    Split text into overlapping chunks.
    Char-based chunking keeps it model-agnostic and cheap.
    """
    text = (text or "").strip()
    if not text:
        return []

    chunks = []
    i = 0
    n = len(text)

    while i < n:
        end = min(i + max_chars, n)
        chunk = text[i:end].strip()
        if chunk:
            chunks.append(chunk)

        if end == n:
            break

        i = max(0, end - overlap)

    return chunks

# -------------------------
# DB initialization
# -------------------------

def init_db():
    """Initialize SQLite database and tables."""
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            summary TEXT
        );
        """)

        con.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            tokens TEXT NOT NULL,
            FOREIGN KEY(doc_id) REFERENCES documents(id)
        );
        """)

        con.execute("""
        CREATE TABLE IF NOT EXISTS qa_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_name TEXT NOT NULL,
            question_hash TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(doc_name, question_hash)
        );
        """)

        con.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);")
        con.execute("CREATE INDEX IF NOT EXISTS idx_docs_name ON documents(name);")
        con.execute("CREATE INDEX IF NOT EXISTS idx_qa_doc ON qa_cache(doc_name);")

# -------------------------
# Document storage
# -------------------------

def upsert_document(name: str, created_at_iso: str) -> int:
    """Insert document if not exists and return its id."""
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT OR IGNORE INTO documents(name, created_at, summary) VALUES (?, ?, NULL);",
            (name, created_at_iso),
        )
        row = con.execute(
            "SELECT id FROM documents WHERE name = ?;",
            (name,),
        ).fetchone()

    return int(row[0])

def list_documents() -> List[Tuple[str, str]]:
    """Return list of (name, created_at)."""
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute(
            "SELECT name, created_at FROM documents ORDER BY id DESC;"
        ).fetchall()
    return [(r[0], r[1]) for r in rows]

def delete_document(name: str):
    """Delete a document and all associated chunks and cache."""
    with sqlite3.connect(DB_PATH) as con:
        row = con.execute(
            "SELECT id FROM documents WHERE name=?;",
            (name,),
        ).fetchone()

        if not row:
            return

        doc_id = int(row[0])
        con.execute("DELETE FROM chunks WHERE doc_id=?;", (doc_id,))
        con.execute("DELETE FROM documents WHERE id=?;", (doc_id,))
        con.execute("DELETE FROM qa_cache WHERE doc_name=?;", (name,))

def insert_chunks(doc_id: int, chunks: List[str]):
    """
    Replace chunks for a document.

    IMPORTANT:
    - `tokens` must be stored as TEXT, not a Python list.
    - We store tokens as a single space-separated string.
    """
    with sqlite3.connect(DB_PATH) as con:
        con.execute("DELETE FROM chunks WHERE doc_id=?;", (doc_id,))

        for idx, ch in enumerate(chunks):
            # FIX: store tokens as a TEXT string, not a list
            toks_text = " ".join(tokenize(ch))
            con.execute(
                "INSERT INTO chunks(doc_id, chunk_index, content, tokens) VALUES (?, ?, ?, ?);",
                (doc_id, idx, ch, toks_text),
            )

# -------------------------
# Document retrieval
# -------------------------

def get_document_text(name: str) -> Optional[str]:
    """Return full text of a document."""
    with sqlite3.connect(DB_PATH) as con:
        row = con.execute(
            "SELECT id FROM documents WHERE name=?;",
            (name,),
        ).fetchone()

        if not row:
            return None

        doc_id = int(row[0])
        rows = con.execute(
            "SELECT content FROM chunks WHERE doc_id=? ORDER BY chunk_index ASC;",
            (doc_id,),
        ).fetchall()

    return "\n\n".join(r[0] for r in rows)

def get_chunks_for_doc(name: str) -> List[Tuple[int, int, str, List[str]]]:
    """
    Return list of:
    (chunk_id, chunk_index, content, tokens_list)

    Since `tokens` are stored as "word word word", we reconstruct the list via split().
    """
    with sqlite3.connect(DB_PATH) as con:
        row = con.execute(
            "SELECT id FROM documents WHERE name=?;",
            (name,),
        ).fetchone()

        if not row:
            return []

        doc_id = int(row[0])
        rows = con.execute(
            "SELECT id, chunk_index, content, tokens FROM chunks WHERE doc_id=? ORDER BY chunk_index ASC;",
            (doc_id,),
        ).fetchall()

    out = []
    for cid, cidx, content, toks_text in rows:
        out.append((int(cid), int(cidx), content, toks_text.split()))
    return out

def get_chunk_text_by_index(doc_name: str, chunk_index: int) -> Optional[str]:
    """Fetch a chunk text by index."""
    chunks = get_chunks_for_doc(doc_name)
    for (_cid, cidx, content, _toks) in chunks:
        if cidx == int(chunk_index):
            return content
    return None

# -------------------------
# Summary cache
# -------------------------

def set_summary(name: str, summary: Optional[str]):
    """Store or clear summary."""
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "UPDATE documents SET summary=? WHERE name=?;",
            (summary, name),
        )

def get_summary(name: str) -> Optional[str]:
    """Get cached summary."""
    with sqlite3.connect(DB_PATH) as con:
        row = con.execute(
            "SELECT summary FROM documents WHERE name=?;",
            (name,),
        ).fetchone()

    if not row:
        return None
    return row[0]

# -------------------------
# Q&A cache
# -------------------------

def hash_question(q: str) -> str:
    qn = (q or "").strip().lower()
    return hashlib.sha256(qn.encode("utf-8")).hexdigest()

def get_cached_answer(doc_name: str, question: str) -> Optional[str]:
    """Return cached Q&A if exists."""
    h = hash_question(question)

    with sqlite3.connect(DB_PATH) as con:
        row = con.execute(
            "SELECT answer FROM qa_cache WHERE doc_name=? AND question_hash=?;",
            (doc_name, h),
        ).fetchone()

    return row[0] if row else None

def set_cached_answer(doc_name: str, question: str, answer: str):
    """Store cached Q&A."""
    h = hash_question(question)
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT OR REPLACE INTO qa_cache(doc_name, question_hash, question, answer, created_at) VALUES (?, ?, ?, ?, ?);",
            (doc_name, h, question, answer, created),
        )
