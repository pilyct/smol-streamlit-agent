from __future__ import annotations

import logging
import os
from typing import Literal, Optional

import streamlit as st
from dotenv import load_dotenv

# Load .env before importing doc_agent: its modules read settings such as
# MODEL_ID at import time. Existing environment variables win, so values set
# by the host (e.g. Streamlit secrets) are never overridden.
load_dotenv()

from doc_agent.agent import build_agent, build_model  # noqa: E402
from doc_agent.errors import user_message_for  # noqa: E402
from doc_agent.storage import get_document_text, init_db  # noqa: E402
from doc_agent.summarize import summarize_text  # noqa: E402

logger = logging.getLogger(__name__)


def ai_enabled_from_env() -> bool:
    """
    Read the AI_ENABLED setting: "true", "1", "yes" or "on" turn the AI features on.

    Anything else, including an unset variable, keeps them off, so a deployment
    without a model shows the banner instead of failing on every question.
    """
    return os.getenv("AI_ENABLED", "").strip().lower() in {"true", "1", "yes", "on"}


# Switch for the AI features, set per environment with AI_ENABLED (.env
# locally, Streamlit secrets when deployed). While this is False, every page
# shows a banner and nothing in the app calls the model.
MODEL_AVAILABLE = ai_enabled_from_env()
MODEL_UNAVAILABLE_MESSAGE = "The AI model is temporarily unavailable while we upgrade it."


def app_setup(*, page_title: str, layout: Literal["centered", "wide"] = "centered") -> None:
    st.set_page_config(page_title=page_title, layout=layout)
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


@st.cache_resource
def get_model():
    return build_model()


def run_summary(name: str) -> tuple[Optional[str], Optional[str]]:
    """
    Summarize a stored document with one model call (no agent), without ever
    surfacing raw exceptions to the user.

    Returns:
        (summary, None) on success, or (None, user_facing_error) on failure.
    """
    if not MODEL_AVAILABLE:
        return None, MODEL_UNAVAILABLE_MESSAGE
    text = get_document_text(name)
    if not text:
        return None, "This document has no text to summarize."
    try:
        return summarize_text(get_model(), text), None
    except Exception as e:
        logger.exception("Summary failed")
        return None, user_message_for(e)


def init_ui_state() -> None:
    st.session_state.setdefault("selected_doc", None)
    st.session_state.setdefault("latest_summary", None)
    st.session_state.setdefault("latest_summary_doc", None)
    st.session_state.setdefault("messages_by_doc", {})
