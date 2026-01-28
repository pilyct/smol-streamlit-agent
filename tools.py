"""
Custom tools for the agent.
"""
from smolagents import tool
from datetime import datetime
import pytz


@tool
def get_time(timezone: str = "UTC") -> str:
    """
    Get the current time in a specific timezone.
    
    Args:
        timezone: The timezone name (e.g., 'Europe/Berlin', 'America/New_York', 'UTC', 'Asia/Tokyo')
    
    Returns:
        Current time in ISO format for the specified timezone
    
    Examples:
        get_time("Europe/Berlin") -> "2024-01-28T15:30:45+01:00"
        get_time() -> "2024-01-28T14:30:45+00:00" (UTC)
    """
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        return current_time.isoformat(timespec="seconds")
    except pytz.exceptions.UnknownTimeZoneError:
        # Fallback to UTC if timezone is invalid
        return f"Invalid timezone '{timezone}'. Using UTC: {datetime.now(pytz.UTC).isoformat(timespec='seconds')}"
    except Exception as e:
        return f"Error getting time: {str(e)}"


@tool
def word_count(text: str) -> int:
    """
    Count the number of words in a text.
    
    Args:
        text: The text to count words in
    
    Returns:
        Number of words in the text
    
    Examples:
        word_count("Hello world") -> 2
        word_count("The quick brown fox") -> 4
    """
    if not text or not text.strip():
        return 0
    return len(text.split())