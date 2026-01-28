"""
Test the tools directly without the agent.
This is the fastest way to verify tools work correctly.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import get_time, word_count


def test_get_time():
    """Test the get_time tool with various timezones"""
    print("🧪 Testing get_time tool...")
    print("-" * 60)
    
    timezones = [
        "Europe/Berlin",
        "America/New_York",
        "Asia/Tokyo",
        "UTC",
        "InvalidTimezone"  # Test error handling
    ]
    
    for tz in timezones:
        try:
            if tz == "InvalidTimezone":
                result = get_time(tz)
            else:
                result = get_time(tz)
            print(f"  ✅ {tz:20} -> {result}")
        except Exception as e:
            print(f"  ❌ {tz:20} -> Error: {e}")
    
    # Test default (no argument)
    print(f"  ✅ {'Default (UTC)':20} -> {get_time()}")
    print()


def test_word_count():
    """Test the word_count tool with various inputs"""
    print("🧪 Testing word_count tool...")
    print("-" * 60)
    
    test_cases = [
        ("Hello world", 2),
        ("The quick brown fox jumps", 5),
        ("one", 1),
        ("", 0),
        ("  spaces   everywhere  ", 2),
        ("Hello world from Berlin!", 4),
    ]
    
    for text, expected in test_cases:
        result = word_count(text)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{text:30}' -> {result} (expected {expected})")
    print()


def main():
    """Run all tool tests"""
    print("\n" + "="*60)
    print("🧪 TOOL TESTS")
    print("="*60 + "\n")
    
    test_get_time()
    test_word_count()
    
    print("="*60)
    print("✅ All tool tests completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()