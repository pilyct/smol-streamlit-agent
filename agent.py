import os
from smolagents import CodeAgent, InferenceClientModel

from tools import get_time, word_count

MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.2"

def build_agent():
    token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError(
            "Missing Hugging Face token. Set HUGGINGFACEHUB_API_TOKEN (or HF_TOKEN) in your environment/.env."
        )

    model = InferenceClientModel(
        model_id=MODEL_ID,
        token=token,
        temperature=0.2,
        max_tokens=800,
        # optional: requests_per_minute=30,
    )

    agent = CodeAgent(
        tools=[get_time, word_count],
        model=model,
        add_base_tools=False,
    )
    return agent
