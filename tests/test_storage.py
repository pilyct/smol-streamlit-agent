from datetime import datetime, timezone
from doc_agent.storage import (
    init_db, upsert_document, insert_chunks, chunk_text,
    list_documents, get_chunks_for_doc, get_document_text,
    set_summary, get_summary,
    set_cached_answer, get_cached_answer,
    delete_document
)

def test_storage_roundtrip_document_and_chunks():
    init_db()
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    doc_id = upsert_document("profile", created)

    text = "Hello world.\n\nThis is a test document.\nIt has multiple lines."
    chunks = chunk_text(text, max_chars=40, overlap=5)
    assert len(chunks) >= 1

    insert_chunks(doc_id, chunks)

    docs = list_documents()
    assert any(name == "profile" for name, _ in docs)

    stored = get_document_text("profile")
    assert stored is not None
    assert "Hello world" in stored

    ch = get_chunks_for_doc("profile")
    assert len(ch) == len(chunks)
    # tokens_list is list[str]
    assert isinstance(ch[0][3], list)

def test_summary_cache():
    init_db()
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    upsert_document("doc1", created)

    assert get_summary("doc1") is None
    set_summary("doc1", "short summary")
    assert get_summary("doc1") == "short summary"

def test_qa_cache():
    init_db()
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    upsert_document("doc2", created)

    q = "What is important?"
    assert get_cached_answer("doc2", q) is None
    set_cached_answer("doc2", q, "Answer A")
    assert get_cached_answer("doc2", q) == "Answer A"

def test_delete_document_cleans_up():
    init_db()
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    doc_id = upsert_document("todelete", created)
    insert_chunks(doc_id, ["chunk one", "chunk two"])
    set_summary("todelete", "summary")
    set_cached_answer("todelete", "q", "a")

    delete_document("todelete")

    assert get_document_text("todelete") is None
    assert get_summary("todelete") is None
    assert get_cached_answer("todelete", "q") is None
