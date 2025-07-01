import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agent2.openai_narrative import OpenAINarrative
from utils.secrets import get_openai_api_key
from tests.openai_test_utils import handle_openai_exception


def test_openai_narrative_live():
    try:
        get_openai_api_key()
    except RuntimeError:
        pytest.skip("OPENAI_API_KEY not found")

    narrative = OpenAINarrative(model="gpt-3.5-turbo")
    metadata = [{"title": "Test", "doi": "10.1234/test"}]
    snippet = ["Example snippet from the paper."]
    try:
        result = narrative.generate(metadata, snippet)
    except Exception as exc:  # pragma: no cover - live network error handling
        handle_openai_exception(exc)
        return
    assert isinstance(result, str) and result.strip()
