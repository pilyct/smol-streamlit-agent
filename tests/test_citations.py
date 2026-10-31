import pytest

from doc_agent.citations import extract_cited_chunks


@pytest.mark.parametrize(
    "answer, expected",
    [
        ("Tuesday [chunk 0]", [0]),
        ("Python and R [chunk 1] [chunk 0]", [0, 1]),
        ("Design and data skills [chunk 0, chunk 1]", [0, 1]),
        ("Both roles [chunks 0, 2]", [0, 2]),
        ("Repeated [chunk 1] and again [CHUNK 1]", [1]),
        ("A pigeon", []),
        ("", []),
        (None, []),
    ],
)
def test_extract_cited_chunks(answer, expected):
    assert extract_cited_chunks(answer) == expected


def test_ignores_brackets_that_are_not_citations():
    assert extract_cited_chunks("See [note 3] and [1]") == []
