from __future__ import annotations

from typing import Optional

GENERIC_MESSAGE = "Something went wrong while generating a response. Please try again in a moment."

# Messages shown to app users. They deliberately avoid provider names,
# URLs, request IDs, and billing details from the underlying exception.
_MESSAGES_BY_STATUS = {
    401: "The assistant is not configured correctly right now. Please try again later.",
    402: "The assistant is temporarily unavailable. Please try again later.",
    403: "The assistant is not configured correctly right now. Please try again later.",
    404: "The assistant is temporarily unavailable. Please try again later.",
    429: "The assistant is receiving too many requests. Please wait a minute and try again.",
    503: "The assistant is starting up or overloaded. Please try again in a minute.",
}


def _status_code(exc: BaseException) -> Optional[int]:
    """Find an HTTP status code anywhere in the exception's cause chain."""
    seen = set()
    cur: Optional[BaseException] = exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        response = getattr(cur, "response", None)
        code = getattr(response, "status_code", None)
        if isinstance(code, int):
            return code
        cur = cur.__cause__ or cur.__context__
    return None


def _is_timeout(exc: BaseException) -> bool:
    cur: Optional[BaseException] = exc
    seen = set()
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        if isinstance(cur, TimeoutError) or "timeout" in type(cur).__name__.lower():
            return True
        cur = cur.__cause__ or cur.__context__
    return False


def user_message_for(exc: BaseException) -> str:
    """
    Map an exception raised while running the agent to a safe, user-facing message.

    Args:
        exc: The exception raised by agent construction or agent.run().

    Returns:
        A short message suitable for showing to end users.
    """
    if isinstance(exc, RuntimeError) and "token" in str(exc).lower():
        return _MESSAGES_BY_STATUS[401]

    code = _status_code(exc)
    if code in _MESSAGES_BY_STATUS:
        return _MESSAGES_BY_STATUS[code]
    if code is not None and code >= 500:
        return _MESSAGES_BY_STATUS[503]
    if _is_timeout(exc):
        return "The assistant took too long to respond. Please try again."
    return GENERIC_MESSAGE
