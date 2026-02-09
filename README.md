# 🤖 SmolAgents + Streamlit Document Memory Agent

A complete end-to-end **document-aware AI agent** built with:

- **smolagents** → reasoning + tool orchestration
- **Hugging Face Inference API** → free hosted LLM
- **Streamlit** → clean interactive web interface
- **SQLite + BM25** → local document memory & retrieval

This project evolves a simple tool-using agent into a **realistic document assistant with persistent memory, caching, and tests**.

The agent runs on:

`Qwen/Qwen2.5-7B-Instruct` (free tier)

and can:

- Store documents locally
- Summarize documents (cached)
- Answer questions using citations
- Retrieve exact source excerpts
- Cache answers to avoid repeated model calls
- Run mostly **model-free** for cost control
- Be fully tested with a local test suite

This is a production-style “AI with memory” architecture you can run locally and extend safely.

---

# 📁 Project Structure

```bash
smol_streamlit_agent/
├── .env                     # Hugging Face token (ignored by git)
├── .gitignore
├── requirements.txt
├── pytest.ini               # Pytest configuration (optional but recommended)
├── README.md
│
├── doc_agent/               # Main package
│   ├── __init__.py
│   ├── app.py               # Streamlit UI
│   ├── agent.py             # Agent configuration (smolagents)
│   ├── tools.py             # Agent tools (search, summary cache)
│   └── storage.py           # SQLite storage + retrieval layer
│
├── tests/                   # Test suite
│   ├── conftest.py          # Test configuration + temp DB
│   ├── test_storage.py      # Storage layer tests
│   ├── test_tools.py        # Tool tests
│   ├── test_agent_smoke.py  # Agent build tests (no model call)
│   └── test_agent_live.py   # Optional live model tests
│
└── doc_agent.db             # Auto-created SQLite database (ignored by git)
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
```

### 2. Install dependencies

```bash
pip install -U pip
pip install -r requirements.txt
```

### 3. Create a Hugging Face token

- Go to Hugging Face → Settings → Access Tokens.
- Create a Fine-grained token with:
  - Inference → Make calls to Inference Providers.
  - Repositories → Read access to public gated repos you can access.

Create an `.env` file and add your token:

```bash
HUGGINGFACEHUB_API_TOKEN=hf_your_token_here
```

## 🌐 Run the App

```bash
streamlit run app.py
```

Open the local URL shown in your terminal (typically http://localhost:8501).

## 🧠 What This Agent Can Do

### 📄 <ins>Upload documents</ins>

Upload `.txt` or text-based PDFs.

Documents are:

- chunked locally
- stored in SQLite
- indexed with BM25 search
- never sent fully to the model

No model call happens during upload.

### 🧾 <ins>Summarize documents</ins>

Click “Summarize”.

- Uses model once
- Summary is cached in DB
- Future calls = zero cost

### 🔎 <ins>Ask questions about documents</ins>

Example prompts:

- “What is important in this document?”
- “Summarize the key obligations”
- “What does it say about refunds?”
- “List risks mentioned”

The agent:

- Searches document locally (BM25)
- Sends only relevant chunks to model
- Answers with citations `[chunk N]`
- Caches the answer for reuse

Repeated question = zero model call.

### 📚 <ins>Source citations</ins>

Every answer includes:

```csharp
[chunk 3]
[chunk 7]
```

You can expand **Show sources** to see exact text used.

This makes answers verifiable and trustworthy.

## 🧪 Testing

The project includes a complete test suite covering storage, tools, and agent setup.

Run all tests:

```bash
pytest # or `pytest -v` (shows each test name and status)
```

Run specific test groups:

```bash
pytest tests/test_storage.py
pytest tests/test_tools.py
pytest tests/test_agent_smoke.py
```

## ⚙️ Cost-Control Architecture

This project is designed to stay **near-zero cost**.

Model is used ONLY for:

- new summaries
- new Q&A queries

Model is NOT used for:

- upload/store
- list docs
- delete docs
- retrieval search
- showing citations
- cached answers

Caching ensures repeated usage costs nothing.

## 🧠 Agent Tools

The agent has a minimal, safe toolset:

`search_documents(name, query)`: Find relevant chunks using BM25.

`get_cached_summary(name)`: Return stored summary if available.

`save_summary(name, summary)`: Store summary after first generation.

Everything else runs locally in Python/SQLite.

## 🔐 Security & Safety

Safe by design:

- No filesystem access outside project
- No shell execution
- No arbitrary web requests
- Local SQLite storage only
- Input size limits
- No hidden model loops
- Deterministic operations first

This makes it safe to deploy publicly with basic auth.

## ⚙️ Configuration

### Change the Model

Edit `agent.py` to use a different model:

```python
# Current model (recommended)
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

# Alternatives (all free):
# MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"      # Faster, less capable
# MODEL_ID = "Qwen/Qwen2.5-14B-Instruct"     # Slower, more capable
# MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"
```

### Add New Tools

Add to `tools.py`:

```python
from smolagents import tool

@tool
def your_new_tool(param: str) -> str:
    """
    Description of what your tool does.

    Args:
        param: Description of the parameter

    Returns:
        Description of what it returns
    """
    # Your implementation
    return result
```

Then register it in `agent.py`:

```python
from tools import get_time, word_count, your_new_tool

agent = CodeAgent(
    tools=[get_time, word_count, your_new_tool],
    # ...
)
```

## 🎓 What This Project Teaches

This is not just a chatbot.

It demonstrates:

- Agent + tools architecture
- Retrieval Augmented Generation (RAG)
- Memory + caching design
- Cost-controlled LLM usage
- Verifiable AI with citations
- Production-safe tool design
