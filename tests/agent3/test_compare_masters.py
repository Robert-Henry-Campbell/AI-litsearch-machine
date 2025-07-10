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


def test_compare_skips_matching_fields(tmp_path: Path, monkeypatch) -> None:
    m1_path = tmp_path / "m1.json"
    m2_path = tmp_path / "m2.json"
    create_master(m1_path, [{"doi": "1", "title": "A"}])
    create_master(m2_path, [{"doi": "1", "title": "A"}])

    called = False

    def fake_conflict(v1: str, v2: str, field: str) -> bool:
        nonlocal called
        called = True
        return True

    monkeypatch.setattr(compare_masters, "is_conflict", fake_conflict)

    out_path = tmp_path / "out.json"
    results = compare_masters.compare(m1_path, m2_path, out_path)
    assert results == []
    assert out_path.read_text() == "[]"
    assert called is False


def test_fuzzy_title_match(tmp_path: Path) -> None:
    m1_path = tmp_path / "m1.json"
    m2_path = tmp_path / "m2.json"
    create_master(m1_path, [{"doi": "1", "title": "An Example Title"}])
    create_master(m2_path, [{"doi": "x", "title": "An example title"}])

    out_path = tmp_path / "out.json"
    results = compare_masters.compare(m1_path, m2_path, out_path)
    assert {
        "key": "1",
        "field": "doi",
        "v1": "1",
        "v2": "x",
        "conflict": True,
    } in results
    assert {
        "key": "1",
        "field": "title",
        "v1": "An Example Title",
        "v2": "An example title",
        "conflict": True,
    } in results


def test_doi_tie_breaker(tmp_path: Path) -> None:
    m1_path = tmp_path / "m1.json"
    m2_path = tmp_path / "m2.json"
    create_master(m1_path, [{"doi": "1", "title": "Alpha Beta"}])
    create_master(
        m2_path,
        [
            {"doi": "2", "title": "Alpha Beta"},
            {"doi": "1", "title": "Alpha Beta Updated"},
        ],
    )

    out_path = tmp_path / "out.json"
    results = compare_masters.compare(m1_path, m2_path, out_path)
    assert {
        "key": "1",
        "field": "title",
        "v1": "Alpha Beta",
        "v2": "Alpha Beta Updated",
        "conflict": True,
    } in results
