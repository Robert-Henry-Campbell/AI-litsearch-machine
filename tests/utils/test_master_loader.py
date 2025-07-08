from pathlib import Path

import orjson
import pytest

from utils.master_loader import load_master, ensure_compat


def create_master(path: Path, records: list[dict]) -> None:
    path.write_bytes(orjson.dumps(records))


def test_load_master(tmp_path: Path) -> None:
    records = [{"doi": "a"}, {"doi": "b"}]
    path = tmp_path / "master.json"
    create_master(path, records)
    assert load_master(path) == records


def test_load_master_not_list(tmp_path: Path) -> None:
    path = tmp_path / "master.json"
    path.write_bytes(orjson.dumps({"doi": "x"}))
    with pytest.raises(ValueError):
        load_master(path)


def test_ensure_compat_ok() -> None:
    list1 = [{"doi": "1"}, {"doi": "2"}]
    list2 = [{"doi": "2"}, {"doi": "1"}]
    ensure_compat(list1, list2)


def test_ensure_compat_length_mismatch() -> None:
    list1 = [{"doi": "1"}]
    list2 = [{"doi": "1"}, {"doi": "2"}]
    with pytest.raises(ValueError):
        ensure_compat(list1, list2)


def test_ensure_compat_key_mismatch() -> None:
    list1 = [{"doi": "1"}, {"doi": "2"}]
    list2 = [{"doi": "1"}, {"doi": "3"}]
    with pytest.raises(ValueError):
        ensure_compat(list1, list2)
