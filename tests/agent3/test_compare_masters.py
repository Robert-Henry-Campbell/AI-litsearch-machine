from __future__ import annotations

import sys
import types
from pathlib import Path
import orjson

# Stub out openai_validator before importing module
fake_validator = types.ModuleType("agent3.openai_validator")
fake_validator.is_conflict = lambda v1, v2, field: True
sys.modules["agent3.openai_validator"] = fake_validator

from agent3 import compare_masters  # noqa: E402

sys.modules.pop("agent3.openai_validator")


def create_master(path: Path, records: list[dict]) -> None:
    path.write_bytes(orjson.dumps(records))


def test_compare_cli(tmp_path: Path):
    m1_path = tmp_path / "m1.json"
    m2_path = tmp_path / "m2.json"
    create_master(m1_path, [{"doi": "1", "title": "A"}])
    create_master(m2_path, [{"doi": "1", "title": "B"}])

    out_path = tmp_path / "out.json"
    code = compare_masters.main([str(m1_path), str(m2_path), "--out", str(out_path)])
    assert code == 0
    data = orjson.loads(out_path.read_bytes())
    assert data == [
        {"key": "1", "field": "title", "v1": "A", "v2": "B", "conflict": True}
    ]
