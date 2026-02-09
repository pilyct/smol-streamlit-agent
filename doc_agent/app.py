import io
import re
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader

from doc_agent.agent import build_agent
from doc_agent.storage import (
    init_db, upsert_document, insert_chunks, chunk_text,
    list_documents, delete_document,
    get_cached_answer, set_cached_answer,
    get_chunk_text_by_index,
)

load_dotenv()
init_db()

st.set_page_config(page_title="Doc Agent", layout="centered")
st.title("Document Summarizer with Memory")
st.caption("Model is only used for Summarize and Q&A. List/Delete/Store are model-free.")

@st.cache_resource
def get_agent():
    return build_agent(verbose=0)

agent = get_agent()

# -----------------------
# PDF / TXT extraction
# -----------------------
def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()

def extract_text(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore").strip()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(data)
    return ""

# -----------------------
# UI: Document controls
# -----------------------
with st.sidebar:
    st.subheader("Documents")

    docs = list_documents()
    doc_names = [n for n, _created in docs]

    selected_doc = st.selectbox(
        "Current document",
        options=["(none)"] + doc_names,
        index=0 if not doc_names else 1,
    )
    current_doc = None if selected_doc == "(none)" else selected_doc

    st.divider()

    st.subheader("Upload & store (no model call)")
    uploaded = st.file_uploader("TXT or text-based PDF", type=["txt", "pdf"])
    doc_name = st.text_input("Document name (optional)", value="")

    if uploaded is not None:
        inferred_name = doc_name.strip() or uploaded.name.rsplit(".", 1)[0]
        if st.button("Store document"):
            text = extract_text(uploaded)
            if not text or len(text) < 50:
                st.error("Could not extract meaningful text. If this PDF is scanned, OCR is not supported in this starter.")
            else:
                # Store without model
                doc_id = upsert_document(inferred_name, created_at_iso="stored_via_app")
                chunks = chunk_text(text)
                insert_chunks(doc_id, chunks)
                st.success(f"Stored '{inferred_name}' with {len(chunks)} chunks.")

    st.divider()

    st.subheader("List (no model call)")
    if st.button("Refresh list"):
        st.rerun()

    if docs:
        st.write("Stored documents:")
        for name, created in docs:
            st.write(f"- {name} ({created})")
    else:
        st.caption("No documents stored yet.")

    st.divider()

    st.subheader("Delete (no model call)")
    if current_doc:
        if st.button(f"Delete '{current_doc}'"):
            delete_document(current_doc)
            st.success(f"Deleted '{current_doc}'.")
            st.rerun()
    else:
        st.caption("Select a document to delete.")

    st.divider()

    st.subheader("Summarize (uses model once, then cached)")
    if current_doc:
        if st.button(f"Summarize '{current_doc}'"):
            # Model call, but summary will be cached by the agent tool save_summary
            summary = agent.run(f"Summarize the document named '{current_doc}'.")
            st.success("Summary ready.")
            st.write(summary)
    else:
        st.caption("Select a document to summarize.")

# -----------------------
# Chat
# -----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

user_text = st.chat_input("Ask about the selected document…")

def extract_cited_chunks(answer: str) -> list[int]:
    return sorted(set(int(x) for x in re.findall(r"\[chunk\s+(\d+)\]", answer, flags=re.IGNORECASE)))

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Thinking...")

        if not current_doc:
            answer = "Select a document in the sidebar first."
            placeholder.markdown(answer)
        else:
            # Q&A cache: zero model call if repeated question
            cached = get_cached_answer(current_doc, user_text)
            if cached:
                answer = cached
                placeholder.markdown(answer)
            else:
                # Model call: force doc context to remove ambiguity
                prompt = (
                    f"Document name: {current_doc}\n"
                    f"User question: {user_text}\n"
                    f"Answer the question about this document."
                )
                try:
                    answer = agent.run(prompt)
                except Exception as e:
                    answer = f"Error: {e}"

                # Cache the answer
                set_cached_answer(current_doc, user_text, answer)
                placeholder.markdown(answer)

        # Show citations (no model call)
        cited = extract_cited_chunks(answer)
        if current_doc and cited:
            with st.expander("Show sources (cited chunks)"):
                for idx in cited:
                    chunk_text_val = get_chunk_text_by_index(current_doc, idx)
                    if chunk_text_val:
                        st.markdown(f"**[chunk {idx}]**")
                        st.write(chunk_text_val)
                    else:
                        st.markdown(f"**[chunk {idx}]** (not found)")

    st.session_state.messages.append({"role": "assistant", "content": answer})
