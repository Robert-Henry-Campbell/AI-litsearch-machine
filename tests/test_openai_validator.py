import importlib
import sys
import types

import pytest


# Fake OpenAI module for assistants API
fake_openai = types.ModuleType("openai")


class FakeAssistants:
    def __init__(self) -> None:
        self.create_calls = []

    def create(self, **kwargs):
        self.create_calls.append(kwargs)
        return types.SimpleNamespace(id="assist-1")


class FakeRuns:
    def __init__(self) -> None:
        self.create_calls = []
        self.retrieve_calls = []

    def create(self, thread_id, assistant_id, **kwargs):
        self.create_calls.append({"thread_id": thread_id, "assistant_id": assistant_id})
        return types.SimpleNamespace(id="run-1", status="completed")

    def retrieve(self, thread_id, run_id):
        self.retrieve_calls.append({"thread_id": thread_id, "run_id": run_id})
        return types.SimpleNamespace(id=run_id, status="completed")


class FakeMessages:
    def __init__(self, parent) -> None:
        self.parent = parent
        self.list_calls = []

    def list(self, thread_id):
        self.list_calls.append({"thread_id": thread_id})
        text = self.parent.responses.pop(0)
        msg = types.SimpleNamespace(
            content=[types.SimpleNamespace(text=types.SimpleNamespace(value=text))]
        )
        return types.SimpleNamespace(data=[msg])


class FakeThreads:
    def __init__(self) -> None:
        self.create_calls = []
        self.runs = FakeRuns()
        self.messages = FakeMessages(self)
        self.responses = []

    def create(self, messages=None):
        self.create_calls.append(messages)
        return types.SimpleNamespace(id=f"thread-{len(self.create_calls)}")


fake_assistants = FakeAssistants()
fake_threads = FakeThreads()
fake_client = types.SimpleNamespace(
    beta=types.SimpleNamespace(assistants=fake_assistants, threads=fake_threads)
)
fake_openai.OpenAI = lambda api_key=None: fake_client

real_openai = sys.modules.get("openai")


@pytest.fixture(autouse=True)
def fake_module(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    import agent3.openai_validator as ov

    prompt = tmp_path / "agent3_system.txt"
    prompt.write_text("Prompt")
    monkeypatch.setattr(ov, "PROMPT_PATH", prompt)
    monkeypatch.setattr(ov, "get_openai_api_key", lambda: "key")
    fake_assistants.create_calls.clear()
    importlib.reload(ov)
    yield ov
    if real_openai is not None:
        monkeypatch.setitem(sys.modules, "openai", real_openai)
    else:
        monkeypatch.delitem(sys.modules, "openai", raising=False)
    sys.modules.pop("agent3.openai_validator", None)


def test_reuse_assistant(fake_module):
    fake_threads.responses = ["Yes", "No"]
    assert fake_module.is_conflict("A", "B", "title") is True
    assert fake_module.is_conflict("A", "A", "title") is False
    assert len(fake_assistants.create_calls) == 1
