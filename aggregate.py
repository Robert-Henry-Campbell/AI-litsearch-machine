from __future__ import annotations


from datetime import datetime
from pathlib import Path
from typing import List

import logging

import orjson
from pydantic import ValidationError

from schemas.metadata import PaperMetadata


DATA_DIR = Path(__file__).resolve().parent / "data"
META_DIR = DATA_DIR / "meta"
MASTER_PATH = DATA_DIR / "master.json"
HISTORY_DIR = DATA_DIR / "master_history"
ERROR_LOG = DATA_DIR / "aggregation_errors.log"


def _log_error(path: Path, exc: Exception) -> None:
    timestamp = datetime.utcnow().isoformat()
    msg = f'[{timestamp}] Invalid JSON in file {path}: "{exc}"\n'
    ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ERROR_LOG.open("a") as f:
        f.write(msg)
    logging.error("Invalid JSON in file %s: %s", path, exc)


def _load_metadata() -> List[PaperMetadata]:
    META_DIR.mkdir(parents=True, exist_ok=True)
    records: List[PaperMetadata] = []
    for path in sorted(META_DIR.glob("*.json")):
        try:
            data = orjson.loads(path.read_bytes())
            record = PaperMetadata.model_validate(data)
        except (orjson.JSONDecodeError, ValidationError) as exc:
            _log_error(path, exc)
            continue
        records.append(record)
    return records


def _backup_master() -> None:
    if MASTER_PATH.exists():
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        backup = HISTORY_DIR / f"master_{timestamp}.json"
        backup.write_bytes(MASTER_PATH.read_bytes())


def aggregate_metadata() -> List[PaperMetadata]:
    records = _load_metadata()
    _backup_master()
    MASTER_PATH.write_bytes(
        orjson.dumps([r.model_dump() for r in records], option=orjson.OPT_INDENT_2)
    )
    return records


if __name__ == "__main__":
    aggregate_metadata()

