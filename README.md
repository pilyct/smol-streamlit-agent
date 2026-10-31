# 🤖 SmolAgents + Streamlit Document Memory Agent

A **document-aware AI assistant** you can run entirely on your own machine, for free.
Upload documents, ask questions about them and get answers with verifiable `[chunk N]`
citations, or generate summaries.

Built with:

- **smolagents**: agent reasoning and tool orchestration
- **Ollama**: free, local LLM (`qwen3.8` by default) through an OpenAI-compatible API
- **Streamlit**: interactive web interface
- **SQLite + BM25**: local document storage and keyword retrieval

<p align="center">
  <img src="./public/dark-Home.png?raw=true" width="400" height="380">
  <img src="./public/dark-Upload.png?raw=true" width="400" height="380">
  <img src="./public/dark-Documents.png?raw=true" width="400" height="380">
  <img src="./public/dark-Chat.png?raw=true" width="400" height="380">
</p>
<p align="center">
  <img src="./public/light-Home.png?raw=true" width="400" height="380">
  <img src="./public/light-Upload.png?raw=true" width="400" height="380">
  <img src="./public/light-Documents.png?raw=true" width="400" height="380">
  <img src="./public/light-Chat.png?raw=true" width="400" height="380">
</p>

---

## 🎯 Project Goal

Build a realistic, production-style **"AI with memory"** document assistant step by step,
and learn the engineering around LLM apps along the way: agents and tools, retrieval (RAG),
citations, caching, testing and evaluation.

The project is meant to grow from a single Streamlit app into a full application:
better retrieval with vector embeddings, an MCP server, and eventually a dedicated
backend and frontend. See the [Roadmap](#-roadmap).

## 📍 Current Status (October 2026)

**Working, running fully locally on a free model.**

Hugging Face stopped including free inference credits for free accounts, which broke
the original hosted setup. The app now runs on a **local model served by Ollama**.
Because the model is reached through the standard OpenAI-compatible API, moving to
another provider later only means changing environment variables.

What changed in this version:

- **Local model**: `qwen3.8` through Ollama, configured with `MODEL_ID`, `MODEL_API_BASE`
  and `MODEL_API_KEY`.
- **Agent prompt fixed**: the custom instructions were silently ignored before
  (`system_prompt` is read-only in smolagents). They are now appended to the default
  template, with an explicit "search, then `final_answer`" flow and citation examples.
- **Search returns full chunks**: excerpts were cut to 700 characters, which made the
  agent search in loops.
- **Summaries without the agent**: a summary is one direct model call instead of a
  multi-step agent run.
- **One shared citation parser** for the Chat page and the eval, which also understands
  grouped citations such as `[chunk 0, chunk 1]`.
- **Eval improvements**: `--only` to run selected questions, progress output, and fixes
  to scoring that was penalizing correct answers.

Latest eval results (local `qwen3.8` on Apple Silicon, 18 questions):

| Metric | Result |
|---|---|
| Mean correctness | 1.00 |
| Groundedness (correctly says "I can't find it") | 100% |
| Citation match | 73% on the last full run, 100% on the 4 previously failing questions after the citation fix (full re-run pending) |
| Errors | 0 / 18 |
| Latency | ~20–60 s per question, ~34 s on average |

Known limitations:

- **Speed**: each answer takes 20–60 s, because a reasoning model runs locally and the
  agent needs at least two model calls per question.
- **Local only**: Ollama runs on your machine, so a Streamlit Community Cloud deployment
  has no model. It runs with the AI features off (see [Deployment](#deployment)) until a
  hosted, OpenAI-compatible provider is configured.
- **Long documents**: summaries use the first 24,000 characters of a document.
- **Keyword-based scoring**: the eval checks for expected keywords and phrases, so it can
  miss correct answers phrased differently.

---

## 📁 Project Structure

```bash
smol_streamlit_agent/
├── app.py                    # Streamlit entry point (redirects to Home)
├── pages/                    # Home, Upload, Documents, Chat
├── ui/
│   └── common.py             # Shared UI setup, cached agent/model, error-safe runners
├── doc_agent/
│   ├── agent.py              # Model + agent configuration and prompt rules
│   ├── tools.py              # Agent tools (BM25 search, summary cache)
│   ├── summarize.py          # One-call document summaries
│   ├── citations.py          # Shared [chunk N] citation parser
│   ├── storage.py            # SQLite storage, chunking, caches
│   └── errors.py             # User-facing error messages
├── eval/
│   ├── run_eval.py           # Run, score and report the eval
│   ├── score.py              # Pure scoring functions
│   ├── questions.yaml        # 18 eval questions with expected answers
│   └── fixtures/             # The 3 eval documents
├── tests/                    # pytest suite (no model needed)
├── requirements.txt          # Hash-locked dependencies
└── .env                      # Optional local settings (ignored by git)
```

## 🚀 Quick Start

### 1. Install Ollama and a model

Install [Ollama](https://ollama.com/download), then download the model:

```bash
ollama pull qwen3.8
```

`qwen3.8` needs roughly 24 GB of memory. On smaller machines, try `gpt-oss:20b` and set
`MODEL_ID` accordingly.

**Set the context length to 16k or more.** Ollama's default is small, and the agent's
prompt won't fit in it. In the Ollama app, use **Settings → Context length**. If you run
the server yourself, start it with:

```bash
OLLAMA_CONTEXT_LENGTH=16384 ollama serve
```

Check it with `ollama ps` while the model is loaded: the `CONTEXT` column should show
`16384` or more.

### 2. Set up Python

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install --require-hashes -r requirements.txt
```

### 3. Configure

The AI features are **off unless you turn them on**, so a deployment without a model
shows a banner instead of failing. Create a `.env` file with:

```bash
AI_ENABLED=true
```

The model settings default to a local Ollama. Add them only to change them:

```bash
MODEL_ID=qwen3.8
MODEL_API_BASE=http://localhost:11434/v1
MODEL_API_KEY=ollama              # Ollama ignores it; hosted providers need a real key
```

### 4. Run the app

```bash
streamlit run app.py
```

Open the local URL shown in your terminal (usually http://localhost:8501).

## 🧠 How It Works

### 📄 Upload documents

Upload `.txt` files or text-based PDFs. Documents are chunked locally, stored in SQLite
and indexed for BM25 search. **No model call happens during upload.**

### 🔎 Ask questions

The chat agent follows a fixed flow:

1. Search the document with `search_documents` (BM25) and read the top 3 chunks.
2. Answer with `final_answer(...)`, using only those excerpts and citing them as `[chunk N]`.
3. If the excerpts don't answer the question, search once more, then say it can't find it
   rather than guess.

Expand **Show sources** under an answer to see the exact text that was cited.
Answers are cached, so asking the same question again needs no model call.

### 🧾 Summarize documents

Click **Summarize**. The app sends the document text to the model in **one call**, with
no agent involved, and caches the result in SQLite. Later views of the same summary need
no model call.

## 🧪 Testing

The test suite needs no model and no running Ollama, so it also runs in CI.

```bash
pytest          # or pytest -v to see each test
```

## 📊 Evaluation

`eval/run_eval.py` asks the agent 18 questions (`eval/questions.yaml`) about three
fixture documents and scores the answers. It uses its own database, `eval/eval.db`, so
your documents are never touched.

```bash
python eval/run_eval.py                                      # run all questions, score, report
python eval/run_eval.py --only li-01,ls-03                    # run selected questions
python eval/run_eval.py --replay eval/results/run_<ts>.json   # re-score a past run, no model calls
```

| Metric | What it measures |
|---|---|
| **Correctness** | Share of the expected keywords found in the answer |
| **Citation match** | Whether the answer cites one of the chunks that contain the answer |
| **Groundedness** | For questions the document can't answer: does the agent say so instead of guessing? |
| **Latency** | Seconds per question |

Raw answers are saved to `eval/results/run_<timestamp>.json` after every question, and a
per-question CSV goes to `eval/results/report_<timestamp>.csv`.

Tips:

- Use `--only` with a few questions while developing, and the full run before decisions
  (comparing models, changing retrieval).
- Read failing answers before "fixing" the model: a wrong score can come from the eval itself.

## ⚙️ Configuration

| Variable | Default | Purpose |
|---|---|---|
| `AI_ENABLED` | off | `true` turns on chat and new summaries; anything else shows the "unavailable" banner |
| `MODEL_ID` | `qwen3.8` | Model name on the server |
| `MODEL_API_BASE` | `http://localhost:11434/v1` | Any OpenAI-compatible endpoint |
| `MODEL_API_KEY` | `ollama` | API key (ignored by Ollama) |
| `DOC_AGENT_DB` | `doc_agent.db` | SQLite database path |

### Switching provider

Any server that speaks the OpenAI chat-completions API works without code changes.
Point `MODEL_API_BASE`, `MODEL_API_KEY` and `MODEL_ID` at it. Before using a hosted free
tier, check its rate limits and data-use terms.

### Deployment

On Streamlit Community Cloud, settings go in the app's **Secrets** instead of `.env`.
Leave `AI_ENABLED` out to deploy with the AI features off: uploading, browsing and cached
summaries keep working. To turn them on with a hosted provider:

```toml
AI_ENABLED = "true"
MODEL_API_BASE = "https://..."
MODEL_API_KEY = "..."
MODEL_ID = "..."
```

**Quote the values.** Streamlit only copies string and number secrets into environment
variables, so an unquoted `AI_ENABLED = true` (a TOML boolean) would be ignored.

### Adding a tool

Add a function to `doc_agent/tools.py`:

```python
from smolagents import tool

@tool
def your_new_tool(param: str) -> str:
    """
    Description of what your tool does.

    Args:
        param: Description of the parameter.

    Returns:
        Description of what it returns.
    """
    return ...
```

Then register it in `doc_agent/agent.py`:

```python
agent = CodeAgent(
    tools=[search_documents, get_cached_summary, save_summary, your_new_tool],
    # ...
)
```

## 🔐 Security & Safety

- The agent only has first-party tools, none of which touch the filesystem, network or a shell.
- The agent's code sandbox allows no extra imports (`additional_authorized_imports=[]`).
- Printed output and agent steps are capped (`max_print_outputs_length`, `max_steps`).
- Errors shown to users never include provider names, URLs or raw exception details.
- With a local model, documents never leave your machine.
- Dependencies are pinned and hash-locked.

## 🗺️ Roadmap

1. **Finish the evaluation baseline**
   - Full eval run with the latest prompt as the new baseline.
   - Show "n/a" for metrics without questions, and include citations in the worst-scoring list.
   - A **retrieval-only eval**: check that search returns the expected chunks, with no
     LLM involved, so it runs in seconds.
2. **Vector embeddings**
   - Add embedding-based search with a free, local embedding model, and compare it with
     BM25 on the retrieval eval and the full eval.
   - Add harder questions that use different words from the document, where semantic
     search should beat keyword search.
3. **MCP server**
   - Expose document search and summaries through the Model Context Protocol, so other
     AI clients can use the document memory.
4. **Dedicated backend and frontend**
   - Move the agent, storage and retrieval behind a backend API, and build a proper
     frontend on top of it.
   - Add a hosted model option for deployment.

## 🎓 What This Project Teaches

- Agent + tools architecture, and when **not** to use an agent
- Retrieval-Augmented Generation (RAG) and verifiable citations
- Memory and caching design
- Running LLMs locally behind a provider-agnostic API
- Testing LLM apps without calling a model
- Evaluating LLM output, including the limits of the eval itself
