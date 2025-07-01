from pathlib import Path
import orjson

import agent2.openai_index as oi
import build_embeddings


def create_text_file(dir_path: Path, doi: str, text: str) -> Path:
    path = dir_path / f"{doi.replace('/', '_')}.json"
    data = {"pages": [{"page": 1, "text": text}]}
    path.write_bytes(orjson.dumps(data))
    return path


def test_build_openai_index(tmp_path, monkeypatch):
    text_dir = tmp_path / "text"
    text_dir.mkdir()
    file_path = create_text_file(text_dir, "10.1/abc", "some text")
    index_path = tmp_path / "index.faiss"

    monkeypatch.setattr(
        oi, "embed_chunks", lambda chunks, model="m": [[0.1, 0.2] for _ in chunks]
    )

    oi.build_openai_index([file_path], index_path, model="m")
    assert index_path.exists()
    assert index_path.with_suffix(".meta.json").exists()


def test_cli_main(tmp_path, monkeypatch):
    text_dir = tmp_path / "text"
    text_dir.mkdir()
    (text_dir / "a.json").write_text("{}")

    calls = {}

    def fake_build(paths, index_path, model="x"):
        calls["count"] = len(paths)
        calls["index"] = index_path
        calls["model"] = model

    monkeypatch.setattr("build_embeddings.build_openai_index", fake_build)

    code = build_embeddings.main(["--base_dir", str(tmp_path), "--model", "m"])

    assert code == 0
    assert calls == {
        "count": 1,
        "index": Path(tmp_path / "index.faiss"),
        "model": "m",
    }
