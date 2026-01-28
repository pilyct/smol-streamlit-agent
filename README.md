# 🤖 SmolAgents + Streamlit Demo

A tiny and complete end-to-end project demonstrating agentic AI with tool use:

- **smolagents** for agent logic and tool orchestration.
- **Hugging Face Inference API** for a free, hosted LLM.
- **Streamlit** for a clean web chat interface.

The agent runs on the open model:

`Qwen/Qwen2.5-7B-Instruct`(free tier)

It can intelligently decide when to use Python tools such as:

- `get_time(timezone)` – Get current time in any timezone.
- `word_count(text)` – Count words in a string.

This is a minimal production-ready "AI app" you can run locally in minutes, plus an interactive terminal interface for testing!

## 📁 Project Structure

```bash
smol_streamlit_agent/
├── .env                    # Your HF token (ignored by git)
├── .gitignore              # Files excluded from version control
├── requirements.txt        # Python dependencies
├── README.md               # This file
│
├── tools.py                # Custom Python tools for the agent
├── agent.py                # Agent construction (smolagents + model)
├── app.py                  # Streamlit web UI (chat interface)
│
└── test/                   # Testing suite
    ├── test_tools.py       # Test tools directly (fastest)
    ├── test_agent.py       # Test agent with predefined questions
    ├── interactive_test.py # Terminal chat interface
    └── run_all_tests.py    # Run all tests in sequence
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

## 🧪 Testing (Before running the app)

### 1. Test Tools (Fastest)

```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
```

### 2. Test Agent

```bash
python test/test_agent.py
```

Runs predefined test cases to verify agent functionality.

### 3. Interactive Terminal Chat

```bash
python test/interactive_test.py
```

Chat with your agent directly in the terminal:

```
🤖 INTERACTIVE AGENT TEST
📦 Model: Qwen/Qwen2.5-7B-Instruct
💡 Type your questions and press Enter

You: What time is it in Berlin?
🤖 Agent (took 3.2s): The current time in Berlin is 2024-01-28T15:30:45+01:00

You: quit
👋 Goodbye!
```

### Run All Tests at once

```bash
python test/run_all_tests.py
```

## 🌐 Run the App

```bash
streamlit run app.py
```

Open the local URL shown in your terminal (typically http://localhost:8501).

Try prompts like:

- "What time is it in Tokyo?"
- "Count the words in: 'agents are loops with ambition'"
- "What time is it in Berlin and New York?"
- "Write a haiku about black holes, then count its words"

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

## 🎓 Learning Resources

- [smolagents Documentation](https://github.com/huggingface/smolagents)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Hugging Face Inference API](https://huggingface.co/docs/api-inference)
- [Building AI Agents Guide](https://huggingface.co/blog/smolagents)

## 📝 Notes

- The **Hugging Face free tier** has rate limits and occasional cold starts.
- `Qwen 2.5 7B` provides the best balance of speed and capability for free.
- This project is intentionally minimal: it's a **learning scaffold**showing how agents, tools, models, and UI fit together.
- All code is production-ready with proper error handling and testing.

## Next Steps

1. **Add more tools** (weather API, calculator, web search)
2. **Integrate with external APIs** (news, stocks, etc.)
3. **Deploy to cloud** (Streamlit Cloud, HF Spaces)
4. **Add conversation memory** for multi-turn dialogues
5. **Implement RAG** (Retrieval Augmented Generation)
