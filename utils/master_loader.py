from __future__ import annotations

from pathlib import Path
from typing import List

import orjson


def load_master(path: str | Path) -> List[dict]:
    """Return metadata records from the master JSON file at ``path``.

    The file must contain a JSON array where each element is a dictionary
    of paper metadata keyed by values like ``doi``.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    data = orjson.loads(file_path.read_bytes())
    if not isinstance(data, list):
        raise ValueError("master file must contain a list")
    return data


def ensure_compat(list1: List[dict], list2: List[dict], key: str = "doi") -> None:
    """Validate that ``list1`` and ``list2`` can be compared 1-to-1.

    Compatibility requires the same length and identical sets of values
    for ``key``. A ``ValueError`` is raised if they differ.
    """
    if len(list1) != len(list2):
        raise ValueError("master lengths differ")
    keys1 = {rec.get(key) for rec in list1}
    keys2 = {rec.get(key) for rec in list2}
    if keys1 != keys2:
        raise ValueError(f"master {key} sets differ")
    return None
