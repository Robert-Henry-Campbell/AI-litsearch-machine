from __future__ import annotations


from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import logging

import orjson
from pydantic import ValidationError

from schemas.metadata import PaperMetadata


BASE_DIR = Path("data")
META_DIR = BASE_DIR / "meta"
MASTER_PATH = BASE_DIR / "master.json"
HISTORY_DIR = BASE_DIR / "master_history"
ERROR_LOG = BASE_DIR / "aggregation_errors.log"


def set_base_dir(base_dir: Path) -> None:
    """Update all path constants to live under ``base_dir``."""
    global BASE_DIR, META_DIR, MASTER_PATH, HISTORY_DIR, ERROR_LOG
    BASE_DIR = Path(base_dir)
    META_DIR = BASE_DIR / "meta"
    MASTER_PATH = BASE_DIR / "master.json"
    HISTORY_DIR = BASE_DIR / "master_history"
    ERROR_LOG = BASE_DIR / "aggregation_errors.log"


def _log_error(path: Path, exc: Exception) -> None:
    timestamp = datetime.utcnow().isoformat()
    msg = f'[{timestamp}] Invalid JSON in file {path}: "{exc}"\n'
    ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ERROR_LOG.open("a") as f:
        f.write(msg)
    logging.error("Invalid JSON in file %s: %s", path, exc)


def _load_metadata() -> Tuple[List[PaperMetadata], int]:
    META_DIR.mkdir(parents=True, exist_ok=True)
    records: List[PaperMetadata] = []
    invalid = 0
    for path in sorted(META_DIR.glob("*.json")):
        try:
            data = orjson.loads(path.read_bytes())
            record = PaperMetadata.model_validate(data)
        except (orjson.JSONDecodeError, ValidationError) as exc:
            _log_error(path, exc)
            invalid += 1
            continue
        records.append(record)
    return records, invalid


def _backup_master() -> Path | None:
    if MASTER_PATH.exists():
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        backup = HISTORY_DIR / f"master_{timestamp}.json"
        backup.write_bytes(MASTER_PATH.read_bytes())
        return backup
    return None


def aggregate_metadata() -> Tuple[List[PaperMetadata], int, Path | None]:
    records, skipped = _load_metadata()
    backup = _backup_master()
    MASTER_PATH.write_bytes(
        orjson.dumps([r.model_dump() for r in records], option=orjson.OPT_INDENT_2)
    )
    return records, skipped, backup


def main() -> None:
    records, skipped, backup = aggregate_metadata()
    print(f"Aggregated {len(records)} metadata files successfully.")
    if skipped:
        print(f"Skipped {skipped} invalid metadata files (see {ERROR_LOG.name}).")
    else:
        print("Skipped 0 invalid metadata files.")
    if backup is not None:
        rel_backup = backup.relative_to(BASE_DIR)
        print(f"Backup created: {rel_backup}")


if __name__ == "__main__":
    main()
