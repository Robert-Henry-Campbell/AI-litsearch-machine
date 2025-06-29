import logging
from datetime import datetime
from pathlib import Path

import pytest

import aggregate


def test_log_error_writes_file_and_logs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    log_path = tmp_path / "err.log"
    monkeypatch.setattr(aggregate, "ERROR_LOG", log_path)

    with caplog.at_level(logging.ERROR):
        aggregate._log_error(tmp_path / "bad.json", ValueError("boom"))

    assert log_path.exists()
    content = log_path.read_text()
    assert "bad.json" in content
    assert "boom" in content
    assert "Invalid JSON in file" in caplog.text


def test_backup_master_creates_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    master = tmp_path / "master.json"
    master.write_text("old")
    monkeypatch.setattr(aggregate, "MASTER_PATH", master)
    history = tmp_path / "history"
    monkeypatch.setattr(aggregate, "HISTORY_DIR", history)

    class DummyDT:
        @classmethod
        def utcnow(cls) -> datetime:
            return datetime(2024, 1, 2, 3, 4, 5)

    monkeypatch.setattr(aggregate, "datetime", DummyDT)

    backup = aggregate._backup_master()
    expected = history / "master_20240102T030405.json"
    assert backup == expected
    assert expected.exists()
    assert expected.read_text() == "old"


def test_backup_master_returns_none_when_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(aggregate, "MASTER_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(aggregate, "HISTORY_DIR", tmp_path / "history")

    assert aggregate._backup_master() is None
    assert not (tmp_path / "history").exists()
