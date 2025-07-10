from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
import orjson

from utils.logger import get_logger
from utils.master_loader import load_master
from agent3.json_matcher import fuzzy_match_titles
from agent3.openai_validator import is_conflict


OUT_DIR = Path("data/validation")
logger = get_logger(__name__)


def _pair_records(master1: list[dict], master2: list[dict]) -> list[tuple[dict, dict]]:
    pairs: list[tuple[dict, dict]] = []
    remaining = list(master2)
    for rec1 in master1:
        doi1 = rec1.get("doi")
        title1 = rec1.get("title", "")
        match_idx: int | None = None
        if doi1:
            for i, rec2 in enumerate(remaining):
                if rec2.get("doi") == doi1:
                    match_idx = i
                    break
        if match_idx is None:
            candidates: list[tuple[int, int]] = []
            for i, rec2 in enumerate(remaining):
                title2 = rec2.get("title", "")
                score = fuzzy_match_titles(title1, title2)
                if score is not None:
                    candidates.append((score, i))
            if candidates:
                doi_candidates = [
                    c for c in candidates if doi1 and remaining[c[1]].get("doi") == doi1
                ]
                if doi_candidates:
                    match_idx = doi_candidates[0][1]
                else:
                    match_idx = max(candidates, key=lambda t: t[0])[1]
        if match_idx is not None:
            rec2 = remaining.pop(match_idx)
            pairs.append((rec1, rec2))
        else:
            logger.warning("No match found for record %s", doi1 or title1)
    return pairs


def compare(master1_path: Path, master2_path: Path, out_path: Path) -> list[dict]:
    """Compare *master1_path* and *master2_path* and write results to *out_path*."""
    m1 = load_master(master1_path)
    m2 = load_master(master2_path)
    pairs = _pair_records(m1, m2)
    results: list[dict] = []
    for rec1, rec2 in pairs:
        key = rec1.get("doi") or rec2.get("doi") or rec1.get("title")
        fields = sorted(set(rec1) | set(rec2))
        for field in fields:
            v1 = rec1.get(field)
            v2 = rec2.get(field)
            if v1 == v2:
                continue
            conflict = is_conflict(str(v1), str(v2), field)
            results.append(
                {
                    "key": key,
                    "field": field,
                    "v1": v1,
                    "v2": v2,
                    "conflict": conflict,
                }
            )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(orjson.dumps(results, option=orjson.OPT_INDENT_2))
    logger.info(
        "Compared %s fields, %s conflicts found",
        len(results),
        sum(1 for r in results if r["conflict"]),
    )
    return results


def main(argv: list[str] | None = None) -> int:
    parser = ArgumentParser(description="Detect conflicts between two master files.")
    parser.add_argument("master_v1", help="Path to first master JSON")
    parser.add_argument("master_v2", help="Path to second master JSON")
    parser.add_argument("--out", help="Output JSON path")
    args = parser.parse_args(argv)

    if args.out:
        out_path = Path(args.out)
    else:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = OUT_DIR / f"comparison_{timestamp}.json"

    compare(Path(args.master_v1), Path(args.master_v2), out_path)
    print(f"Results written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
