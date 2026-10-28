from __future__ import annotations

import logging
from typing import Literal, Optional

import streamlit as st
from dotenv import load_dotenv

from doc_agent.agent import build_agent
from doc_agent.errors import user_message_for
from doc_agent.storage import init_db

logger = logging.getLogger(__name__)


def app_setup(*, page_title: str, layout: Literal["centered", "wide"] = "centered") -> None:
    st.set_page_config(page_title=page_title, layout=layout)
    load_dotenv()
    init_db()


@st.cache_resource
def get_agent():
    return build_agent(verbose=0)


def run_agent(prompt: str) -> tuple[Optional[str], Optional[str]]:
    """
    Run the agent without ever surfacing raw exceptions to the user.

    Returns:
        (answer, None) on success, or (None, user_facing_error) on failure.
        Full error details are written to the server log only.
    """
    try:
        return str(get_agent().run(prompt)), None
    except Exception as e:
        logger.exception("Agent run failed")
        return None, user_message_for(e)


def init_ui_state() -> None:
    st.session_state.setdefault("selected_doc", None)
    st.session_state.setdefault("latest_summary", None)
    st.session_state.setdefault("latest_summary_doc", None)
    st.session_state.setdefault("messages_by_doc", {})
