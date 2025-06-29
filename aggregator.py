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
ERROR_LOG = DATA_DIR / "aggregation_errors.log"


def _log_error(path: Path, exc: Exception) -> None:
    timestamp = datetime.utcnow().isoformat()
    message = f'[{timestamp}] Invalid JSON in file {path}: "{exc}"\n'
    ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ERROR_LOG.open("a") as f:
        f.write(message)
    logging.error("Invalid JSON in file %s: %s", path, exc)


def aggregate_metadata() -> List[PaperMetadata]:
    META_DIR.mkdir(parents=True, exist_ok=True)
    records: List[PaperMetadata] = []
    for json_file in sorted(META_DIR.glob("*.json")):
        try:
            data = orjson.loads(json_file.read_bytes())
            metadata = PaperMetadata.model_validate(data)
        except (orjson.JSONDecodeError, ValidationError) as exc:
            _log_error(json_file, exc)
            continue
        records.append(metadata)

    MASTER_PATH.write_bytes(
        orjson.dumps([r.model_dump() for r in records], option=orjson.OPT_INDENT_2)
    )
    return records


if __name__ == "__main__":
    aggregate_metadata()
