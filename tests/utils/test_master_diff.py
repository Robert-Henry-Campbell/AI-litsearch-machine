from pathlib import Path

import orjson

from utils.master_diff import generate_diffs


FIXTURES = Path(__file__).parents[1] / "fixtures" / "masters"


def load_json(name: str) -> list[dict]:
    return orjson.loads((FIXTURES / name).read_bytes())


def test_all_match() -> None:
    m1 = [{"doi": "1", "title": "A"}]
    m2 = [{"doi": "1", "title": "A"}]
    diffs = generate_diffs(m1, m2)
    assert list(diffs.keys()) == [("1", "doi"), ("1", "title")]
    assert all(res.status == "match" for res in diffs.values())


def test_all_diff() -> None:
    m1 = [{"doi": "1", "title": "A"}]
    m2 = [{"doi": "1", "title": "B"}]
    diffs = generate_diffs(m1, m2)
    assert diffs[("1", "title")].status == "diff"
    assert diffs[("1", "title")].value1 == "A"
    assert diffs[("1", "title")].value2 == "B"


def test_mixed_fields() -> None:
    m1 = [{"doi": "1", "title": "A", "extra": 1}]
    m2 = [{"doi": "1", "title": "A", "extra": 2}]
    diffs = generate_diffs(m1, m2)
    assert diffs[("1", "title")].status == "match"
    assert diffs[("1", "extra")].status == "diff"


def test_fixture_all_match() -> None:
    m1 = load_json("master_a.json")
    m2 = load_json("master_a.json")
    diffs = generate_diffs(m1, m2)
    assert all(d.status == "match" for d in diffs.values())


def test_fixture_all_diff() -> None:
    m1 = load_json("master_a.json")
    m2 = load_json("master_b.json")
    diffs = generate_diffs(m1, m2)
    statuses = {d.status for d in diffs.values()}
    assert statuses == {"match", "diff"}
    assert diffs[("b", "title")].status == "diff"


def test_numeric_rounding_edge() -> None:
    m1 = [{"doi": "1", "val": 1.2345}]
    m2 = [{"doi": "1", "val": 1.2346}]
    diff = generate_diffs(m1, m2)[("1", "val")]
    assert diff.status == "diff"
    assert round(diff.value1, 2) == round(diff.value2, 2)
