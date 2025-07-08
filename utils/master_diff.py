from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from utils.master_loader import ensure_compat


@dataclass
class DiffResult:
    value1: Any
    value2: Any
    status: str


def generate_diffs(
    master1: list[dict], master2: list[dict], key: str = "doi"
) -> Dict[Tuple[str, str], DiffResult]:
    """Return field-level diffs between ``master1`` and ``master2``.

    ``master1`` and ``master2`` must contain the same set of records for
    ``key``. Each pair of values is compared and stored under a tuple of the
    record key and field name.
    """
    ensure_compat(master1, master2, key)

    recs1 = {rec.get(key): rec for rec in master1}
    recs2 = {rec.get(key): rec for rec in master2}

    diffs: Dict[Tuple[str, str], DiffResult] = {}
    for rec_key in recs1:
        r1 = recs1[rec_key]
        r2 = recs2[rec_key]
        fields = sorted(set(r1) | set(r2))
        for field in fields:
            v1 = r1.get(field)
            v2 = r2.get(field)
            status = "match" if v1 == v2 else "diff"
            diffs[(rec_key, field)] = DiffResult(v1, v2, status)
    return diffs
