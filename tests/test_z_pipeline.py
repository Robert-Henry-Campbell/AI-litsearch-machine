from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from ingest.collector import ingest_pdf
from extract.pdf_to_text import pdf_to_text


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def call(self, _text, *, max_retries=2):
        self.calls += 1
        return self.response


def create_pdf(path: Path, pages: int = 1) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    for i in range(pages):
        c.drawString(100, 750, f"Page {i + 1}")
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
        "outcome": None,
        "additional_QC": None,
    }


def test_ingest_prevents_duplicates(tmp_path, monkeypatch):
    pdf = tmp_path / "file.pdf"
    create_pdf(pdf)

    log = tmp_path / "log.jsonl"
    monkeypatch.setattr("ingest.collector.LOG_PATH", log)

    first = ingest_pdf(pdf)
    assert first is not None
    assert log.exists()

    second = ingest_pdf(pdf)
    assert second is None
    lines = log.read_text().splitlines()
    assert len(lines) == 1


def test_full_pipeline(tmp_path, monkeypatch):
    pdf = tmp_path / "paper.pdf"
    create_pdf(pdf)

    # Ingestion
    log = tmp_path / "log.jsonl"
    monkeypatch.setattr("ingest.collector.LOG_PATH", log)
    entry = ingest_pdf(pdf)
    assert entry is not None

    # Text extraction
    text_dir = tmp_path / "text"
    monkeypatch.setattr("extract.pdf_to_text.DATA_DIR", text_dir)
    data = pdf_to_text(pdf)
    text_path = text_dir / f"{pdf.stem}.json"
    assert text_path.exists()
    assert len(data.pages) == 1

    # Metadata extraction
    from agent1.metadata_extractor import MetadataExtractor

    meta_dir = tmp_path / "meta"
    monkeypatch.setattr("agent1.metadata_extractor.META_DIR", meta_dir)
    client = FakeClient(valid_metadata())
    extractor = MetadataExtractor(client=client)
    meta = extractor.extract(text_path, "Drug")
    assert meta is not None
    out_file = meta_dir / "10.1_test.json"
    assert out_file.exists()
    assert client.calls == 1
