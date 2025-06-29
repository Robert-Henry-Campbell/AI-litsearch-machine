import sys
import types

import orjson
import pytest

# Create a fake openai module
fake_openai = types.ModuleType("openai")
fake_openai.error = types.SimpleNamespace()
fake_openai.error.AuthenticationError = type("AuthError", (Exception,), {})
fake_openai.error.RateLimitError = type("RateLimitError", (Exception,), {})


class FakeChatCompletion:
    def __init__(self):
        self.calls = []
        self.responses = []

    def create(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})
        resp = self.responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp


fake_chat = FakeChatCompletion()
fake_openai.ChatCompletion = fake_chat
sys.modules["openai"] = fake_openai

from agent1.openai_client import OpenAIJSONCaller  # noqa: E402


def setup_prompt(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    path = prompt_dir / "agent1_prompt.txt"
    path.write_text("Prompt")
    return path


def test_success(monkeypatch, tmp_path):
    path = setup_prompt(tmp_path)
    monkeypatch.setattr("agent1.openai_client.PROMPT_PATH", path)
    fake_chat.calls.clear()
    fake_chat.responses = [{"choices": [{"message": {"content": '{"ok": 1}'}}]}]
    client = OpenAIJSONCaller(model="test")
    result = client.call("hello")
    assert result == {"ok": 1}
    assert len(fake_chat.calls) == 1


def test_retry(monkeypatch, tmp_path):
    path = setup_prompt(tmp_path)
    monkeypatch.setattr("agent1.openai_client.PROMPT_PATH", path)
    fake_chat.calls.clear()
    fake_chat.responses = [
        {"choices": [{"message": {"content": "not json"}}]},
        {"choices": [{"message": {"content": '{"ok": 2}'}}]},
    ]
    monkeypatch.setattr("time.sleep", lambda x: None)
    client = OpenAIJSONCaller(model="test")
    result = client.call("hello")
    assert result == {"ok": 2}
    assert len(fake_chat.calls) == 2


def test_fail(monkeypatch, tmp_path):
    path = setup_prompt(tmp_path)
    monkeypatch.setattr("agent1.openai_client.PROMPT_PATH", path)
    fake_chat.calls.clear()
    fake_chat.responses = [
        {"choices": [{"message": {"content": "bad"}}]},
        {"choices": [{"message": {"content": "still bad"}}]},
        {"choices": [{"message": {"content": "nope"}}]},
    ]
    monkeypatch.setattr("time.sleep", lambda x: None)
    client = OpenAIJSONCaller(model="test")
    with pytest.raises(orjson.JSONDecodeError):
        client.call("hello")
    assert len(fake_chat.calls) == 3


def test_auth_error(monkeypatch, tmp_path):
    path = setup_prompt(tmp_path)
    monkeypatch.setattr("agent1.openai_client.PROMPT_PATH", path)
    fake_chat.calls.clear()
    fake_chat.responses = [fake_openai.error.AuthenticationError("bad key")]
    client = OpenAIJSONCaller(model="test")
    with pytest.raises(fake_openai.error.AuthenticationError):
        client.call("hello")
    assert len(fake_chat.calls) == 1


def test_rate_limit(monkeypatch, tmp_path):
    path = setup_prompt(tmp_path)
    monkeypatch.setattr("agent1.openai_client.PROMPT_PATH", path)
    fake_chat.calls.clear()
    fake_chat.responses = [
        fake_openai.error.RateLimitError("rate"),
        {"choices": [{"message": {"content": '{"ok": 3}'}}]},
    ]
    monkeypatch.setattr("time.sleep", lambda x: None)
    client = OpenAIJSONCaller(model="test")
    result = client.call("hello")
    assert result == {"ok": 3}
    assert len(fake_chat.calls) == 2
