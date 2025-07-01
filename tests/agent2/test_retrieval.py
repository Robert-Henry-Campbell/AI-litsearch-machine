from __future__ import annotations

from pathlib import Path
import shutil

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


def test_retrieval_cache(tmp_path: Path, monkeypatch) -> None:
    text_dir = tmp_path / "text"
    text_dir.mkdir()
    file_path = create_text_file(text_dir, "10.4/cache")
    index_path = tmp_path / "index.faiss"

    from agent2 import openai_index as oi

    monkeypatch.setattr(
        oi, "embed_chunks", lambda chunks, model="m": [[0.1] * 2 for _ in chunks]
    )
    oi.build_openai_index([file_path], index_path, model="m")

    calls = {"count": 0}

    def fake_embed(chunks, model="m"):
        calls["count"] += 1
        return [[0.1] * 2 for _ in chunks]

    monkeypatch.setattr(oi, "embed_chunks", fake_embed)
    oi.clear_cache()

    monkeypatch.setattr(retrieval, "TEXT_DIR", text_dir)
    monkeypatch.setattr(retrieval, "INDEX_PATH", index_path)

    retrieval.get_snippets("10.4/cache", "mendelian", method="faiss")
    retrieval.get_snippets("10.4/cache", "mendelian", method="faiss")

    assert calls["count"] == 1


def test_build_index_when_missing(tmp_path: Path, monkeypatch) -> None:
    text_dir = tmp_path / "text"
    text_dir.mkdir()
    _ = create_text_file(text_dir, "10.5/new")
    index_path = tmp_path / "index.faiss"

    from agent2 import openai_index as oi

    monkeypatch.setattr(
        oi, "embed_chunks", lambda chunks, model="m": [[0.1] * 2 for _ in chunks]
    )

    monkeypatch.setattr(retrieval, "TEXT_DIR", text_dir)
    monkeypatch.setattr(retrieval, "INDEX_PATH", index_path)
    monkeypatch.setattr(retrieval, "build_openai_index", oi.build_openai_index)

    result = retrieval.get_snippets(
        "10.5/new", "mendelian", method="faiss", embed_model="m"
    )

    assert index_path.exists()
    assert result


def test_embedding_snippets_test_papers(tmp_path: Path, monkeypatch) -> None:
    base_dir = tmp_path / "test_papers"
    pdf_dir = base_dir / "pdfs"
    text_dir = base_dir / "text"
    meta_dir = base_dir / "meta"
    pdf_dir.mkdir(parents=True)
    text_dir.mkdir()
    meta_dir.mkdir()

    for src in Path("data/test_papers/pdfs").glob("*.pdf"):
        shutil.copy(src, pdf_dir / src.name)

    monkeypatch.setattr("extract.pdf_to_text.DATA_DIR", text_dir)

    from extract.pdf_to_text import pdf_to_text
    from agent2.openai_index import build_openai_index

    dois: list[str] = []
    for pdf in sorted(pdf_dir.glob("*.pdf")):
        pdf_to_text(pdf)
        original = text_dir / f"{pdf.stem}.json"
        doi = f"10.1/{pdf.stem}"
        dois.append(doi)
        renamed = text_dir / f"{doi.replace('/', '_')}.json"
        original.rename(renamed)

    index_path = base_dir / "index.faiss"
    monkeypatch.setattr(
        "agent2.openai_index.embed_chunks",
        lambda chunks, model="m": [[0.1] * 2 for _ in chunks],
    )
    build_openai_index(sorted(text_dir.glob("*.json")), index_path, model="m")

    monkeypatch.setattr(retrieval, "TEXT_DIR", text_dir)
    monkeypatch.setattr(retrieval, "INDEX_PATH", index_path)

    result = retrieval.get_snippets(dois[0], "Sample", k=1, method="faiss")
    assert result
    assert "Sample" in result[0]
