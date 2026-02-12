import io
import streamlit as st
from pypdf import PdfReader

from ui.common import app_setup, init_ui_state
from doc_agent.storage import upsert_document, insert_chunks, chunk_text


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    parts = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(parts).strip()


def extract_text(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()

    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore").strip()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(data)
    return ""


def main() -> None:
    app_setup(page_title="Doc Agent | Upload", layout="centered")
    init_ui_state()

    st.session_state.setdefault("upload_ok", False)
    st.session_state.setdefault("uploaded_doc_name", None)

    if st.button("Back to Home", icon=":material/home:"):
        st.switch_page("pages/Home.py")

    st.divider()

    st.title("Upload a document")
    st.caption(
        "Upload a TXT or PDF to add it to your library. Once stored, you can generate summaries and chat with the document."
    )
    st.caption("Uploading is model-free, while summaries and chat use the model.")

    with st.form("upload_form", clear_on_submit=True):
        uploaded = st.file_uploader("TXT or text based PDF", type=["txt", "pdf"])
        doc_name = st.text_input("Rename document (optional)")
        submitted = st.form_submit_button("Store document")

    if submitted:
        st.session_state.upload_ok = False
        st.session_state.uploaded_doc_name = None

        if uploaded is None:
            st.error("Please choose a file.")
        else:
            inferred_name = doc_name.strip() or uploaded.name.rsplit(".", 1)[0]
            text = extract_text(uploaded)

            if not text or len(text) < 50:
                st.error(
                    "Could not extract meaningful text. Scanned PDFs need OCR, which is not enabled here."
                )
            else:
                doc_id = upsert_document(inferred_name, created_at_iso="stored_via_app")
                chunks = chunk_text(text)
                insert_chunks(doc_id, chunks)

                st.session_state.upload_ok = True
                st.session_state.uploaded_doc_name = inferred_name

                st.session_state.selected_doc = inferred_name
                st.session_state.latest_summary = None
                st.session_state.latest_summary_doc = None

    if st.session_state.upload_ok:
        st.success(
            f"Stored '{st.session_state.uploaded_doc_name}' successfully. You can view it in your documents list."
        )

        if st.button("Go to your documents", use_container_width=True):
            st.switch_page("pages/Documents.py")


main()
