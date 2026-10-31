from smolagents import ChatMessage, MessageRole, Model

# A summary has a fixed input (the whole document), so it needs one model call,
# not an agent deciding which steps to take.

# Keeps the prompt plus the answer well inside the 16k-token context Ollama is
# configured with (roughly 4 characters per token).
MAX_SUMMARY_INPUT_CHARS = 24_000

SUMMARY_PROMPT = (
    "Summarize the following document in one short paragraph, followed by 3 to 5 "
    "bullet points with its key facts. Use only information from the document.\n\n"
    "Document:\n{text}"
)


def summarize_text(model: Model, text: str) -> str:
    """
    Summarize a document's text with a single model call.

    Raises:
        RuntimeError: if the model returns no summary text.
    """
    if len(text) > MAX_SUMMARY_INPUT_CHARS:
        text = text[:MAX_SUMMARY_INPUT_CHARS] + "\n\n[Document truncated for length.]"

    message = ChatMessage(
        role=MessageRole.USER,
        content=[{"type": "text", "text": SUMMARY_PROMPT.format(text=text)}],
    )
    summary = model.generate([message]).content

    if not isinstance(summary, str) or not summary.strip():
        raise RuntimeError("The model returned an empty summary.")
    return summary.strip()
