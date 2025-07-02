import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import utils.secrets


@pytest.fixture(autouse=True)
def global_openai_key(monkeypatch):
    monkeypatch.setattr(utils.secrets, "get_openai_api_key", lambda: "key")
    monkeypatch.setenv("OPENAI_API_KEY", "key")
