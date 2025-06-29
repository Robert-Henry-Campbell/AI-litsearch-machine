from pathlib import Path

import orjson

from aggregate import aggregate_metadata


def create_meta(path: Path, name: str, data: dict) -> None:
    file = path / f"{name}.json"
    file.write_bytes(orjson.dumps(data))


def test_aggregate_creates_master(tmp_path: Path) -> None:
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    create_meta(meta_dir, "a", {"title": "A"})
    master_path = tmp_path / "master.json"
    history_dir = tmp_path / "master_history"

    aggregate_metadata(
        meta_dir=meta_dir, master_path=master_path, history_dir=history_dir
    )
    assert master_path.exists()
    data = orjson.loads(master_path.read_bytes())
    assert data == [
        {
            "title": "A",
            "authors": None,
            "doi": None,
            "pub_date": None,
            "data_sources": None,
            "omics_modalities": None,
            "targets": None,
            "p_threshold": None,
            "ld_r2": None,
        }
    ]


def test_aggregate_backup(tmp_path: Path) -> None:
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    create_meta(meta_dir, "a", {"title": "A"})
    master_path = tmp_path / "master.json"
    history_dir = tmp_path / "master_history"

    aggregate_metadata(
        meta_dir=meta_dir, master_path=master_path, history_dir=history_dir
    )
    first = master_path.read_bytes()

    create_meta(meta_dir, "b", {"title": "B"})
    aggregate_metadata(
        meta_dir=meta_dir, master_path=master_path, history_dir=history_dir
    )

    backups = list(history_dir.glob("master_*.json"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == first
