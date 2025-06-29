from pathlib import Path

import pytest

from ingest.collector import ingest_pdf
from extract.pdf_to_text import pdf_to_text


class FakeClient:
    def __init__(self, response):
        self.response = response

    def call(self, text, *, max_retries=2):
        return self.response


def valid_metadata() -> dict:
    return {
        "title": "T",
        "authors": "A",
        "doi": "10.1/test",
        "pub_date": None,
        "data_sources": None,
        "omics_modalities": None,
        "targets": None,
        "p_threshold": None,
        "ld_r2": None,
    }


@pytest.mark.parametrize("pdf_path", sorted(Path("data/pdfs").glob("*.pdf")))
def test_pdf_to_text_real_files(
    tmp_path: Path, pdf_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("extract.pdf_to_text.DATA_DIR", tmp_path)
    ingest_pdf(pdf_path)
    result = pdf_to_text(pdf_path)
    assert result.pages


@pytest.mark.parametrize("pdf_path", sorted(Path("data/pdfs").glob("*.pdf")))
def test_metadata_extractor_prompt_decode_error(
    tmp_path: Path, pdf_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("extract.pdf_to_text.DATA_DIR", tmp_path / "text")
    monkeypatch.setattr("agent1.metadata_extractor.META_DIR", tmp_path / "meta")
    pdf_to_text(pdf_path)

    import agent1.openai_client as oc

    original_read_text = oc.Path.read_text

    def cp1252_read_text(self, *args, **kwargs):
        return original_read_text(self, encoding="cp1252")

    monkeypatch.setattr(oc.Path, "read_text", cp1252_read_text)

    from agent1.metadata_extractor import MetadataExtractor

    MetadataExtractor()
