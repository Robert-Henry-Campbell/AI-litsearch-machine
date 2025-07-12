from __future__ import annotations

from datetime import datetime
from pathlib import Path
import orjson
import pytest

import agent3.compare_masters as compare_masters
import cli.resolve_conflicts as resolver
import agent3.write_validated_master as writer


class DummyDT:
    @classmethod
    def utcnow(cls) -> datetime:
        return datetime(2024, 1, 2, 3, 4, 5)


MASTER_V1 = Path(__file__).parent / "master_v1.json"
MASTER_V2 = Path(__file__).parent / "master_v2.json"


def test_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(compare_masters, "is_conflict", lambda *_a, **_k: True)
    cmp_out = tmp_path / "cmp.json"
    code = compare_masters.main(
        [
            str(MASTER_V1),
            str(MASTER_V2),
            "--out",
            str(cmp_out),
        ]
    )
    assert code == 0
    assert cmp_out.exists()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(resolver, "datetime", DummyDT)
    res_code = resolver.main([str(cmp_out), "--auto", "2"])
    assert res_code == 0
    res_path = tmp_path / "resolution_20240102_030405.json"
    assert res_path.exists()

    out_dir = tmp_path / "out"
    monkeypatch.setattr(writer, "datetime", DummyDT)
    write_code = writer.main(
        [
            str(MASTER_V1),
            str(MASTER_V2),
            str(res_path),
            "--out_dir",
            str(out_dir),
            "--drug",
            "DrugY",
        ]
    )
    assert write_code == 0
    master_path = out_dir / "master_DrugY_cleaned_20240102_030405.json"
    meta_path = out_dir / "master_validated_meta_20240102_030405.json"
    data = orjson.loads(master_path.read_bytes())
    assert data == [
        {"doi": "1", "title": "A2", "year": 2001},
        {"doi": "2", "title": "B2", "year": 2003},
    ]
    meta = orjson.loads(meta_path.read_bytes())
    assert meta == {
        "total_fields": 6,
        "matches": 3,
        "conflicts": 3,
        "v1_chosen": 0,
        "v2_chosen": 3,
        "manual_edits": 0,
    }
    assert (
        cmp_out.exists()
        and res_path.exists()
        and master_path.exists()
        and meta_path.exists()
    )
