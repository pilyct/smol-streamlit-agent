from datetime import datetime, timezone
from doc_agent.storage import init_db, upsert_document, insert_chunks, chunk_text, set_summary
from doc_agent.tools import search_documents, get_cached_summary, save_summary

def test_search_documents_returns_chunks_with_citations():
    init_db()
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    doc_id = upsert_document("doc", created)

    text = "Refund policy: refunds allowed within 14 days.\n\nShipping takes 3-5 days."
    chunks = chunk_text(text, max_chars=60, overlap=5)
    insert_chunks(doc_id, chunks)

    res = search_documents("doc", "refunds")
    assert "[chunk" in res.lower()
    assert "refund" in res.lower()

def test_summary_tools():
    init_db()
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    upsert_document("docsum", created)

    assert "No cached summary" in get_cached_summary("docsum")

    msg = save_summary("docsum", "This is a summary.")
    assert "Saved summary" in msg

    assert get_cached_summary("docsum") == "This is a summary."
