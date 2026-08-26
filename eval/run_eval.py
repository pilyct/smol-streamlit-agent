import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("DOC_AGENT_DB", str(Path(__file__).parent / "eval.db"))

from doc_agent.agent import build_agent
from doc_agent.storage import (
    init_db,
    list_documents,
    upsert_document,
    chunk_text,
    insert_chunks,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
QUESTIONS_PATH = Path(__file__).parent / "questions.yaml"
RESULTS_DIR = Path(__file__).parent / "results"

FIXTURES = {
    "Home_Workout_Routine": "home_workout_routine.txt",
    "Life_Story": "life_story.txt",
    "LinkedIn_Profile": "linkedin_profile.txt",
}

# Same regex pages/Chat.py uses to pull citations out of an answer, copied
# verbatim so the eval measures exactly what the UI shows users.
_CITATION_RE = re.compile(r"\[chunk\s+(\d+)\]", re.IGNORECASE)


def seed_fixtures() -> None:
    init_db()
    existing = {name for name, _created_at in list_documents()}

    for doc_name, filename in FIXTURES.items():
        if doc_name in existing:
            continue

        text = (FIXTURES_DIR / filename).read_text(encoding="utf-8")
        created_at_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

        doc_id = upsert_document(doc_name, created_at_iso)
        chunks = chunk_text(text)
        insert_chunks(doc_id, chunks)


def extract_cited_chunks(answer: str) -> list[int]:
    return sorted({int(x) for x in _CITATION_RE.findall(answer)})


def load_questions() -> list[dict]:
    with QUESTIONS_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_questions(questions: list[dict]) -> Path:
    """
    Ask every question to a single, real agent instance and record what it
    returns. Nothing is scored here -- this only captures raw answers.
    """
    agent = build_agent(verbose=0)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results_path = RESULTS_DIR / f"run_{run_id}.json"

    results: list[dict] = []

    for q in questions:
        prompt = (
            f"Document name: {q['doc']}\n"
            f"User question: {q['question']}\n"
            "Answer the question about this document."
        )

        started = time.monotonic()
        row = {"id": q["id"], "doc": q["doc"], "question": q["question"]}

        try:
            answer = agent.run(prompt)
            row["answer"] = answer
            row["cited_chunks"] = extract_cited_chunks(answer)
            row["error"] = None
        except Exception as e:
            row["answer"] = None
            row["cited_chunks"] = []
            row["error"] = str(e)

        row["latency_seconds"] = round(time.monotonic() - started, 3)
        results.append(row)

        # Write after every question so a crash mid-run doesn't lose earlier
        # answers -- the file is always valid, complete JSON up to this point.
        with results_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    return results_path


if __name__ == "__main__":
    seed_fixtures()
    questions = load_questions()
    results_path = run_questions(questions)
    print(f"Wrote {len(questions)} results to {results_path}")
