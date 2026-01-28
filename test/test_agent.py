"""
Test the agent with predefined questions.
Run this after test_tools.py succeeds.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from agent import build_agent, MODEL_ID
import time

# Load environment variables
load_dotenv()


def test_agent():
    """Test the agent with various questions"""
    print("\n" + "="*60)
    print("🤖 AGENT TESTS")
    print("="*60)
    print(f"📦 Model: {MODEL_ID}")
    print("="*60 + "\n")
    
    # Build the agent
    print("🚀 Building agent...")
    try:
        agent = build_agent(verbose=1)  # Set to 2 for more details
        print("✅ Agent built successfully!\n")
    except Exception as e:
        print(f"❌ Failed to build agent: {e}")
        return
    
    # Test cases
    test_cases = [
        "What time is it in Europe/Berlin?",
        "What time is it?",
        "Count the words in 'Hello world from Berlin'",
        "What time is it in Tokyo and New York?",
    ]
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"📝 Test {i}/{len(test_cases)}")
        print(f"Question: {question}")
        print('='*60)
        
        start_time = time.time()
        
        try:
            answer = agent.run(question)
            elapsed = time.time() - start_time
            
            print(f"\n✅ Answer (took {elapsed:.1f}s):")
            print(f"   {answer}")
            
        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted by user")
            break
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n❌ Error (after {elapsed:.1f}s):")
            print(f"   {e}")
            
            # Optionally show full traceback
            import traceback
            print("\nFull traceback:")
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ All agent tests completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_agent()