from __future__ import annotations

from pathlib import Path

import orjson
import pytest

from schemas.metadata import PaperMetadata


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def call(self, _text, *, max_retries=2):
        self.calls += 1
        return self.responses.pop(0)


def create_text_file(tmp_path: Path) -> Path:
    data = {"pages": [{"page": 1, "text": "content"}]}
    path = tmp_path / "text.json"
    path.write_bytes(orjson.dumps(data))
    return path


def create_pdf(path: Path) -> None:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(100, 750, "Hello")
    c.showPage()
    c.save()


def test_retry_logic(monkeypatch, tmp_path):
    from agent1.metadata_extractor import MetadataExtractor

    monkeypatch.setattr("agent1.metadata_extractor.META_DIR", tmp_path / "meta")
    text_path = create_text_file(tmp_path)
    client = FakeClient([{"title": 1}, {"title": "T"}])
    extractor = MetadataExtractor(client=client)
    result = extractor.extract(text_path, None)
    assert result is not None
    assert client.calls == 2


def test_paper_metadata_validation():
    data = {
        "title": "T",
        "authors": "A",
        "doi": "10.1/abc",
        "pub_date": "2024-01-01",
        "data_sources": ["db"],
        "omics_modalities": ["gen"],
        "targets": ["t"],
        "p_threshold": "1e-5",
        "ld_r2": "0.1",
    }
    meta = PaperMetadata(**data)
    assert meta.title == "T"
    with pytest.raises(Exception):
        PaperMetadata(title=123)  # type: ignore


def test_cli_end_to_end(monkeypatch, tmp_path):

    result = {"title": "T", "doi": "10.1/x"}
    fake_client = FakeClient([result])
    monkeypatch.setattr(
        "agent1.metadata_extractor.OpenAIJSONCaller", lambda: fake_client
    )
    monkeypatch.setattr("agent1.metadata_extractor.META_DIR", tmp_path / "meta")
    monkeypatch.setattr("extract.pdf_to_text.DATA_DIR", tmp_path / "text")

    import agent1.run as run

    pdf = tmp_path / "paper.pdf"
    create_pdf(pdf)

    code = run.main(["--pdf", str(pdf)])
    assert code == 0
    out_file = tmp_path / "meta" / "10.1_x.json"
    assert out_file.exists()
    loaded = orjson.loads(out_file.read_bytes())
    PaperMetadata.model_validate(loaded)
    assert fake_client.calls == 1
