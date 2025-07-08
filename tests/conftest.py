import sys
from pathlib import Path
import socket

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import utils.secrets


@pytest.fixture(autouse=True)
def global_openai_key(monkeypatch):
    monkeypatch.setattr(utils.secrets, "get_openai_api_key", lambda: "key")
    monkeypatch.setenv("OPENAI_API_KEY", "key")


@pytest.fixture(autouse=True)
def no_network_calls(monkeypatch):
    """Fail tests that attempt real network access."""

    def guard(*_args, **_kwargs):
        raise RuntimeError("Network access blocked during tests")

    monkeypatch.setattr(socket.socket, "connect", guard)
