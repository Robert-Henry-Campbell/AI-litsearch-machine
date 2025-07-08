from pathlib import Path

import orjson
import pytest

from utils.master_loader import ensure_compat, load_master


FIXTURES = Path(__file__).parents[1] / "fixtures" / "masters"


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


def test_load_master_fixture() -> None:
    """Load records from bundled fixture file."""
    path = FIXTURES / "master_a.json"
    records = load_master(path)
    assert isinstance(records, list)
    assert records[0]["doi"] == "a"


def test_incompatible_length_using_fixtures() -> None:
    """Different number of records triggers error."""
    m1 = load_master(FIXTURES / "master_a.json")
    m2 = m1 + [{"doi": "c"}]
    with pytest.raises(ValueError):
        ensure_compat(m1, m2)


def test_missing_primary_key() -> None:
    """A record missing the primary key fails compatibility check."""
    m1 = load_master(FIXTURES / "master_a.json")
    m2 = [{"title": "First"}, *m1[1:]]
    with pytest.raises(ValueError):
        ensure_compat(m1, m2)
