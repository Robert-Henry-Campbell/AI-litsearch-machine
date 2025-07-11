from __future__ import annotations

from datetime import datetime
from pathlib import Path
import orjson

from agent3 import write_validated_master


def create_master(path: Path, records: list[dict]) -> None:
    path.write_bytes(orjson.dumps(records))


def test_cli(tmp_path: Path, monkeypatch) -> None:
    m1 = [
        {"doi": "1", "title": "A", "year": 2023},
        {"doi": "2", "title": "B", "year": 2020},
    ]
    m2 = [
        {"doi": "1", "title": "A2", "year": 2023},
        {"doi": "2", "title": "B", "year": 2021},
    ]
    m1_path = tmp_path / "m1.json"
    m2_path = tmp_path / "m2.json"
    create_master(m1_path, m1)
    create_master(m2_path, m2)

    resolution = [
        {"key": "1", "field": "title", "resolved_value": "A2", "resolution_type": "v2"},
        {"key": "2", "field": "year", "resolved_value": 2021, "resolution_type": "v2"},
    ]
    res_path = tmp_path / "res.json"
    res_path.write_bytes(orjson.dumps(resolution))

    out_dir = tmp_path / "out"

    class DummyDT:
        @classmethod
        def utcnow(cls) -> datetime:
            return datetime(2024, 1, 2, 3, 4, 5)

    monkeypatch.setattr(write_validated_master, "datetime", DummyDT)

    code = write_validated_master.main(
        [
            str(m1_path),
            str(m2_path),
            str(res_path),
            "--out_dir",
            str(out_dir),
            "--drug",
            "DrugX",
        ]
    )
    assert code == 0

    master_path = out_dir / "master_DrugX_cleaned_20240102_030405.json"
    meta_path = out_dir / "master_validated_meta_20240102_030405.json"

    data = orjson.loads(master_path.read_bytes())
    assert data == [
        {"doi": "1", "title": "A2", "year": 2023},
        {"doi": "2", "title": "B", "year": 2021},
    ]

    meta = orjson.loads(meta_path.read_bytes())
    assert meta == {
        "total_fields": 6,
        "matches": 4,
        "conflicts": 2,
        "v1_chosen": 0,
        "v2_chosen": 2,
        "manual_edits": 0,
    }


class DummyDT:
    @classmethod
    def utcnow(cls) -> datetime:
        return datetime(2024, 1, 2, 3, 4, 5)


def test_merge_defaults_to_v1(tmp_path: Path, monkeypatch) -> None:
    m1 = [{"doi": "1", "title": "A", "year": 2020}]
    m2 = [{"doi": "1", "title": "B", "year": 2021}]
    m1_path = tmp_path / "m1.json"
    m2_path = tmp_path / "m2.json"
    create_master(m1_path, m1)
    create_master(m2_path, m2)

    res_path = tmp_path / "res.json"
    res_path.write_bytes(b"[]")

    out_dir = tmp_path / "out"
    monkeypatch.setattr(write_validated_master, "datetime", DummyDT)
    master_path, meta_path = write_validated_master.merge_masters(
        m1_path, m2_path, res_path, out_dir
    )

    data = orjson.loads(master_path.read_bytes())
    assert data == [{"doi": "1", "title": "A", "year": 2020}]
    meta = orjson.loads(meta_path.read_bytes())
    assert meta == {
        "total_fields": 3,
        "matches": 1,
        "conflicts": 0,
        "v1_chosen": 0,
        "v2_chosen": 0,
        "manual_edits": 0,
    }


def test_merge_manual_resolution(tmp_path: Path, monkeypatch) -> None:
    m1 = [{"doi": "1", "title": "A", "year": 2020}]
    m2 = [{"doi": "1", "title": "B", "year": 2021}]
    m1_path = tmp_path / "m1.json"
    m2_path = tmp_path / "m2.json"
    create_master(m1_path, m1)
    create_master(m2_path, m2)

    resolution = [
        {
            "key": "1",
            "field": "title",
            "resolved_value": "B",
            "resolution_type": "v2",
        },
        {
            "key": "1",
            "field": "year",
            "resolved_value": 2020,
            "resolution_type": "manual",
        },
    ]
    res_path = tmp_path / "res.json"
    res_path.write_bytes(orjson.dumps(resolution))

    out_dir = tmp_path / "out"
    monkeypatch.setattr(write_validated_master, "datetime", DummyDT)
    master_path, meta_path = write_validated_master.merge_masters(
        m1_path, m2_path, res_path, out_dir
    )

    data = orjson.loads(master_path.read_bytes())
    assert data == [{"doi": "1", "title": "B", "year": 2020}]
    meta = orjson.loads(meta_path.read_bytes())
    assert meta == {
        "total_fields": 3,
        "matches": 1,
        "conflicts": 2,
        "v1_chosen": 0,
        "v2_chosen": 1,
        "manual_edits": 1,
    }


def test_merge_handles_none_doi(tmp_path: Path, monkeypatch) -> None:
    m1 = [{"doi": None, "title": "A", "year": 2020}]
    m2 = [{"doi": None, "title": "B", "year": 2021}]
    m1_path = tmp_path / "m1.json"
    m2_path = tmp_path / "m2.json"
    create_master(m1_path, m1)
    create_master(m2_path, m2)

    res_path = tmp_path / "res.json"
    res_path.write_bytes(b"[]")

    out_dir = tmp_path / "out"
    monkeypatch.setattr(write_validated_master, "datetime", DummyDT)
    master_path, _meta_path = write_validated_master.merge_masters(
        m1_path, m2_path, res_path, out_dir
    )

    data = orjson.loads(master_path.read_bytes())
    assert data == [{"title": "A", "year": 2020}]
