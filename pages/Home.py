import streamlit as st
from ui.common import app_setup, init_ui_state


def main() -> None:
    app_setup(page_title="Doc Agent", layout="centered")
    init_ui_state()

    st.title("Doc Agent")
    st.caption(
        "Your document hub. Choose what you want to do: open your existing library, or upload a new document to summarize and chat with."
    )

    col1, col2 = st.columns(2, gap="xsmall")

    with col1:
        with st.container(border=True):
            st.subheader("Browse your documents")
            st.write("View documents you have already uploaded, summarize them, or jump into chat.")
            if st.button("Go to your documents", use_container_width=True, type="secondary"):
                st.switch_page("pages/Documents.py")

    with col2:
        with st.container(border=True):
            st.subheader("Upload a new document")
            st.write("Add a TXT or a text based PDF to your library so you can summarize and chat with it.")
            if st.button("Upload a document", use_container_width=True, type="primary"):
                st.switch_page("pages/Upload.py")


main()
