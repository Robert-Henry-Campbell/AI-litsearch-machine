from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pytest

import pipeline
from schemas.metadata import PaperMetadata


@pytest.fixture(autouse=True)
def fake_openai_key(monkeypatch):
    monkeypatch.setattr("agent1.openai_client.get_openai_api_key", lambda: "key")
    monkeypatch.setattr("agent2.openai_narrative.get_openai_api_key", lambda: "key")


def create_pdf(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(100, 750, "Hello")
    c.showPage()
    c.save()


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


class FakeNarrative:
    def __init__(self):
        self.calls = []

    def generate(self, metadata, snippets):
        self.calls.append((metadata, snippets))
        return "review"


def test_run_pipeline(monkeypatch, tmp_path):
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    pdf = pdf_dir / "paper.pdf"
    create_pdf(pdf)

    log_path = tmp_path / "log.jsonl"
    monkeypatch.setattr("ingest.collector.LOG_PATH", log_path)
    monkeypatch.setattr("extract.pdf_to_text.DATA_DIR", tmp_path / "text")
    monkeypatch.setattr("agent1.metadata_extractor.META_DIR", tmp_path / "meta")
    monkeypatch.setattr(
        "agent1.metadata_extractor.MetadataExtractor.extract",
        lambda self, _path: PaperMetadata(**valid_metadata()),
    )
    monkeypatch.setattr("aggregate.META_DIR", tmp_path / "meta")
    monkeypatch.setattr("aggregate.MASTER_PATH", tmp_path / "master.json")
    monkeypatch.setattr("aggregate.HISTORY_DIR", tmp_path / "history")
    monkeypatch.setattr("agent2.retrieval.TEXT_DIR", tmp_path / "text")
    monkeypatch.setattr("pipeline.OUTPUT_DIR", tmp_path / "out")

    fake = FakeNarrative()
    monkeypatch.setattr("pipeline.OpenAINarrative", lambda: fake)

    pipeline.run_pipeline(str(pdf_dir), "test")

    assert (tmp_path / "master.json").exists()
    out_file = tmp_path / "out" / "test_review.md"
    assert out_file.exists()
    assert fake.calls
