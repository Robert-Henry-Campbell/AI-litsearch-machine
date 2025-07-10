from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
import orjson

from utils.master_loader import load_master, ensure_compat
from utils.master_diff import generate_diffs

OUT_DIR = Path("data/validation")


def merge_masters(
    m1_path: Path, m2_path: Path, res_path: Path, out_dir: Path
) -> tuple[Path, Path]:
    m1 = load_master(m1_path)
    m2 = load_master(m2_path)
    ensure_compat(m1, m2)
    diffs = generate_diffs(m1, m2)

    resolutions = orjson.loads(res_path.read_bytes())
    res_map = {(r["key"], r["field"]): r for r in resolutions}

    records = []
    recs1 = {rec.get("doi"): rec for rec in m1}
    recs2 = {rec.get("doi"): rec for rec in m2}
    for key in sorted(recs1, key=lambda k: str(k).lower() if k is not None else ""):
        r1 = recs1[key]
        r2 = recs2[key]
        fields = sorted(set(r1) | set(r2))
        merged: dict = {}
        for field in fields:
            if (key, field) in res_map:
                value = res_map[(key, field)]["resolved_value"]
            else:
                value = r1.get(field)
            if value is not None:
                merged[field] = value
        records.append(merged)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    master_path = out_dir / f"master_validated_{timestamp}.json"
    meta_path = out_dir / f"master_validated_meta_{timestamp}.json"
    master_path.write_bytes(orjson.dumps(records, option=orjson.OPT_INDENT_2))

    total_fields = len(diffs)
    matches = sum(1 for d in diffs.values() if d.status == "match")
    meta = {
        "total_fields": total_fields,
        "matches": matches,
        "conflicts": len(resolutions),
        "v1_chosen": sum(r["resolution_type"] == "v1" for r in resolutions),
        "v2_chosen": sum(r["resolution_type"] == "v2" for r in resolutions),
        "manual_edits": sum(r["resolution_type"] == "manual" for r in resolutions),
    }
    meta_path.write_bytes(orjson.dumps(meta, option=orjson.OPT_INDENT_2))

    return master_path, meta_path


def main(argv: list[str] | None = None) -> int:
    parser = ArgumentParser(description="Write validated master dataset")
    parser.add_argument("master_v1", help="Path to master_v1.json")
    parser.add_argument("master_v2", help="Path to master_v2.json")
    parser.add_argument("resolution", help="Path to resolution JSON")
    parser.add_argument("--out_dir", default=str(OUT_DIR), help="Output directory")
    args = parser.parse_args(argv)

    merge_masters(
        Path(args.master_v1),
        Path(args.master_v2),
        Path(args.resolution),
        Path(args.out_dir),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
