from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
import orjson

from utils.logger import get_logger
from utils.master_loader import load_master
from utils.master_diff import generate_diffs
from agent3.openai_validator import is_conflict


OUT_DIR = Path("data/validation")
logger = get_logger(__name__)


def compare(master1_path: Path, master2_path: Path, out_path: Path) -> list[dict]:
    """Compare *master1_path* and *master2_path* and write results to *out_path*."""
    m1 = load_master(master1_path)
    m2 = load_master(master2_path)
    diffs = generate_diffs(m1, m2)
    results: list[dict] = []
    for (key, field), diff in diffs.items():
        if diff.status != "diff":
            continue
        conflict = is_conflict(str(diff.value1), str(diff.value2), field)
        results.append(
            {
                "key": key,
                "field": field,
                "v1": diff.value1,
                "v2": diff.value2,
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
