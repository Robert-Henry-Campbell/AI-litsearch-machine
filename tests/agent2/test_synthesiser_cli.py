from __future__ import annotations

import sys
import types
from pathlib import Path

import orjson

# Setup fake openai before importing synthesiser
fake_openai = types.ModuleType("openai")
sys.modules["openai"] = fake_openai


def teardown_module(module):
    """Restore the real OpenAI module after tests."""
    for mod in ("agent2.synthesiser", "openai"):
        sys.modules.pop(mod, None)


import agent2.synthesiser as synthesiser  # noqa: E402


class FakeNarrative:
    def __init__(self):
        self.calls = []

    def generate(self, metadata, snippets):
        self.calls.append({"metadata": metadata, "snippets": snippets})
        return "# Review"


def create_master(tmp_path: Path) -> Path:
    data = [
        {"title": "A", "doi": "10.1/a", "targets": ["DrugX"]},
        {"title": "B", "doi": "10.2/b", "targets": ["Other"]},
    ]
    path = tmp_path / "master.json"
    path.write_bytes(orjson.dumps(data))
    return path


def test_cli_success(monkeypatch, tmp_path: Path) -> None:
    master = create_master(tmp_path)
    out_dir = tmp_path / "out"
    monkeypatch.setattr(synthesiser, "MASTER_PATH", master)
    monkeypatch.setattr(synthesiser, "OUTPUT_DIR", out_dir)
    monkeypatch.setattr(synthesiser, "SNIPPETS_PATH", tmp_path / "snippets.json")
    monkeypatch.setattr(synthesiser, "OpenAINarrative", FakeNarrative)
    monkeypatch.setattr(synthesiser.retrieval, "get_snippets", lambda doi, kw: [f"s-{doi}"])  # type: ignore

    code = synthesiser.main(["--drug", "DrugX"])
    assert code == 0
    out_file = out_dir / "review_DrugX.md"
    assert out_file.exists()
    assert out_file.read_text() == "# Review"
    snippets_path = tmp_path / "snippets.json"
    assert snippets_path.exists()
    assert orjson.loads(snippets_path.read_bytes()) == ["s-10.1/a"]


def test_no_data(monkeypatch, tmp_path: Path) -> None:
    master = create_master(tmp_path)
    out_dir = tmp_path / "out"
    monkeypatch.setattr(synthesiser, "MASTER_PATH", master)
    monkeypatch.setattr(synthesiser, "OUTPUT_DIR", out_dir)
    monkeypatch.setattr(synthesiser, "SNIPPETS_PATH", tmp_path / "snippets.json")
    monkeypatch.setattr(synthesiser, "OpenAINarrative", FakeNarrative)

    code = synthesiser.main(["--drug", "Missing"])
    assert code == 1
    assert not out_dir.exists()


def test_empty_snippets(monkeypatch, tmp_path: Path) -> None:
    master = create_master(tmp_path)
    out_dir = tmp_path / "out"
    monkeypatch.setattr(synthesiser, "MASTER_PATH", master)
    monkeypatch.setattr(synthesiser, "OUTPUT_DIR", out_dir)
    monkeypatch.setattr(synthesiser, "SNIPPETS_PATH", tmp_path / "snippets.json")
    monkeypatch.setattr(synthesiser, "OpenAINarrative", FakeNarrative)
    monkeypatch.setattr(synthesiser.retrieval, "get_snippets", lambda doi, kw: [])  # type: ignore

    code = synthesiser.main(["--drug", "DrugX"])
    assert code == 0
    out_file = out_dir / "review_DrugX.md"
    assert out_file.exists()
    assert out_file.read_text() == "# Review"
    snippets_path = tmp_path / "snippets.json"
    assert snippets_path.exists()
    assert orjson.loads(snippets_path.read_bytes()) == []
