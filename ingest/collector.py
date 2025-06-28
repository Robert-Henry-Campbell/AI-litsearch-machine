from __future__ import annotations

from datetime import datetime
from hashlib import md5
from pathlib import Path
from typing import Optional

import orjson
from pydantic import BaseModel

LOG_PATH = Path(__file__).resolve().parents[1] / "ingestion_log.jsonl"


class LogEntry(BaseModel):
    filename: str
    filepath: str
    md5: str
    timestamp: datetime


def compute_md5(path: Path) -> str:
    hash_md5 = md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def load_existing_checksums() -> set[str]:
    if not LOG_PATH.exists():
        return set()
    checksums = set()
    with LOG_PATH.open("rb") as f:
        for line in f:
            try:
                entry = orjson.loads(line)
                checksums.add(entry["md5"])
            except orjson.JSONDecodeError:
                continue
    return checksums


def append_log(entry: LogEntry) -> None:
    with LOG_PATH.open("ab") as f:
        f.write(orjson.dumps(entry.model_dump()) + b"\n")


def ingest_pdf(path: str | Path) -> Optional[LogEntry]:
    pdf_path = Path(path)
    checksum = compute_md5(pdf_path)
    existing = load_existing_checksums()
    if checksum in existing:
        return None
    entry = LogEntry(
        filename=pdf_path.name,
        filepath=str(pdf_path.resolve()),
        md5=checksum,
        timestamp=datetime.utcnow(),
    )
    append_log(entry)
    return entry


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest a PDF file")
    parser.add_argument("pdf", type=str)
    args = parser.parse_args()
    result = ingest_pdf(args.pdf)
    if result is None:
        print("PDF already ingested")
    else:
        print(orjson.dumps(result.model_dump()).decode())
