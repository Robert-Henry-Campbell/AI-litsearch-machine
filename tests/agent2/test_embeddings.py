from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

# Setup fake openai module before import
fake_openai = types.ModuleType("openai")
fake_openai.AuthenticationError = type("AuthError", (Exception,), {})
fake_openai.RateLimitError = type("RateLimitError", (Exception,), {})
fake_openai.error = types.SimpleNamespace(
    AuthenticationError=fake_openai.AuthenticationError,
    RateLimitError=fake_openai.RateLimitError,
)


class FakeEmbeddingEndpoint:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.responses: list = []

    def create(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})
        resp = self.responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp


fake_embed = FakeEmbeddingEndpoint()
fake_client = types.SimpleNamespace(embeddings=fake_embed)

fake_openai.OpenAI = lambda api_key=None: fake_client

real_openai = sys.modules.get("openai")


@pytest.fixture(autouse=True)
def fake_openai_module(monkeypatch):
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    import agent2.embeddings as emb

    importlib.reload(emb)
    yield
    if real_openai is not None:
        monkeypatch.setitem(sys.modules, "openai", real_openai)
    else:
        monkeypatch.delitem(sys.modules, "openai", raising=False)
    importlib.reload(emb)


def teardown_module(module):
    for mod in ("agent2.embeddings", "openai"):
        sys.modules.pop(mod, None)


@pytest.fixture(autouse=True)
def fake_openai_key(monkeypatch):
    import agent2.embeddings as emb

    monkeypatch.setattr(emb, "get_openai_api_key", lambda: "key")


def test_chunk_text_basic():
    from agent2.embeddings import chunk_text

    text = " ".join(f"t{i}" for i in range(100))
    chunks = chunk_text(text, chunk_size=10, overlap=2)
    assert len(chunks) == 13
    assert chunks[0].split()[0] == "t0"
    assert chunks[1].split()[0] == "t8"


def test_embed_chunks_success(monkeypatch):
    from agent2.embeddings import embed_chunks

    fake_embed.calls.clear()
    fake_embed.responses = [
        types.SimpleNamespace(data=[types.SimpleNamespace(embedding=[0.1, 0.2])])
    ]
    result = embed_chunks(["hello"])
    assert result == [[0.1, 0.2]]
    assert len(fake_embed.calls) == 1


def test_embed_chunks_retry(monkeypatch):
    from agent2.embeddings import embed_chunks

    fake_embed.calls.clear()
    fake_embed.responses = [
        RuntimeError("fail"),
        types.SimpleNamespace(data=[types.SimpleNamespace(embedding=[1.0])]),
    ]
    monkeypatch.setattr("time.sleep", lambda x: None)
    result = embed_chunks(["test"])
    assert result == [[1.0]]
    assert len(fake_embed.calls) == 2


def test_embed_chunks_auth(monkeypatch):
    from agent2.embeddings import embed_chunks

    fake_embed.calls.clear()
    fake_embed.responses = [fake_openai.error.AuthenticationError("bad key")]
    with pytest.raises(fake_openai.error.AuthenticationError):
        embed_chunks(["x"])
    assert len(fake_embed.calls) == 1
