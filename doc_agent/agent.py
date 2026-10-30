import os
from smolagents import CodeAgent, OpenAIModel
from doc_agent.tools import search_documents, get_cached_summary, save_summary

# Any OpenAI-compatible server works here. Defaults point at a local Ollama;
# switching provider (e.g. Groq) only means changing these env vars.
MODEL_ID = os.getenv("MODEL_ID", "qwen3.8")
MODEL_API_BASE = os.getenv("MODEL_API_BASE", "http://localhost:11434/v1")

# Spelled out step by step: without an explicit way to finish, the model kept
# searching until max_steps and smolagents had to force an extra answer call.
DOC_ASSISTANT_RULES = (
    "You are a document assistant. Be concise.\n"
    "Answer questions about a stored document in exactly this order:\n"
    "1. Call search_documents(name, query) and print the result.\n"
    "2. In the next step, call final_answer(...) with your answer. Use only the printed "
    "excerpts and cite them in the form [chunk N].\n"
    "Every answer ends with its citations, even a one-word answer, with one chunk per "
    'bracket. For example: final_answer("Tuesday [chunk 0]") or '
    'final_answer("Python and R [chunk 0] [chunk 1]").\n'
    "If the excerpts do not answer the question, you may search once more with different "
    "words. If there is still no evidence, call final_answer saying you cannot find it.\n"
    "Always finish with final_answer(...) inside a code block, never with plain text.\n"
    "Never invent citations."
)

def build_model() -> OpenAIModel:
    return OpenAIModel(
        model_id=MODEL_ID,
        api_base=MODEL_API_BASE,
        api_key=os.getenv("MODEL_API_KEY", "ollama"),
        temperature=0.2,
        max_tokens=2000,

        # smolagents retries rate limits (429) up to 3 times, waiting about
        # a minute between attempts, which leaves users stuck on "Thinking...".
        # Fail fast instead and let the UI show a "too many requests" message.  
        retry=False,
    )

def build_agent(verbose: int = 0):
    agent = CodeAgent(
        # Only these 3 first-party tools are exposed; none of them touch the
        # filesystem, network, or a subshell, so there is nothing for
        # generated code to pivot to even though it runs in-process.
        tools=[search_documents, get_cached_summary, save_summary],
        model=build_model(),
        add_base_tools=False,
        max_steps=4,
        # Explicitly pin the sandbox to no extra imports (no requests, os,
        # subprocess, socket, ...) on top of smolagents' own minimal default.
        # This is a known-incomplete area of smolagents' local code executor
        # (CVE-2025-9959 / GHSA-jxgv-6j54-wwc7); keeping this empty removes
        # the specific SSRF/injection vectors those advisories describe.
        additional_authorized_imports=[],
        # Cap captured print() output so a runaway loop can't exhaust memory
        # via stdout buffering.
        max_print_outputs_length=8000,
        verbosity_level=int(verbose),
    )

    # system_prompt is read-only in smolagents; append to the template instead
    # of replacing it, since the default one teaches the model the code format.
    agent.prompt_templates["system_prompt"] += "\n\n" + DOC_ASSISTANT_RULES

    return agent
