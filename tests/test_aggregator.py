import orjson
from datetime import datetime
from pathlib import Path
import pytest

import aggregate
from schemas.metadata import PaperMetadata


def create_meta_file(dir_path: Path, name: str) -> None:
    data = PaperMetadata(title=name).model_dump()
    (dir_path / f"{name}.json").write_bytes(orjson.dumps(data))


def test_successful_aggregation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    create_meta_file(meta_dir, "a")
    create_meta_file(meta_dir, "b")

    monkeypatch.setattr(aggregate, "META_DIR", meta_dir)
    master = tmp_path / "master.json"
    monkeypatch.setattr(aggregate, "MASTER_PATH", master)
    history = tmp_path / "history"
    monkeypatch.setattr(aggregate, "HISTORY_DIR", history)

    records, skipped, backup = aggregate.aggregate_metadata()

    assert len(records) == 2
    assert skipped == 0
    assert backup is None
    assert master.exists()
    data = orjson.loads(master.read_bytes())
    assert len(data) == 2


def test_invalid_json_handling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    create_meta_file(meta_dir, "valid")
    (meta_dir / "bad.json").write_text("{invalid}")

    monkeypatch.setattr(aggregate, "META_DIR", meta_dir)
    master = tmp_path / "master.json"
    monkeypatch.setattr(aggregate, "MASTER_PATH", master)
    history = tmp_path / "history"
    monkeypatch.setattr(aggregate, "HISTORY_DIR", history)
    log_path = tmp_path / "err.log"
    monkeypatch.setattr(aggregate, "ERROR_LOG", log_path)

    records, skipped, backup = aggregate.aggregate_metadata()

    assert len(records) == 1
    assert skipped == 1
    assert backup is None
    assert master.exists()
    assert log_path.exists()
    assert "bad.json" in log_path.read_text()


def test_backup_creation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    create_meta_file(meta_dir, "only")

    monkeypatch.setattr(aggregate, "META_DIR", meta_dir)
    master = tmp_path / "master.json"
    master.write_text("old")
    monkeypatch.setattr(aggregate, "MASTER_PATH", master)
    history = tmp_path / "history"
    monkeypatch.setattr(aggregate, "HISTORY_DIR", history)

    class DummyDT:
        @classmethod
        def utcnow(cls) -> datetime:
            return datetime(2024, 5, 15, 13, 45, 0)

    monkeypatch.setattr(aggregate, "datetime", DummyDT)

    records, skipped, backup = aggregate.aggregate_metadata()

    assert skipped == 0
    expected = history / "master_20240515T134500.json"
    assert backup == expected
    assert expected.exists()
    assert expected.read_text() == "old"
