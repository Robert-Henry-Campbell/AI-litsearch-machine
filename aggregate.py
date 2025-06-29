from __future__ import annotations

from pathlib import Path
import orjson
from pydantic import ValidationError

from schemas.metadata import PaperMetadata

META_DIR = Path(__file__).resolve().parent / "data" / "meta"
OUT_PATH = Path(__file__).resolve().parent / "data" / "master.json"


def aggregate() -> list[PaperMetadata]:
    entries: list[PaperMetadata] = []
    META_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(META_DIR.glob("*.json")):
        try:
            data = orjson.loads(path.read_bytes())
            entry = PaperMetadata.model_validate(data)
        except (orjson.JSONDecodeError, ValidationError):
            continue
        entries.append(entry)
    OUT_PATH.write_bytes(orjson.dumps([e.model_dump() for e in entries]))
    return entries


if __name__ == "__main__":
    result = aggregate()
    print(orjson.dumps([e.model_dump() for e in result]).decode())
