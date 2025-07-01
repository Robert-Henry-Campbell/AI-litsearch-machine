from pathlib import Path
import orjson

from agent2.vector_index import build_vector_index, query_index


def create_text_file(dir_path: Path, doi: str, text: str) -> Path:
    path = dir_path / f"{doi.replace('/', '_')}.json"
    data = {"pages": [{"page": 1, "text": text}]}
    path.write_bytes(orjson.dumps(data))
    return path


def test_build_and_query(tmp_path: Path) -> None:
    text_dir = tmp_path / "text"
    text_dir.mkdir()
    file_path = create_text_file(
        text_dir, "10.1/abc", "Mendelian randomization study results"
    )
    index_path = tmp_path / "index.faiss"
    build_vector_index([file_path], index_path)
    results = query_index("10.1/abc", "Mendelian", k=1, index_path=index_path)
    assert results
    assert "Mendelian".lower() in results[0]["text"].lower()
