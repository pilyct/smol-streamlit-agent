import sys
from pathlib import Path

# eval/ isn't a package, so make its contents importable the same way
# conftest.py already makes the project root importable.
EVAL_DIR = Path(__file__).resolve().parents[1] / "eval"
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

from score import (  # noqa: E402
    score_correctness,
    score_citation,
    score_groundedness,
    score_result,
)


# -------------------------
# score_correctness
# -------------------------

def test_correctness_all_keywords_present_is_correct():
    score, label = score_correctness(
        "She used Power BI, Tableau, and Shiny for dashboards.",
        ["Power BI", "Tableau", "Shiny"],
    )
    assert score == 1.0
    assert label == "correct"


def test_correctness_is_case_insensitive():
    score, label = score_correctness(
        "she used power bi and tableau",
        ["Power BI", "Tableau"],
    )
    assert score == 1.0
    assert label == "correct"


def test_correctness_some_keywords_present_is_partial():
    score, label = score_correctness(
        "She used Power BI for dashboards.",
        ["Power BI", "Tableau", "Shiny"],
    )
    assert round(score, 2) == round(1 / 3, 2)
    assert label == "partial"


def test_correctness_no_keywords_present_is_incorrect():
    score, label = score_correctness(
        "I'm not sure what tools were used.",
        ["Power BI", "Tableau", "Shiny"],
    )
    assert score == 0.0
    assert label == "incorrect"


def test_correctness_handles_none_answer():
    score, label = score_correctness(None, ["Power BI"])
    assert score == 0.0
    assert label == "incorrect"


# -------------------------
# score_citation
# -------------------------

def test_citation_hit_scores_one():
    assert score_citation([1], [1]) == 1.0


def test_citation_partial_overlap_still_scores_one():
    assert score_citation([0, 1], [1]) == 1.0


def test_citation_miss_scores_zero():
    assert score_citation([0], [1]) == 0.0


def test_citation_no_citations_scores_zero_not_none():
    result = score_citation([], [1])
    assert result == 0.0
    assert result is not None


# -------------------------
# score_groundedness
# -------------------------

def test_groundedness_passes_on_explicit_abstention():
    assert score_groundedness("I cannot find this information in the document.") is True


def test_groundedness_fails_on_confident_hallucination():
    assert score_groundedness("Mira's job title is Senior Data Analyst.") is False


def test_groundedness_handles_none_answer():
    assert score_groundedness(None) is False


# -------------------------
# score_result (dispatch)
# -------------------------

def test_score_result_non_abstain_question():
    question = {
        "id": "li-03",
        "doc": "LinkedIn_Profile",
        "expected_keywords": ["Power BI", "Tableau", "Shiny"],
        "expected_chunks": [1],
        "expects_abstain": False,
    }
    result = {"answer": "Power BI, Tableau, and Shiny [chunk 1]", "cited_chunks": [1]}

    scored = score_result(question, result)

    assert scored["correctness_score"] == 1.0
    assert scored["correctness_label"] == "correct"
    assert scored["citation_score"] == 1.0
    assert "groundedness_pass" not in scored


def test_score_result_abstain_question():
    question = {
        "id": "ls-06",
        "doc": "Life_Story",
        "expected_keywords": [],
        "expected_chunks": [],
        "expects_abstain": True,
    }
    result = {"answer": "I cannot find this information in the document.", "cited_chunks": []}

    scored = score_result(question, result)

    assert scored["groundedness_pass"] is True
    assert "correctness_score" not in scored
    assert "citation_score" not in scored
