import os
import sys
import tempfile
from pathlib import Path
import importlib
import pytest

# Ensure project root is importable so `import doc_agent` works
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@pytest.fixture(autouse=True)
def fresh_db_per_test(monkeypatch):
    """
    Create a fresh SQLite DB for each test and reload doc_agent.storage
    so DB_PATH is recomputed from DOC_AGENT_DB.
    """
    fd, path = tempfile.mkstemp(prefix="doc_agent_test_", suffix=".db")
    os.close(fd)
    monkeypatch.setenv("DOC_AGENT_DB", path)

    # Reload storage module so DB_PATH picks up the new env var
    import doc_agent.storage as storage
    importlib.reload(storage)

    # Initialize schema
    storage.init_db()

    yield

    try:
        os.remove(path)
    except OSError:
        pass
