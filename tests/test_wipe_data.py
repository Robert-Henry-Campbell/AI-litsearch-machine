from __future__ import annotations

from pathlib import Path

import aggregate
from utils import data_wipe


def setup_paths(tmp_path: Path, monkeypatch) -> dict[str, Path]:
    paths = {
        "meta": tmp_path / "meta",
        "text": tmp_path / "text",
        "history": tmp_path / "history",
        "out": tmp_path / "out",
        "master": tmp_path / "master.json",
        "error": tmp_path / "err.log",
        "log": tmp_path / "ingestion.log",
        "pdfs": tmp_path / "pdfs",
    }
    for key in ("meta", "text", "history", "out", "pdfs"):
        (paths[key] / "dummy").parent.mkdir(parents=True, exist_ok=True)
        (paths[key] / "dummy").write_text("x")
    for key in ("master", "error", "log"):
        paths[key].write_text("x")

    monkeypatch.setattr(data_wipe, "META_DIR", paths["meta"])
    monkeypatch.setattr(data_wipe, "TEXT_DIR", paths["text"])
    monkeypatch.setattr(data_wipe, "OUTPUT_DIR", paths["out"])
    monkeypatch.setattr(data_wipe, "LOG_PATH", paths["log"])
    monkeypatch.setattr(data_wipe, "PDF_DIR", paths["pdfs"])

    monkeypatch.setattr(aggregate, "HISTORY_DIR", paths["history"])
    monkeypatch.setattr(aggregate, "MASTER_PATH", paths["master"])
    monkeypatch.setattr(aggregate, "ERROR_LOG", paths["error"])
    return paths


def test_wipe_data(tmp_path: Path, monkeypatch) -> None:
    paths = setup_paths(tmp_path, monkeypatch)

    data_wipe.wipe_data()

    for key in ("meta", "text", "history", "out"):
        assert not paths[key].exists()
    for key in ("master", "error", "log"):
        assert not paths[key].exists()
    assert paths["pdfs"].exists()


def test_wipe_data_with_pdfs(tmp_path: Path, monkeypatch) -> None:
    paths = setup_paths(tmp_path, monkeypatch)

    data_wipe.wipe_data(delete_pdfs=True)

    for key in ("meta", "text", "history", "out", "pdfs"):
        assert not paths[key].exists()
    for key in ("master", "error", "log"):
        assert not paths[key].exists()
