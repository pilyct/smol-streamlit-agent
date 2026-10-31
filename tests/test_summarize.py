import pytest
from smolagents import ChatMessage, MessageRole, Model

from doc_agent.summarize import MAX_SUMMARY_INPUT_CHARS, summarize_text


class FakeModel(Model):
    """Stands in for the LLM: records the prompt and returns a fixed reply."""

    def __init__(self, reply):
        super().__init__()
        self.reply = reply
        self.calls = []

    def generate(self, messages, stop_sequences=None, response_format=None, tools_to_call_from=None, **kwargs):
        self.calls.append(messages)
        return ChatMessage(role=MessageRole.ASSISTANT, content=self.reply)


def _prompt(model: FakeModel) -> str:
    return model.calls[0][0].content[0]["text"]


def test_summary_is_a_single_model_call():
    model = FakeModel("  A short summary.  ")

    assert summarize_text(model, "Some document text.") == "A short summary."
    assert len(model.calls) == 1
    assert "Some document text." in _prompt(model)


def test_long_documents_are_truncated():
    model = FakeModel("Summary.")

    summarize_text(model, "x" * (MAX_SUMMARY_INPUT_CHARS + 500))

    prompt = _prompt(model)
    assert "x" * (MAX_SUMMARY_INPUT_CHARS + 1) not in prompt
    assert "[Document truncated for length.]" in prompt


@pytest.mark.parametrize("reply", ["", "   ", None])
def test_empty_reply_raises(reply):
    model = FakeModel(reply)

    with pytest.raises(RuntimeError):
        summarize_text(model, "Some document text.")
