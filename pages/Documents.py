import streamlit as st

from ui.common import MODEL_AVAILABLE, MODEL_UNAVAILABLE_MESSAGE, app_setup, init_ui_state, run_agent
from doc_agent.storage import list_documents, delete_document, get_summary, set_summary


def _render_documents_header() -> None:
    h1, h2, h3, h4 = st.columns([3, 2, 1.6, 1.3], vertical_alignment="center")
    h1.write("**Document**")
    h2.write("**Created**")
    h3.write("**Actions**")
    h4.write("")


def _handle_delete(name: str) -> None:
    delete_document(name)
    if st.session_state.selected_doc == name:
        st.session_state.selected_doc = None
    if st.session_state.latest_summary_doc == name:
        st.session_state.latest_summary = None
        st.session_state.latest_summary_doc = None
    st.rerun()


def _get_summary(name: str) -> tuple[str | None, str | None]:
    cached = get_summary(name)
    if cached:
        # Served from the database, so this works even while the model is down.
        return cached, None

    summary, error = run_agent(f"Summarize the document named '{name}'.")
    if summary is not None and not get_summary(name):
        # The agent is asked to call save_summary itself, but may skip it.
        set_summary(name, summary)
    return summary, error


def _render_document_row(name: str, created: str) -> None:
    c1, c2, c3, c4 = st.columns([3, 2, 1.6, 1.3], vertical_alignment="center")

    is_selected = st.session_state.selected_doc == name
    label = f"• {name}" if is_selected else name

    if c1.button(label, key=f"select_{name}"):
        st.session_state.selected_doc = name

    c2.write(created)

    # Cached summaries need no model, so Summarize stays enabled for them.
    can_summarize = MODEL_AVAILABLE or get_summary(name) is not None
    if c3.button(
        "Summarize",
        key=f"sum_{name}",
        icon=":material/summarize:",
        disabled=not can_summarize,
        help=None if can_summarize else MODEL_UNAVAILABLE_MESSAGE,
    ):
        st.session_state.selected_doc = name
        with st.spinner("Summarizing..."):
            summary, error = _get_summary(name)
        if error:
            st.error(error)
        else:
            st.session_state.latest_summary = summary
            st.session_state.latest_summary_doc = name

    if c4.button("Delete", key=f"del_{name}", icon=":material/delete:"):
        _handle_delete(name)


def _render_summary_section() -> None:
    if st.session_state.latest_summary:
        st.subheader(f"Summary: {st.session_state.latest_summary_doc}")
        st.write(st.session_state.latest_summary)

    if st.session_state.selected_doc:
        st.info(f"Selected document: {st.session_state.selected_doc}")
        if st.button("Open chat", width="stretch"):
            st.switch_page("pages/Chat.py")


def main() -> None:
    app_setup(page_title="Doc Agent | Documents", layout="centered")
    init_ui_state()

    if st.button("Back to Home", icon=":material/home:"):
        st.switch_page("pages/Home.py")

    st.divider()

    st.subheader("Your Documents")
    st.write("Select a document to summarize it or open the chat for deeper questions.")

    docs = list_documents()
    if not docs:
        st.caption("No documents stored yet.")
        return

    _render_documents_header()
    for name, created in docs:
        _render_document_row(name, created)

    st.divider()
    _render_summary_section()


main()
