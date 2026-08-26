import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from doc_agent.storage import (
    init_db,
    list_documents,
    upsert_document,
    chunk_text,
    insert_chunks,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"

FIXTURES = {
    "Home_Workout_Routine": "home_workout_routine.txt",
    "Life_Story": "life_story.txt",
    "LinkedIn_Profile": "linkedin_profile.txt",
}


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


if __name__ == "__main__":
    seed_fixtures()
