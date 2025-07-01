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
    monkeypatch.setattr(retrieval, "INDEX_PATH", tmp_path / "missing.faiss")

    result = retrieval.get_snippets("10.1/abc", "mendelian", method="text")
    assert result
    assert any("Page 1" in s for s in result)


def test_no_matches(tmp_path: Path, monkeypatch) -> None:
    text_dir = tmp_path / "text"
    text_dir.mkdir()
    create_text_file(text_dir, "10.2/xyz")
    monkeypatch.setattr(retrieval, "TEXT_DIR", text_dir)
    monkeypatch.setattr(retrieval, "INDEX_PATH", tmp_path / "missing.faiss")

    result = retrieval.get_snippets("10.2/xyz", "unrelated", method="text")
    assert result == []


def test_embedding_snippets(tmp_path: Path, monkeypatch) -> None:
    text_dir = tmp_path / "text"
    text_dir.mkdir()
    file_path = create_text_file(text_dir, "10.3/emb")
    index_path = tmp_path / "index.faiss"
    from agent2.openai_index import build_openai_index

    monkeypatch.setattr(
        "agent2.openai_index.embed_chunks",
        lambda chunks, model="m": [[0.1] * 2 for _ in chunks],
    )
    build_openai_index([file_path], index_path, model="m")
    monkeypatch.setattr(retrieval, "TEXT_DIR", text_dir)
    monkeypatch.setattr(retrieval, "INDEX_PATH", index_path)

    result = retrieval.get_snippets("10.3/emb", "mendelian", k=1, method="faiss")
    assert result
    assert "mendelian" in result[0].lower()
