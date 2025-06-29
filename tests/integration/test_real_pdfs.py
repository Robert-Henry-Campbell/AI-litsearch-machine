from pathlib import Path

import pytest

from ingest.collector import ingest_pdf
from extract.pdf_to_text import pdf_to_text
from schemas.metadata import PaperMetadata
from utils.secrets import get_openai_api_key

import importlib
import sys

if "openai" in sys.modules:
    module = sys.modules["openai"]
    if not hasattr(module, "OpenAI"):
        importlib.reload(module)


@pytest.mark.parametrize("pdf_path", sorted(Path("data/pdfs").glob("*.pdf")))
def test_full_extraction_real_file(
    tmp_path: Path, pdf_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    try:
        get_openai_api_key()
    except RuntimeError:
        pytest.skip("OPENAI_API_KEY not found")

    monkeypatch.setattr("extract.pdf_to_text.DATA_DIR", tmp_path / "text")
    monkeypatch.setattr("agent1.metadata_extractor.META_DIR", tmp_path / "meta")

    ingest_pdf(pdf_path)
    text_data = pdf_to_text(pdf_path)
    assert text_data.pages

    from agent1.metadata_extractor import MetadataExtractor

    extractor = MetadataExtractor()
    meta = extractor.extract(tmp_path / "text" / f"{pdf_path.stem}.json")
    assert meta is not None
    PaperMetadata.model_validate(meta.model_dump())


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


def test_run_pipeline_real(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import pipeline

    try:
        get_openai_api_key()
    except RuntimeError:
        pytest.skip("OPENAI_API_KEY not found")

    monkeypatch.setattr("ingest.collector.LOG_PATH", tmp_path / "log.jsonl")
    monkeypatch.setattr("extract.pdf_to_text.DATA_DIR", tmp_path / "text")
    monkeypatch.setattr("pipeline.TEXT_DIR", tmp_path / "text")
    monkeypatch.setattr("agent1.metadata_extractor.META_DIR", tmp_path / "meta")
    monkeypatch.setattr("aggregate.META_DIR", tmp_path / "meta")
    monkeypatch.setattr("aggregate.MASTER_PATH", tmp_path / "master.json")
    monkeypatch.setattr("aggregate.HISTORY_DIR", tmp_path / "history")
    monkeypatch.setattr("agent2.retrieval.TEXT_DIR", tmp_path / "text")
    monkeypatch.setattr("pipeline.OUTPUT_DIR", tmp_path / "out")

    pipeline.run_pipeline("data/pdfs", "sglt2i")

    master = tmp_path / "master.json"
    assert master.exists()
    data = master.read_bytes()
    assert data
    out_file = tmp_path / "out" / "review_sglt2i.md"
    assert out_file.exists()
