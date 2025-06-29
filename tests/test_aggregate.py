from datetime import datetime
from pathlib import Path

import orjson
import pytest

import aggregate
from schemas.metadata import PaperMetadata


def create_meta_file(dir_path: Path, name: str) -> None:
    data = PaperMetadata(title=name).model_dump()
    (dir_path / f"{name}.json").write_bytes(orjson.dumps(data))


def test_aggregate_creates_master(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    create_meta_file(meta_dir, "a")
    create_meta_file(meta_dir, "b")
    monkeypatch.setattr(aggregate, "META_DIR", meta_dir)
    master_path = tmp_path / "master.json"
    monkeypatch.setattr(aggregate, "MASTER_PATH", master_path)
    history_dir = tmp_path / "history"
    monkeypatch.setattr(aggregate, "HISTORY_DIR", history_dir)

    records, skipped, backup = aggregate.aggregate_metadata()
    assert skipped == 0
    assert backup is None

    assert master_path.exists()
    data = orjson.loads(master_path.read_bytes())
    assert len(data) == 2
    assert not history_dir.exists()


def test_backup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    create_meta_file(meta_dir, "c")
    monkeypatch.setattr(aggregate, "META_DIR", meta_dir)
    master_path = tmp_path / "master.json"
    master_path.write_text("old")
    monkeypatch.setattr(aggregate, "MASTER_PATH", master_path)
    history_dir = tmp_path / "history"
    monkeypatch.setattr(aggregate, "HISTORY_DIR", history_dir)

    class DummyDT:
        @classmethod
        def utcnow(cls) -> datetime:
            return datetime(2024, 5, 15, 13, 45, 0)

    monkeypatch.setattr(aggregate, "datetime", DummyDT)

    records, skipped, backup = aggregate.aggregate_metadata()
    assert skipped == 0
    assert backup == history_dir / "master_20240515T134500.json"
    assert backup.exists()
    assert backup.read_text() == "old"


def test_invalid_json_logs_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    valid = PaperMetadata(title="t").model_dump()
    (meta_dir / "valid.json").write_bytes(orjson.dumps(valid))
    (meta_dir / "bad.json").write_text("{invalid}")

    monkeypatch.setattr(aggregate, "META_DIR", meta_dir)
    master_path = tmp_path / "master.json"
    monkeypatch.setattr(aggregate, "MASTER_PATH", master_path)
    history_dir = tmp_path / "history"
    monkeypatch.setattr(aggregate, "HISTORY_DIR", history_dir)
    log_path = tmp_path / "err.log"
    monkeypatch.setattr(aggregate, "ERROR_LOG", log_path)

    records, skipped, backup = aggregate.aggregate_metadata()
    assert skipped == 1
    assert backup is None

    assert master_path.exists()
    data = orjson.loads(master_path.read_bytes())
    assert len(data) == 1
    assert log_path.exists()
    assert "bad.json" in log_path.read_text()
