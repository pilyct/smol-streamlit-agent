import streamlit as st

from ui.common import app_setup, init_ui_state, get_agent
from doc_agent.storage import list_documents, delete_document


def main() -> None:
    app_setup(page_title="Doc Agent | Documents", layout="centered")
    init_ui_state()
    agent = get_agent()

    if st.button("Back to Home", use_container_width=False, icon=":material/home:"):
        st.switch_page("pages/Home.py")

    st.divider()

    st.subheader("Your Documents")
    st.write("Select a document to summarize it or open the chat for deeper questions.")

    docs = list_documents()
    if not docs:
        st.caption("No documents stored yet.")
        return

    h1, h2, h3, h4 = st.columns([3, 2, 1.6, 1.3], vertical_alignment="center")
    h1.write("**Document**")
    h2.write("**Created**")
    h3.write("**Actions**")
    h4.write("")

    for name, created in docs:
        c1, c2, c3, c4 = st.columns([3, 2, 1.6, 1.3], vertical_alignment="center")

        is_selected = st.session_state.selected_doc == name
        label = f"• {name}" if is_selected else name

        if c1.button(label, key=f"select_{name}"):
            st.session_state.selected_doc = name

        c2.write(created)

        if c3.button("Summarize", key=f"sum_{name}", icon=":material/summarize:"):
            st.session_state.selected_doc = name
            summary = agent.run(f"Summarize the document named '{name}'.")
            st.session_state.latest_summary = summary
            st.session_state.latest_summary_doc = name

        if c4.button("Delete", key=f"del_{name}", icon=":material/delete:"):
            delete_document(name)
            if st.session_state.selected_doc == name:
                st.session_state.selected_doc = None
            if st.session_state.latest_summary_doc == name:
                st.session_state.latest_summary = None
                st.session_state.latest_summary_doc = None
            st.rerun()

    st.divider()

    if st.session_state.latest_summary:
        st.subheader(f"Summary: {st.session_state.latest_summary_doc}")
        st.write(st.session_state.latest_summary)

    if st.session_state.selected_doc:
        st.info(f"Selected document: {st.session_state.selected_doc}")
        if st.button("Open chat", use_container_width=True):
            st.switch_page("pages/Chat.py")


main()
