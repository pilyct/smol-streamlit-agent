from smolagents import tool
from rank_bm25 import BM25Okapi
from doc_agent.storage import get_chunks_for_doc, get_summary, set_summary

MAX_ANSWER_CHUNKS = 5

@tool
def search_documents(name: str, query: str) -> str:
    """
    Search a stored document for relevant excerpts using BM25 ranking.

    Args:
        name: The name of the stored document to search.
        query: The user question or search query.

    Returns:
        The most relevant excerpts with citations in the form:
        [chunk <index>] <excerpt>
    """
    name = (name or "").strip()
    query = (query or "").strip()

    if not name:
        return "Document name is required."
    if not query:
        return "Query is empty."

    chunks = get_chunks_for_doc(name)
    if not chunks:
        return f"No chunks found for '{name}'."

    corpus_tokens = [toks for (_cid, _idx, _content, toks) in chunks]
    bm25 = BM25Okapi(corpus_tokens)
    scores = bm25.get_scores(query.lower().split())

    ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)[:MAX_ANSWER_CHUNKS]

    out = []
    for (_cid, cidx, content, _toks), score in ranked:
        excerpt = content[:700].replace("\n", " ").strip()
        out.append(f"[chunk {cidx}] {excerpt}")

    return "\n".join(out)

@tool
def get_cached_summary(name: str) -> str:
    """
    Retrieve the cached summary for a document, if one exists.

    Args:
        name: The name of the stored document.

    Returns:
        The cached summary text if available, otherwise a message indicating
        no summary is cached.
    """
    name = (name or "").strip()
    if not name:
        return "Document name is required."
    s = get_summary(name)
    return s if s else "No cached summary found."

@tool
def save_summary(name: str, summary: str) -> str:
    """
    Save a summary for a document in the cache.

    Args:
        name: The name of the stored document.
        summary: The summary text to store.

    Returns:
        A confirmation message indicating the summary was saved.
    """
    name = (name or "").strip()
    summary = (summary or "").strip()
    if not name or not summary:
        return "Name and summary are required."
    set_summary(name, summary)
    return f"Saved summary for '{name}'."
