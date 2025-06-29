from __future__ import annotations

from schemas.metadata import PaperMetadata

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
