from __future__ import annotations

from pathlib import Path

import orjson

import agent2.retrieval as retrieval


def create_text_file(dir_path: Path, doi: str) -> Path:
    pages = [
        {"page": 1, "text": "This study uses Mendelian randomization techniques."},
        {"page": 2, "text": "Further analysis is presented here."},
    ]
    data = {"pages": pages}
    path = dir_path / f"{doi.replace('/', '_')}.json"
    path.write_bytes(orjson.dumps(data))
    return path


def test_successful_snippet_retrieval(tmp_path: Path, monkeypatch) -> None:
    text_dir = tmp_path / "text"
    text_dir.mkdir()
    create_text_file(text_dir, "10.1/abc")
    monkeypatch.setattr(retrieval, "TEXT_DIR", text_dir)

    result = retrieval.get_snippets("10.1/abc", "mendelian")
    assert result
    assert any("Page 1" in s for s in result)


def test_no_matches(tmp_path: Path, monkeypatch) -> None:
    text_dir = tmp_path / "text"
    text_dir.mkdir()
    create_text_file(text_dir, "10.2/xyz")
    monkeypatch.setattr(retrieval, "TEXT_DIR", text_dir)

    result = retrieval.get_snippets("10.2/xyz", "unrelated")
    assert result == []
