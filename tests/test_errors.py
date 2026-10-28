from types import SimpleNamespace

from doc_agent.errors import GENERIC_MESSAGE, user_message_for


class FakeHTTPError(Exception):
    def __init__(self, status_code: int, message: str = ""):
        super().__init__(message)
        self.response = SimpleNamespace(status_code=status_code)


def _wrapped(inner: Exception) -> Exception:
    """Mimic smolagents raising AgentGenerationError(...) from the HTTP error."""
    try:
        try:
            raise inner
        except Exception as e:
            raise RuntimeError(f"Error in generating model output:\n{e}") from e
    except RuntimeError as outer:
        return outer


def test_payment_required_hides_provider_details():
    exc = _wrapped(FakeHTTPError(402, "402 Payment Required for url: https://router.huggingface.co/..."))
    msg = user_message_for(exc)
    assert "temporarily unavailable" in msg
    assert "huggingface" not in msg.lower()
    assert "credit" not in msg.lower()
    assert "402" not in msg


def test_rate_limit_message():
    assert "too many requests" in user_message_for(_wrapped(FakeHTTPError(429)))


def test_unknown_server_error_maps_to_overloaded():
    assert "overloaded" in user_message_for(_wrapped(FakeHTTPError(500)))


def test_missing_token_message():
    msg = user_message_for(RuntimeError("Missing Hugging Face token (HF_TOKEN)."))
    assert "not configured" in msg
    assert "HF_TOKEN" not in msg


def test_timeout_message():
    assert "too long" in user_message_for(_wrapped(TimeoutError("read timed out")))


def test_unknown_error_is_generic():
    assert user_message_for(ValueError("secret internals")) == GENERIC_MESSAGE
