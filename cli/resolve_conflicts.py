from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import List

import orjson


def _load_temp() -> tuple[Path | None, List[dict]]:
    files = sorted(Path(".").glob(".tmp_resolution_*.json"))
    if files:
        tmp_file = files[0]
        data = orjson.loads(tmp_file.read_bytes())
        return tmp_file, data
    return None, []


def _write_temp(path: Path, data: List[dict]) -> None:
    path.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))


def _prompt(entry: dict, index: int, total: int) -> tuple[str, str]:
    print(f"[{index}/{total}] Field: {entry['field']}")
    print(f"1) {entry['v1']}")
    print(f"2) {entry['v2']}")
    print("M) Manual entry")
    while True:
        choice = input("Choice: ").strip()
        if choice in {"1", "2", "M", "m"}:
            break
        print("Enter 1, 2, or M")
    if choice == "1":
        return entry["v1"], "v1"
    if choice == "2":
        return entry["v2"], "v2"
    value = input("Enter value: ")
    return value, "manual"


def resolve(comparison_path: Path, *, auto: str | None = None) -> Path:
    data = orjson.loads(comparison_path.read_bytes())
    conflicts = [d for d in data if d.get("conflict")]

    tmp_file, progress = _load_temp()
    if tmp_file is None:
        tmp_file = Path(f".tmp_resolution_{os.getpid()}.json")

    index = len(progress)
    try:
        for i in range(index, len(conflicts)):
            entry = conflicts[i]
            if auto in {"1", "2"}:
                value = entry[f"v{auto}"]
                rtype = f"v{auto}"
            else:
                value, rtype = _prompt(entry, i + 1, len(conflicts))
            progress.append(
                {
                    "key": entry["key"],
                    "field": entry["field"],
                    "resolved_value": value,
                    "resolution_type": rtype,
                }
            )
            _write_temp(tmp_file, progress)
    except KeyboardInterrupt:
        print("\nInterrupted. Progress saved to", tmp_file)
        raise SystemExit(1)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = comparison_path.parent / f"resolution_{timestamp}.json"
    out_path.write_bytes(orjson.dumps(progress, option=orjson.OPT_INDENT_2))
    tmp_file.unlink(missing_ok=True)
    print(f"Resolution written to {out_path}")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve conflicts interactively")
    parser.add_argument("comparison", help="Path to comparison JSON")
    parser.add_argument(
        "--auto",
        choices=["1", "2"],
        help="Automatically choose version 1 or 2 for all conflicts",
    )
    args = parser.parse_args(argv)
    resolve(Path(args.comparison), auto=args.auto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
