from __future__ import annotations

import sys
import types
from unittest import mock

import pytest


@pytest.fixture()
def validator(monkeypatch, tmp_path):
    responses: list[str] = []
    client = mock.MagicMock()
    client.beta.assistants.create.return_value = types.SimpleNamespace(id="assist-1")
    client.beta.threads.create.return_value = types.SimpleNamespace(id="thread-1")
    client.beta.threads.runs.create.return_value = types.SimpleNamespace(id="run-1")

    def list_messages(thread_id: str):
        text = responses.pop(0)
        msg = types.SimpleNamespace(
            content=[types.SimpleNamespace(text=types.SimpleNamespace(value=text))]
        )
        return types.SimpleNamespace(data=[msg])

    client.beta.threads.messages.list.side_effect = list_messages

    openai_patcher = mock.patch("openai.OpenAI", return_value=client)
    openai_patcher.start()
    monkeypatch.setattr("utils.secrets.get_openai_api_key", lambda: "key")

    import agent3.openai_validator as ov

    monkeypatch.setattr(ov, "_wait_for_run", lambda *a, **k: None)

    yield ov, client.beta.assistants.create, responses

    openai_patcher.stop()
    sys.modules.pop("agent3.openai_validator", None)


def test_is_conflict_reuses_assistant(validator):
    ov, create_call, responses = validator
    responses.extend(["Yes", "No"])
    assert ov.is_conflict("A", "B", "title") is True
    assert ov.is_conflict("A", "A", "title") is False
    assert create_call.call_count == 1
