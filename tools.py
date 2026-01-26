from smolagents import tool
from datetime import datetime

@tool
def get_time() -> str:
    """
    Get the current local time in ISO format.
    """
    return datetime.now().isoformat(timespec="seconds")

@tool
def word_count(text: str) -> int:
    """
    Count the number of words in a text.

    Args:
        text: The text to count words in.
    """
    return len(text.split())
