import sys
import types
from pathlib import Path
import importlib
import pytest


# Setup fake openai module before import
fake_openai = types.ModuleType("openai")
fake_openai.AuthenticationError = type("AuthError", (Exception,), {})
fake_openai.RateLimitError = type("RateLimitError", (Exception,), {})
fake_openai.error = types.SimpleNamespace(
    AuthenticationError=fake_openai.AuthenticationError,
    RateLimitError=fake_openai.RateLimitError,
)


class FakeChatCompletion:
    def __init__(self):
        self.calls = []
        self.responses = []

    def create(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})
        resp = self.responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        if isinstance(resp, dict):
            usage = resp.get("usage", {})

            def to_ns(obj):
                if isinstance(obj, dict):
                    return types.SimpleNamespace(
                        **{k: to_ns(v) for k, v in obj.items()}
                    )
                if isinstance(obj, list):
                    return [to_ns(x) for x in obj]
                return obj

            ns = to_ns({k: v for k, v in resp.items() if k != "usage"})
            ns.usage = usage
            return ns
        return resp


fake_chat = FakeChatCompletion()
fake_client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=fake_chat))
fake_openai.ChatCompletion = fake_chat
fake_openai.OpenAI = lambda api_key=None: fake_client

real_openai = sys.modules.get("openai")


@pytest.fixture(autouse=True)
def fake_openai_module(monkeypatch):
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    import agent2.openai_narrative as on

    importlib.reload(on)
    yield
    if real_openai is not None:
        monkeypatch.setitem(sys.modules, "openai", real_openai)
    else:
        monkeypatch.delitem(sys.modules, "openai", raising=False)
    importlib.reload(on)


@pytest.fixture(autouse=True)
def fake_openai_key(monkeypatch):
    monkeypatch.setattr("agent2.openai_narrative.get_openai_api_key", lambda: "key")


def setup_prompt(tmp_path: Path) -> Path:
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    path = prompt_dir / "agent2_system.txt"
    path.write_text("Prompt")
    return path


def test_success(monkeypatch, tmp_path):
    path = setup_prompt(tmp_path)
    monkeypatch.setattr("agent2.openai_narrative.PROMPT_PATH", path)
    fake_chat.calls.clear()
    fake_chat.responses = [{"choices": [{"message": {"content": "done"}}]}]
    from agent2.openai_narrative import OpenAINarrative

    gen = OpenAINarrative(model="test")
    result = gen.generate([{"title": "T"}], ["s1"])
    assert result == "done"
    assert len(fake_chat.calls) == 1


def test_retry(monkeypatch, tmp_path):
    path = setup_prompt(tmp_path)
    monkeypatch.setattr("agent2.openai_narrative.PROMPT_PATH", path)
    fake_chat.calls.clear()
    fake_chat.responses = [
        RuntimeError("bad"),
        {"choices": [{"message": {"content": "ok"}}]},
    ]
    monkeypatch.setattr("time.sleep", lambda x: None)
    from agent2.openai_narrative import OpenAINarrative

    gen = OpenAINarrative(model="test")
    result = gen.generate([{"title": "T"}], ["s1"])
    assert result == "ok"
    assert len(fake_chat.calls) == 2


def test_auth_error(monkeypatch, tmp_path):
    path = setup_prompt(tmp_path)
    monkeypatch.setattr("agent2.openai_narrative.PROMPT_PATH", path)
    fake_chat.calls.clear()
    fake_chat.responses = [fake_openai.error.AuthenticationError("bad key")]
    from agent2.openai_narrative import OpenAINarrative

    gen = OpenAINarrative(model="test")
    with pytest.raises(fake_openai.error.AuthenticationError):
        gen.generate([{"title": "T"}], ["s1"])
    assert len(fake_chat.calls) == 1


def test_rate_limit(monkeypatch, tmp_path):
    path = setup_prompt(tmp_path)
    monkeypatch.setattr("agent2.openai_narrative.PROMPT_PATH", path)
    fake_chat.calls.clear()
    fake_chat.responses = [
        fake_openai.error.RateLimitError("rate"),
        {"choices": [{"message": {"content": "ok"}}]},
    ]
    monkeypatch.setattr("time.sleep", lambda x: None)
    from agent2.openai_narrative import OpenAINarrative

    gen = OpenAINarrative(model="test")
    result = gen.generate([{"title": "T"}], ["s1"])
    assert result == "ok"
    assert len(fake_chat.calls) == 2
