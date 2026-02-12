from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from doc_agent.agent import build_agent
from doc_agent.storage import init_db


def app_setup(*, page_title: str, layout: str = "centered") -> None:
    st.set_page_config(page_title=page_title, layout=layout)
    load_dotenv()
    init_db()


@st.cache_resource
def get_agent():
    return build_agent(verbose=0)


def init_ui_state() -> None:
    st.session_state.setdefault("selected_doc", None)
    st.session_state.setdefault("latest_summary", None)
    st.session_state.setdefault("latest_summary_doc", None)
    st.session_state.setdefault("messages_by_doc", {})
