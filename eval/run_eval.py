import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

import yaml

EVAL_DIR = Path(__file__).parent
sys.path.insert(0, str(EVAL_DIR.parent))
sys.path.insert(0, str(EVAL_DIR))

os.environ.setdefault("DOC_AGENT_DB", str(EVAL_DIR / "eval.db"))

from doc_agent.agent import build_agent
from doc_agent.storage import (
    init_db,
    list_documents,
    upsert_document,
    chunk_text,
    insert_chunks,
)
from score import score_correctness, score_citation, score_groundedness

FIXTURES_DIR = EVAL_DIR / "fixtures"
QUESTIONS_PATH = EVAL_DIR / "questions.yaml"
RESULTS_DIR = EVAL_DIR / "results"

CSV_FIELDS = [
    "id",
    "doc",
    "question",
    "correctness_score",
    "correctness_label",
    "citation_score",
    "groundedness",
    "cited_chunks",
    "expected_chunks",
    "latency_s",
    "answer_excerpt",
]

ANSWER_EXCERPT_LIMIT = 200

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


def run_questions(questions: list[dict], run_id: str) -> tuple[Path, list[dict]]:
    """
    Ask every question to a single, real agent instance and record what it
    returns. Nothing is scored here -- this only captures raw answers.
    """
    agent = build_agent(verbose=0)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
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

    return results_path, results


def _excerpt(text: str, limit: int = ANSWER_EXCERPT_LIMIT) -> str:
    text = text or ""
    return text[:limit] + ("..." if len(text) > limit else "")


def build_report_rows(questions: list[dict], results: list[dict]) -> list[dict]:
    """
    Score every question/result pair and flatten it into one CSV-ready row.
    Columns that don't apply to a question (e.g. correctness for an
    abstention question) are left blank rather than filled with a fake 0.
    """
    results_by_id = {r["id"]: r for r in results}
    rows: list[dict] = []

    for q in questions:
        r = results_by_id.get(q["id"], {})
        answer = r.get("answer")
        error = r.get("error")
        cited_chunks = r.get("cited_chunks") or []

        row = {
            "id": q["id"],
            "doc": q["doc"],
            "question": q["question"],
            "correctness_score": "",
            "correctness_label": "",
            "citation_score": "",
            "groundedness": "",
            "cited_chunks": ";".join(str(c) for c in cited_chunks),
            "expected_chunks": ";".join(str(c) for c in q["expected_chunks"]),
            "latency_s": r.get("latency_seconds", ""),
            "answer_excerpt": _excerpt(f"ERROR: {error}" if error else answer),
        }

        if q.get("expects_abstain"):
            row["groundedness"] = score_groundedness(answer)
        else:
            score, label = score_correctness(answer, q["expected_keywords"])
            row["correctness_score"] = round(score, 3)
            row["correctness_label"] = label
            row["citation_score"] = score_citation(cited_chunks, q["expected_chunks"])

        rows.append(row)

    return rows


def write_report_csv(rows: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows: list[dict]) -> None:
    non_abstain = [r for r in rows if r["correctness_score"] != ""]
    abstain = [r for r in rows if r["groundedness"] != ""]
    errored = [r for r in rows if r["answer_excerpt"].startswith("ERROR:")]

    mean_correctness = mean(r["correctness_score"] for r in non_abstain) if non_abstain else 0.0
    citation_match_pct = (
        mean(r["citation_score"] for r in non_abstain) * 100 if non_abstain else 0.0
    )
    groundedness_pass_pct = (
        mean(1.0 if r["groundedness"] else 0.0 for r in abstain) * 100 if abstain else 0.0
    )

    def worst_key(r: dict) -> float:
        if r["groundedness"] != "":
            return 1.0 if r["groundedness"] else 0.0
        return r["correctness_score"]

    worst = sorted(rows, key=worst_key)[:3]

    print("\n=== Eval summary ===")
    print(f"Mean correctness (non-abstain): {mean_correctness:.2f}")
    print(f"Citation match rate: {citation_match_pct:.0f}%")
    print(f"Groundedness pass rate (abstain): {groundedness_pass_pct:.0f}%")
    print(f"Errors: {len(errored)}/{len(rows)}")
    print("Worst-scoring questions:")
    for r in worst:
        score = worst_key(r)
        print(f"  {r['id']} ({r['doc']}): {score:.2f}")


def _run_id_from_results_path(path: Path) -> str:
    stem = path.stem  # e.g. "run_20260826T134209Z"
    if stem.startswith("run_"):
        return stem[len("run_"):]
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed fixtures, ask the agent every eval question, score the answers, and report."
    )
    parser.add_argument(
        "--replay",
        type=Path,
        default=None,
        metavar="RUN_JSON",
        help=(
            "Path to a previous eval/results/run_<timestamp>.json. "
            "Re-scores that capture instead of seeding the DB and calling the agent again."
        ),
    )
    args = parser.parse_args()

    questions = load_questions()

    if args.replay:
        results_path = args.replay
        with results_path.open(encoding="utf-8") as f:
            results = json.load(f)
        run_id = _run_id_from_results_path(results_path)
    else:
        seed_fixtures()
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        results_path, results = run_questions(questions, run_id)

    rows = build_report_rows(questions, results)
    report_path = RESULTS_DIR / f"report_{run_id}.csv"
    write_report_csv(rows, report_path)

    print(f"Using results from {results_path}")
    print(f"Wrote report to {report_path}")
    print_summary(rows)


if __name__ == "__main__":
    main()
