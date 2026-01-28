"""
Run all tests in sequence.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_tools import main as test_tools_main
from test_agent import main as test_agent_main


def main():
    print("\n" + "="*60)
    print("🧪 RUNNING ALL TESTS")
    print("="*60 + "\n")
    
    # Run tool tests
    print("1️⃣  Running tool tests...")
    test_tools_main()
    
    # Run agent tests
    print("\n2️⃣  Running agent tests...")
    test_agent_main()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()