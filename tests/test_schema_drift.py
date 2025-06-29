from __future__ import annotations

from pathlib import Path
import orjson
import pytest

from schemas.metadata import PaperMetadata

META_DIR = Path("data/meta")


@pytest.mark.parametrize("path", sorted(META_DIR.glob("*.json")))
def test_metadata_conforms_to_schema(path: Path) -> None:
    data = orjson.loads(path.read_bytes())
    PaperMetadata.model_validate(data)
