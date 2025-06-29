from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

import orjson
from schemas.metadata import PaperMetadata

BASE_DIR = Path(__file__).resolve().parent
META_DIR = BASE_DIR / "data" / "meta"
MASTER_PATH = BASE_DIR / "data" / "master.json"
HISTORY_DIR = BASE_DIR / "data" / "master_history"


def load_metadata() -> List[dict]:
    META_DIR.mkdir(parents=True, exist_ok=True)
    records: List[dict] = []
    for path in sorted(META_DIR.glob("*.json")):
        try:
            data = orjson.loads(path.read_bytes())
            record = PaperMetadata.model_validate(data)
            records.append(record.model_dump())
        except Exception:
            continue
    return records


def backup_master() -> None:
    if MASTER_PATH.exists():
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        backup = HISTORY_DIR / f"master_{timestamp}.json"
        backup.write_bytes(MASTER_PATH.read_bytes())


def aggregate() -> Path:
    records = load_metadata()
    backup_master()
    MASTER_PATH.write_bytes(orjson.dumps(records))
    return MASTER_PATH


if __name__ == "__main__":
    aggregate()
