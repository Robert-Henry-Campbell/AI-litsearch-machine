from __future__ import annotations

from pathlib import Path

import pytest

from ingest.list_pdfs import list_pdfs


def test_list_pdfs_creates_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dir_path = tmp_path / "pdfs"
    monkeypatch.setattr("ingest.list_pdfs.DATA_DIR", dir_path)

    result = list_pdfs()

    assert result == []
    assert dir_path.exists()


def test_list_pdfs_returns_filenames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dir_path = tmp_path / "pdfs"
    monkeypatch.setattr("ingest.list_pdfs.DATA_DIR", dir_path)
    dir_path.mkdir()

    (dir_path / "a.pdf").write_text("a")
    (dir_path / "b.pdf").write_text("b")
    (dir_path / "note.txt").write_text("not a pdf")

    result = list_pdfs()

    assert sorted(result) == ["a.pdf", "b.pdf"]
