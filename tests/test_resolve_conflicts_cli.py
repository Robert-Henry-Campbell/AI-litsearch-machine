from __future__ import annotations

from datetime import datetime
from pathlib import Path
import builtins
import orjson
import pytest

import cli.resolve_conflicts as resolver


class DummyDT:
    @classmethod
    def utcnow(cls) -> datetime:
        return datetime(2024, 1, 2, 3, 4, 5)


def create_comparison(path: Path) -> None:
    data = [
        {"key": "a", "field": "title", "v1": "A", "v2": "B", "conflict": True},
        {"key": "a", "field": "year", "v1": 2023, "v2": 2024, "conflict": True},
    ]
    path.write_bytes(orjson.dumps(data))


def test_complete_run(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    cmp_path = tmp_path / "cmp.json"
    create_comparison(cmp_path)

    inputs = iter(["1", "2"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    monkeypatch.setattr(resolver, "datetime", DummyDT)

    code = resolver.main([str(cmp_path)])
    assert code == 0
    out_path = tmp_path / "resolution_20240102_030405.json"
    data = orjson.loads(out_path.read_bytes())
    assert data == [
        {"key": "a", "field": "title", "resolved_value": "A", "resolution_type": "v1"},
        {"key": "a", "field": "year", "resolved_value": 2024, "resolution_type": "v2"},
    ]
    assert not list(tmp_path.glob(".tmp_resolution_*.json"))


def test_resume_after_interrupt(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    cmp_path = tmp_path / "cmp.json"
    create_comparison(cmp_path)

    answers = iter(["1", KeyboardInterrupt()])

    def fake_input(_: str) -> str:
        value = next(answers)
        if isinstance(value, BaseException):
            raise value
        return value

    monkeypatch.setattr(builtins, "input", fake_input)
    monkeypatch.setattr(resolver, "datetime", DummyDT)

    with pytest.raises(SystemExit):
        resolver.main([str(cmp_path)])

    tmp_files = list(tmp_path.glob(".tmp_resolution_*.json"))
    assert len(tmp_files) == 1
    progress = orjson.loads(tmp_files[0].read_bytes())
    assert len(progress) == 1

    # resume
    inputs = iter(["2"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    resolver.main([str(cmp_path)])

    out_path = tmp_path / "resolution_20240102_030405.json"
    data = orjson.loads(out_path.read_bytes())
    assert len(data) == 2
    assert not list(tmp_path.glob(".tmp_resolution_*.json"))
