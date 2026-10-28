from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ui import common
from ui.common import MODEL_UNAVAILABLE_MESSAGE

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["Home", "Upload", "Documents", "Chat"]


def _page(name: str) -> AppTest:
    at = AppTest.from_file(str(ROOT / "pages" / f"{name}.py"), default_timeout=30)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def _has_banner(at: AppTest) -> bool:
    return any(MODEL_UNAVAILABLE_MESSAGE in i.value for i in at.info)


@pytest.fixture(autouse=True)
def docs():
    """Store one document with a cached summary and one without. No model calls."""
    from doc_agent import storage

    storage.insert_chunks(storage.upsert_document("with_summary", "t"), storage.chunk_text("alpha beta " * 50))
    storage.set_summary("with_summary", "A cached summary.")
    storage.insert_chunks(storage.upsert_document("no_summary", "t"), storage.chunk_text("gamma delta " * 50))


@pytest.fixture
def model_unavailable(monkeypatch):
    monkeypatch.setattr(common, "MODEL_AVAILABLE", False)


@pytest.fixture
def model_available(monkeypatch):
    monkeypatch.setattr(common, "MODEL_AVAILABLE", True)


@pytest.mark.parametrize("name", PAGES)
def test_banner_on_every_page(model_unavailable, name):
    assert _has_banner(_page(name))


def test_chat_input_disabled(model_unavailable):
    chat_input = _page("Chat").chat_input[0]
    assert chat_input.disabled
    assert chat_input.placeholder == MODEL_UNAVAILABLE_MESSAGE


def test_summarize_disabled_only_without_cached_summary(model_unavailable):
    at = _page("Documents")
    assert at.button(key="sum_no_summary").disabled

    cached = at.button(key="sum_with_summary")
    assert not cached.disabled
    cached.click().run()
    assert any("A cached summary." in m.value for m in at.markdown)


@pytest.mark.parametrize("name", PAGES)
def test_no_banner_when_model_available(model_available, name):
    assert not _has_banner(_page(name))


def test_ai_controls_enabled_when_model_available(model_available):
    assert not _page("Chat").chat_input[0].disabled
    assert not _page("Documents").button(key="sum_no_summary").disabled
