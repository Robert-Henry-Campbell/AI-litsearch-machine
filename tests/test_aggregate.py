from pathlib import Path

import orjson

from aggregate import aggregate
from schemas.metadata import PaperMetadata


def write_json(path: Path, data) -> None:  # data may be dict or other
    if isinstance(data, str):
        path.write_text(data)
    else:
        path.write_bytes(orjson.dumps(data))


def test_aggregate(monkeypatch, tmp_path: Path) -> None:
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    monkeypatch.setattr("aggregate.META_DIR", meta_dir)
    out_path = tmp_path / "master.json"
    monkeypatch.setattr("aggregate.OUT_PATH", out_path)

    valid_data = {"title": "Example Title"}
    write_json(meta_dir / "valid.json", valid_data)
    write_json(meta_dir / "bad.json", "not json")
    write_json(meta_dir / "invalid.json", [1, 2, 3])

    results = aggregate()

    assert out_path.exists()
    out = orjson.loads(out_path.read_bytes())
    assert out == [PaperMetadata.model_validate(valid_data).model_dump()]
    assert len(results) == 1
