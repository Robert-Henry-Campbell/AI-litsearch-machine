from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import agent3.compare_masters as compare_masters
import cli.resolve_conflicts as resolver
import agent3.write_validated_master as writer


def main(argv: list[str] | None = None) -> int:
    """Run the full master validation workflow."""
    parser = argparse.ArgumentParser(description="Validate two master JSON files")
    parser.add_argument("master_v1", help="Path to master_v1.json")
    parser.add_argument("master_v2", help="Path to master_v2.json")
    parser.add_argument(
        "--auto",
        choices=["1", "2"],
        help="Automatically choose version 1 or 2 for all conflicts",
    )
    parser.add_argument("--out_dir", default="data/validation", help="Output directory")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    cmp_path = out_dir / f"comparison_{timestamp}.json"

    compare_masters.compare(Path(args.master_v1), Path(args.master_v2), cmp_path)
    res_path = resolver.resolve(cmp_path, auto=args.auto)
    writer.merge_masters(Path(args.master_v1), Path(args.master_v2), res_path, out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
