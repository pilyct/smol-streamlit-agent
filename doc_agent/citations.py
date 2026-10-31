import re
from typing import Optional

# Matches "[chunk 3]" as well as grouped forms models also write, such as
# "[chunk 0, chunk 1]" or "[chunks 0, 1]".
_CITATION_RE = re.compile(
    r"\[\s*chunks?\s+(\d+(?:\s*,\s*(?:chunks?\s+)?\d+)*)\s*\]",
    re.IGNORECASE,
)


def extract_cited_chunks(answer: Optional[str]) -> list[int]:
    """
    Return the sorted, unique chunk indices cited in an answer.

    Shared by the Chat page and the eval, so the eval measures exactly the
    citations users see.
    """
    cited: set[int] = set()
    for group in _CITATION_RE.findall(answer or ""):
        cited.update(int(n) for n in re.findall(r"\d+", group))
    return sorted(cited)
