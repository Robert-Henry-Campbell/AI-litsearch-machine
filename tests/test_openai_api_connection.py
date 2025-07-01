import sys
from pathlib import Path

import openai
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.secrets import get_openai_api_key
from tests.openai_test_utils import handle_openai_exception


@pytest.mark.skip(reason="Live API call too expensive to run every time")
def test_openai_api_connection():
    try:
        api_key = get_openai_api_key()
    except RuntimeError:
        pytest.skip("OPENAI_API_KEY not found")

    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=1,
        )
    except Exception as exc:  # pragma: no cover - live network error handling
        handle_openai_exception(exc)
        return

    assert response.choices[0].message.content


def test_openai_api_connection_offline(monkeypatch):
    """Offline version that avoids real API calls."""
    import types

    monkeypatch.setattr("utils.secrets.get_openai_api_key", lambda: "key")

    class FakeChat:
        def create(self, *args, **kwargs):
            return types.SimpleNamespace(
                choices=[
                    types.SimpleNamespace(message=types.SimpleNamespace(content="hi"))
                ]
            )

    fake_client = types.SimpleNamespace(
        chat=types.SimpleNamespace(completions=FakeChat())
    )

    monkeypatch.setattr(openai, "OpenAI", lambda api_key=None: fake_client)

    api_key = get_openai_api_key()
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=1,
    )
    assert response.choices[0].message.content == "hi"
