"""
Agent configuration and initialization.
"""
import os
from smolagents import CodeAgent, InferenceClientModel
from tools import get_time, word_count

# Using the free 7B model - best balance of speed and capability
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

def build_agent(verbose: int = 1):
    """
    Build and return a configured agent.
    
    Args:
        verbose: Verbosity level (0=silent, 1=basic, 2=detailed)
    
    Returns:
        CodeAgent instance ready to use
    """
    # Get token from environment
    token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")
    
    if not token:
        raise RuntimeError(
            "Missing Hugging Face token!\n"
            "Please set HUGGINGFACEHUB_API_TOKEN in your .env file.\n"
            "Get your token from: https://huggingface.co/settings/tokens"
        )
    
    # Initialize the model
    model = InferenceClientModel(
        model_id=MODEL_ID,
        token=token,
        temperature=0.2,  # Lower temperature for more focused responses
        max_tokens=1500,
        timeout=90,  # 90 second timeout for API calls
    )
    
    # Create the agent (removed verbose parameter)
    agent = CodeAgent(
        tools=[get_time, word_count],
        model=model,
        add_base_tools=False,  # Only use our custom tools
        max_steps=5,  # Prevent infinite reasoning loops
    )
    
    # Set verbosity level on the agent after creation
    agent.verbose = verbose
    
    return agent

if __name__ == "__main__":
    # Quick test when running this file directly
    from dotenv import load_dotenv
    load_dotenv()
    
    print("🔧 Building agent...")
    agent = build_agent(verbose=2)
    print("✅ Agent built successfully!")
    print(f"📦 Model: {MODEL_ID}")
    print(f"🛠️  Tools: {[tool.name for tool in agent.tools]}")