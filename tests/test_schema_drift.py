from __future__ import annotations

from pathlib import Path
import orjson
import pytest

from schemas.metadata import PaperMetadata

META_DIR = Path("data/meta")

EXPECTED_KEYS = {
    "title",
    "authors",
    "doi",
    "pub_date",
    "data_sources",
    "omics_modalities",
    "targets",
    "p_threshold",
    "ld_r2",
}


def test_metadata_schema_keys() -> None:
    schema_keys = set(PaperMetadata.__annotations__.keys())
    assert (
        schema_keys == EXPECTED_KEYS
    ), f"Schema drift detected: {schema_keys ^ EXPECTED_KEYS}"


@pytest.mark.parametrize("path", sorted(META_DIR.glob("*.json")))
def test_metadata_conforms_to_schema(path: Path) -> None:
    data = orjson.loads(path.read_bytes())
    PaperMetadata.model_validate(data)
