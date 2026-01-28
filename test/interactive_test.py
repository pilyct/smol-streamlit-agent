"""
Interactive terminal interface for testing the agent.
This is what you requested - a prompt from terminal!
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from agent import build_agent, MODEL_ID
import sys
import time

# Load environment variables
load_dotenv()


def print_header():
    """Print a nice header"""
    print("\n" + "="*60)
    print("🤖 INTERACTIVE AGENT TEST")
    print("="*60)
    print(f"📦 Model: {MODEL_ID}")
    print("💡 Type your questions and press Enter")
    print("⌨️  Commands: 'quit', 'exit', 'q' to exit")
    print("="*60 + "\n")


def main():
    """Run interactive agent session"""
    print_header()
    
    # Build the agent
    print("🚀 Building agent (this may take a moment)...")
    try:
        agent = build_agent(verbose=1)  # Change to 2 for detailed logs
        print("✅ Agent ready! Start asking questions.\n")
    except Exception as e:
        print(f"❌ Failed to build agent: {e}")
        print("\n💡 Make sure you have:")
        print("   1. Created a .env file with HUGGINGFACEHUB_API_TOKEN")
        print("   2. Installed all requirements: pip install -r requirements.txt")
        sys.exit(1)
    
    # Suggest some example questions
    print("💭 Example questions:")
    print("   • What time is it in Europe/Berlin?")
    print("   • Count the words in 'Hello world from Berlin'")
    print("   • What time is it in Tokyo?")
    print()
    
    # Main interaction loop
    while True:
        try:
            # Get user input
            question = input("You: ").strip()
            
            # Check for exit commands
            if question.lower() in ['quit', 'exit', 'q', 'bye']:
                print("\n👋 Goodbye! Thanks for testing the agent.")
                break
            
            # Skip empty input
            if not question:
                continue
            
            # Show thinking indicator
            print("\n🤔 Agent thinking...", end="", flush=True)
            start_time = time.time()
            
            # Run the agent
            try:
                answer = agent.run(question)
                elapsed = time.time() - start_time
                
                # Clear the "thinking" message and show answer
                print(f"\r{'':50}\r", end="")  # Clear line
                print(f"🤖 Agent (took {elapsed:.1f}s): {answer}\n")
                
            except KeyboardInterrupt:
                print("\n⚠️  Interrupted! Type 'quit' to exit or ask another question.")
                continue
                
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"\r{'':50}\r", end="")  # Clear line
                print(f"❌ Error (after {elapsed:.1f}s): {e}\n")
                
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        
        except EOFError:
            print("\n\n👋 EOF detected. Goodbye!")
            break


if __name__ == "__main__":
    main()