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
import json

DB_PATH = os.getenv("DOC_AGENT_DB", "doc_agent.db")

# -------------------------
# Tokenization + chunking
# -------------------------

_WORD_RE = re.compile(r"[A-Za-z0-9_]+", re.UNICODE)

def tokenize(text: str) -> List[str]:
    """
    Tokenize text into lowercase word tokens for BM25.

    Args:
        text: Input text to tokenize.

    Returns:
        A list of lowercase tokens.
    """
    return [t.lower() for t in _WORD_RE.findall(text or "")]

def chunk_text(text: str, max_chars: int = 2200, overlap: int = 250) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: The full document text.
        max_chars: Maximum characters per chunk.
        overlap: Number of characters to overlap between chunks.

    Returns:
        List of chunk strings.
    """
    text = (text or "").strip()
    if not text:
        return []

    chunks: List[str] = []
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
    """
    Initialize SQLite database and tables.

    Creates tables:
    - documents
    - chunks
    - qa_cache
    """
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
    """
    Insert a document if it doesn't exist and return its id.

    Args:
        name: Unique document name.
        created_at_iso: ISO timestamp for creation.

    Returns:
        Document id.
    """
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
    """
    List stored documents.

    Returns:
        List of (document_name, created_at).
    """
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute(
            "SELECT name, created_at FROM documents ORDER BY id DESC;"
        ).fetchall()
    return [(r[0], r[1]) for r in rows]

def delete_document(name: str):
    """
    Delete a document and associated chunks and cached answers.

    Args:
        name: Document name to delete.
    """
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

    This function is defensive:
    - ensures chunk content is always a string
    - ensures tokens are always stored as TEXT (string)
    - avoids SQLite binding errors if chunks accidentally contain dicts/lists
    """
    with sqlite3.connect(DB_PATH) as con:
        con.execute("DELETE FROM chunks WHERE doc_id=?;", (doc_id,))

        for idx, ch in enumerate(chunks):
            # 1) Ensure chunk content is a string
            if isinstance(ch, dict):
                # Common pattern: {"content": "...", ...}
                ch_text = ch.get("content") or ch.get("text") or json.dumps(ch, ensure_ascii=False)
            elif isinstance(ch, list):
                ch_text = " ".join(str(x) for x in ch)
            else:
                ch_text = str(ch)

            # 2) Tokenize and ensure tokens are stored as TEXT
            toks = tokenize(ch_text)
            if isinstance(toks, dict):
                # Very unexpected, but handle it anyway
                toks_text = json.dumps(toks, ensure_ascii=False)
            elif isinstance(toks, list):
                toks_text = " ".join(str(t) for t in toks)
            else:
                toks_text = str(toks)

            con.execute(
                "INSERT INTO chunks(doc_id, chunk_index, content, tokens) VALUES (?, ?, ?, ?);",
                (doc_id, idx, ch_text, toks_text),
            )


# -------------------------
# Document retrieval
# -------------------------

def get_document_text(name: str) -> Optional[str]:
    """
    Get the full text of a stored document.

    Args:
        name: Document name.

    Returns:
        Full document text, or None if not found.
    """
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
    Get chunks for a document.

    Args:
        name: Document name.

    Returns:
        List of tuples:
        (chunk_id, chunk_index, content, tokens_list)
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

    out: List[Tuple[int, int, str, List[str]]] = []
    for cid, cidx, content, toks_text in rows:
        out.append((int(cid), int(cidx), content, (toks_text or "").split()))
    return out

def get_chunk_text_by_index(doc_name: str, chunk_index: int) -> Optional[str]:
    """
    Fetch a chunk text by its index within a document.

    Args:
        doc_name: Document name.
        chunk_index: Index of the chunk.

    Returns:
        Chunk text if found, otherwise None.
    """
    chunks = get_chunks_for_doc(doc_name)
    for (_cid, cidx, content, _toks) in chunks:
        if cidx == int(chunk_index):
            return content
    return None

# -------------------------
# Summary cache
# -------------------------

def set_summary(name: str, summary: Optional[str]):
    """
    Store or clear the cached summary.

    Args:
        name: Document name.
        summary: Summary text to store, or None to clear.
    """
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "UPDATE documents SET summary=? WHERE name=?;",
            (summary, name),
        )

def get_summary(name: str) -> Optional[str]:
    """
    Get cached summary.

    Args:
        name: Document name.

    Returns:
        Summary text if present, otherwise None.
    """
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
    """
    Hash a question to create a stable cache key.

    Args:
        q: Question text.

    Returns:
        SHA-256 hex digest.
    """
    qn = (q or "").strip().lower()
    return hashlib.sha256(qn.encode("utf-8")).hexdigest()

def get_cached_answer(doc_name: str, question: str) -> Optional[str]:
    """
    Return cached Q&A answer if it exists.

    Args:
        doc_name: Document name.
        question: User question.

    Returns:
        Cached answer if found, otherwise None.
    """
    h = hash_question(question)

    with sqlite3.connect(DB_PATH) as con:
        row = con.execute(
            "SELECT answer FROM qa_cache WHERE doc_name=? AND question_hash=?;",
            (doc_name, h),
        ).fetchone()

    return row[0] if row else None

def set_cached_answer(doc_name: str, question: str, answer: str):
    """
    Store cached Q&A answer.

    Args:
        doc_name: Document name.
        question: User question.
        answer: Agent answer to cache.
    """
    h = hash_question(question)
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT OR REPLACE INTO qa_cache(doc_name, question_hash, question, answer, created_at) "
            "VALUES (?, ?, ?, ?, ?);",
            (doc_name, h, question, answer, created),
        )

