from utils.master_diff import generate_diffs


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
