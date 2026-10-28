from __future__ import annotations

import logging
from typing import Literal, Optional

import streamlit as st
from dotenv import load_dotenv

from doc_agent.agent import build_agent
from doc_agent.errors import user_message_for
from doc_agent.storage import init_db

logger = logging.getLogger(__name__)

# The model is currently unavailable (no inference credits). While this is
# False, every page shows a banner and nothing in the app calls the model.
# Set it back to True once a working model is configured.
MODEL_AVAILABLE = False
MODEL_UNAVAILABLE_MESSAGE = "The AI model is temporarily unavailable while we upgrade it."


def app_setup(*, page_title: str, layout: Literal["centered", "wide"] = "centered") -> None:
    st.set_page_config(page_title=page_title, layout=layout)
    load_dotenv()
    init_db()
    if not MODEL_AVAILABLE:
        st.info(
            f"**{MODEL_UNAVAILABLE_MESSAGE}** In the meantime, chatting and creating new "
            "summaries are switched off. You can still upload and browse documents and view "
            "existing summaries.",
            icon=":material/construction:",
        )


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
    if not MODEL_AVAILABLE:
        return None, MODEL_UNAVAILABLE_MESSAGE
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
