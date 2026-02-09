import os
from smolagents import CodeAgent, InferenceClientModel
from doc_agent.tools import search_documents, get_cached_summary, save_summary

MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen2.5-7B-Instruct")

def build_agent(verbose: int = 0):
    token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("Missing Hugging Face token (HUGGINGFACEHUB_API_TOKEN or HF_TOKEN).")

    model = InferenceClientModel(
        model_id=MODEL_ID,
        token=token,
        temperature=0.2,
        max_tokens=700,   # keep modest for free tier
        timeout=60,
    )

    agent = CodeAgent(
        tools=[search_documents, get_cached_summary, save_summary],
        model=model,
        add_base_tools=False,
        max_steps=4,
    )

    agent.verbose = int(verbose)

    try:
        agent.system_prompt = (
            "You are a document assistant. Be concise.\n"
            "For Q&A:\n"
            "- ALWAYS call search_documents(name, query) first.\n"
            "- Answer using only the returned excerpts.\n"
            "- Include citations in the form [chunk N] in the final answer.\n"
            "- If evidence is missing, say you cannot find it.\n"
            "For summaries:\n"
            "- Call get_cached_summary(name) first.\n"
            "- If missing, create a concise summary and then call save_summary(name, summary).\n"
            "Never invent citations."
        )
    except Exception:
        pass

    return agent
