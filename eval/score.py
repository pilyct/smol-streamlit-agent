"""
Pure scoring functions for the eval.

Every function here takes plain data in (answer text, cited chunk
indices, expected values from questions.yaml) and returns numbers or
labels out. No database access, no agent calls -- that's what keeps
this unit-testable without fixtures or mocks.
"""

from typing import List, Tuple

CORRECT_THRESHOLD = 0.7
PARTIAL_THRESHOLD = 0.3

# Small, deliberately conservative list of phrases that count as the
# agent admitting it doesn't know, rather than guessing an answer.
ABSTAIN_PHRASES = [
    "cannot find",
    "can't find",
    "cannot answer",
    "can't answer",
    "no information",
    "not mentioned",
    "does not mention",
    "doesn't mention",
    "not stated",
    "not provided",
    "no evidence",
    "unable to find",
    "i don't know",
    "i do not know",
]


def score_correctness(answer: str, expected_keywords: List[str]) -> Tuple[float, str]:
    """
    Fraction of expected_keywords found (case-insensitively) in the answer,
    plus a correct/partial/incorrect label.

    Only meaningful for non-abstain questions -- callers should not call
    this with an empty expected_keywords list.
    """
    answer_lower = (answer or "").lower()
    matched = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    score = matched / len(expected_keywords)

    if score >= CORRECT_THRESHOLD:
        label = "correct"
    elif score >= PARTIAL_THRESHOLD:
        label = "partial"
    else:
        label = "incorrect"

    return score, label


def score_citation(cited_chunks: List[int], expected_chunks: List[int]) -> float:
    """
    1.0 if any cited chunk index is among expected_chunks, else 0.0.

    A question with no citations at all scores 0.0, same as one that
    cites the wrong chunk -- both mean "didn't point to the right place".
    """
    return 1.0 if set(cited_chunks) & set(expected_chunks) else 0.0


def score_groundedness(answer: str) -> bool:
    """
    True (pass) if the answer contains an explicit abstention phrase,
    for questions the corpus genuinely does not answer.
    """
    answer_lower = (answer or "").lower()
    return any(phrase in answer_lower for phrase in ABSTAIN_PHRASES)


def score_result(question: dict, result: dict) -> dict:
    """
    Score one question/result pair, dispatching to the right metric(s)
    based on whether the question expects abstention.

    `question` is one entry from questions.yaml.
    `result` is one entry from an eval/results/run_*.json file, expected
    to have "answer" and "cited_chunks" keys.
    """
    answer = result.get("answer") or ""
    cited_chunks = result.get("cited_chunks") or []

    scored = {"id": question["id"], "doc": question["doc"]}

    if question.get("expects_abstain"):
        scored["groundedness_pass"] = score_groundedness(answer)
        return scored

    correctness_score, correctness_label = score_correctness(
        answer, question["expected_keywords"]
    )
    scored["correctness_score"] = correctness_score
    scored["correctness_label"] = correctness_label
    scored["citation_score"] = score_citation(
        cited_chunks, question["expected_chunks"]
    )
    return scored
