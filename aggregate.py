from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

import orjson

from schemas.metadata import PaperMetadata

ROOT = Path(__file__).resolve().parent
META_DIR = ROOT / "data" / "meta"
MASTER_PATH = ROOT / "data" / "master.json"
HISTORY_DIR = ROOT / "data" / "master_history"


def aggregate_metadata(
    meta_dir: Path | None = None,
    master_path: Path | None = None,
    history_dir: Path | None = None,
) -> List[PaperMetadata]:
    meta_dir = meta_dir or META_DIR
    master_path = master_path or MASTER_PATH
    history_dir = history_dir or HISTORY_DIR

    records: List[PaperMetadata] = []
    for file in sorted(meta_dir.glob("*.json")):
        try:
            data = orjson.loads(file.read_bytes())
            record = PaperMetadata.model_validate(data)
            records.append(record)
        except Exception:
            continue

    history_dir.mkdir(parents=True, exist_ok=True)
    if master_path.exists():
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        backup = history_dir / f"master_{timestamp}.json"
        backup.write_bytes(master_path.read_bytes())

    master_path.write_bytes(orjson.dumps([r.model_dump() for r in records]))
    return records


if __name__ == "__main__":
    aggregate_metadata()
