import re
import streamlit as st

from ui.common import app_setup, init_ui_state, get_agent
from doc_agent.storage import (
    list_documents,
    get_cached_answer,
    set_cached_answer,
    get_chunk_text_by_index,
)


def extract_cited_chunks(answer: str) -> list[int]:
    return sorted(
        {int(x) for x in re.findall(r"\[chunk\s+(\d+)\]", answer, flags=re.IGNORECASE)}
    )


def main() -> None:
    app_setup(page_title="Doc Agent | Chat", layout="centered")
    init_ui_state()
    agent = get_agent()

    st.title("Chat about your document")

    docs = [n for n, _c in list_documents()]
    if not docs:
        st.warning("No documents found. Upload one first.")
        if st.button("Back to Home", icon=":material/home:"):
            st.switch_page("pages/Home.py")
        return

    default_doc = st.session_state.get("selected_doc") or docs[0]
    if default_doc not in docs:
        default_doc = docs[0]

    current_doc = st.selectbox("Document", options=docs, index=docs.index(default_doc))
    st.session_state.selected_doc = current_doc

    messages_by_doc = st.session_state["messages_by_doc"]
    messages_by_doc.setdefault(current_doc, [])
    messages = messages_by_doc[current_doc]

    if st.button("Back to documents", icon=":material/edit_document:"):
        st.switch_page("pages/Documents.py")

    st.divider()

    for m in messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    user_text = st.chat_input(f"Ask about '{current_doc}'...")
    if not user_text:
        return

    messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Thinking...")

        cached = get_cached_answer(current_doc, user_text)
        if cached:
            answer = cached
        else:
            prompt = (
                f"Document name: {current_doc}\n"
                f"User question: {user_text}\n"
                "Answer the question about this document."
            )
            try:
                answer = agent.run(prompt)
            except Exception as e:
                answer = f"Error: {e}"
            set_cached_answer(current_doc, user_text, answer)

        placeholder.markdown(answer)

        cited = extract_cited_chunks(answer)
        if cited:
            with st.expander("Show sources (cited chunks)"):
                for idx in cited:
                    chunk = get_chunk_text_by_index(current_doc, idx)
                    st.markdown(f"**[chunk {idx}]**")
                    st.write(chunk or "(not found)")

    messages.append({"role": "assistant", "content": answer})


main()
