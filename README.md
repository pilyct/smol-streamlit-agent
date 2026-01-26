# SmolAgents + Streamlit Demo

A tiny end-to-end project that combines:

- **smolagents** for agent logic and tool use
- **Hugging Face Inference API** for a free, hosted LLM
- **Streamlit** for a simple web chat interface

The agent runs on the open model:

`mistralai/Mistral-7B-Instruct-v0.2`

It can chat and decide when to use small Python tools such as:

- `get_time()` – returns the current time
- `word_count(text)` – counts words in a string

This is a minimal “AI app” you can run locally in a few minutes.

## Project Structure

```bash
smol_streamlit_agent/
├── app.py            # Streamlit web UI (chat interface)
├── agent.py          # Model + agent construction (smolagents)
├── tools.py          # Python tools the agent can call
├── requirements.txt  # Python dependencies
├── .env.example      # Template for environment variables (HF token)
├── .env              # Your real token (ignored by git)
├── .gitignore        # Files and folders excluded from version control
└── README.md         # Project documentation
```

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -U pip
pip install -r requirements.txt
```

### 3. Create a Hugging Face token

- Go to Hugging Face → Settings → Access Tokens
- Create a Fine-grained token with:
  - Inference → Make calls to Inference Providers
  - Repositories → Read access to public gated repos you can access

Copy `.env.example` to `.env` and add your token:

```bash
HUGGINGFACEHUB_API_TOKEN=hf_your_token_here
```

## Run the App

```bash
streamlit run app.py
```

Open the local URL shown in your terminal.

Try prompts like:

- What time is it? Use the tool.
- Count the words in: "agents are loops with ambition".
- Write a haiku about black holes, then tell me the word count.

## Notes

The Hugging Face free tier has rate limits and occasional cold starts.

If the model is unavailable in your region/account, change MODEL_ID
in agent.py to another instruct-tuned model you can access.

This project is intentionally small: it’s a scaffold for learning how
agents, tools, models, and a UI fit together.
