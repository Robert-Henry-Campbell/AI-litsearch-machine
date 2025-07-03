from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import orjson
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
        "outcome": None,
        "additional_QC": None,
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
        lambda self, _path, _drug=None: PaperMetadata(**valid_metadata()),
    )
    monkeypatch.setattr("aggregate.META_DIR", tmp_path / "meta")
    monkeypatch.setattr("aggregate.MASTER_PATH", tmp_path / "master.json")
    monkeypatch.setattr("aggregate.HISTORY_DIR", tmp_path / "history")
    monkeypatch.setattr("agent2.retrieval.TEXT_DIR", tmp_path / "text")
    monkeypatch.setattr("pipeline.OUTPUT_DIR", tmp_path / "out")

    fake = FakeNarrative()
    monkeypatch.setattr("pipeline.OpenAINarrative", lambda *a, **k: fake)

    pipeline.run_pipeline(
        str(pdf_dir), "test", base_dir=tmp_path, retrieval_method="text"
    )

    assert (tmp_path / "master.json").exists()
    out_file = tmp_path / "out" / "review_test.md"
    assert out_file.exists()
    assert fake.calls


def test_generate_narrative_cache(monkeypatch, tmp_path):
    from agent2 import openai_index as oi
    from agent2 import retrieval

    text_dir = tmp_path / "text"
    text_dir.mkdir()
    file_path = text_dir / "10.6_cache.json"
    file_path.write_text('{"pages":[{"page":1,"text":"drug study"}]}')
    index_path = tmp_path / "index.faiss"

    monkeypatch.setattr(
        oi, "embed_chunks", lambda chunks, model="m": [[0.1, 0.2] for _ in chunks]
    )
    oi.build_openai_index([file_path], index_path, model="m")

    calls = {"count": 0}

    def fake_embed(chunks, model="m"):
        calls["count"] += 1
        return [[0.1, 0.2] for _ in chunks]

    monkeypatch.setattr(oi, "embed_chunks", fake_embed)
    oi.clear_cache()

    monkeypatch.setattr(retrieval, "TEXT_DIR", text_dir)
    monkeypatch.setattr(retrieval, "INDEX_PATH", index_path)
    monkeypatch.setattr("pipeline.OUTPUT_DIR", tmp_path / "out")

    monkeypatch.setattr("pipeline.OpenAINarrative", lambda *a, **k: FakeNarrative())
    monkeypatch.setattr("aggregate.MASTER_PATH", tmp_path / "master.json")
    records = [{"title": "T", "doi": "10.6/cache"}, {"title": "T", "doi": "10.6/cache"}]
    (tmp_path / "master.json").write_text(orjson.dumps(records).decode())

    pipeline.generate_narrative("drug", embed_model="m", retrieval_method="faiss")

    assert calls["count"] == 1


def test_no_blank_snippets(monkeypatch, tmp_path):
    from agent2 import openai_index as oi
    from agent2 import retrieval

    text_dir = tmp_path / "text"
    text_dir.mkdir()
    file_path = text_dir / "10.7_blank.json"
    file_path.write_text('{"pages":[{"page":1,"text":"drug snippet"}]}')
    index_path = tmp_path / "index.faiss"

    monkeypatch.setattr(
        oi, "embed_chunks", lambda chunks, model="m": [[0.1, 0.2] for _ in chunks]
    )
    oi.build_openai_index([file_path], index_path, model="m")

    monkeypatch.setattr(retrieval, "TEXT_DIR", text_dir)
    monkeypatch.setattr(retrieval, "INDEX_PATH", index_path)
    monkeypatch.setattr("pipeline.OUTPUT_DIR", tmp_path / "out")
    monkeypatch.setattr("aggregate.MASTER_PATH", tmp_path / "master.json")
    records = [{"title": "T", "doi": "10.7/blank"}]
    (tmp_path / "master.json").write_text(orjson.dumps(records).decode())

    class CheckingNarrative(FakeNarrative):
        def generate(self, metadata, snippets):
            assert snippets, "no snippets returned"
            assert all(s.strip() for s in snippets), "blank snippet detected"
            return super().generate(metadata, snippets)

    monkeypatch.setattr("pipeline.OpenAINarrative", lambda *a, **k: CheckingNarrative())

    pipeline.generate_narrative("drug", embed_model="m", retrieval_method="faiss")


def test_run_pipeline_batch(monkeypatch, tmp_path):
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    pdf = pdf_dir / "p.pdf"
    create_pdf(pdf)

    monkeypatch.setattr("ingest.collector.LOG_PATH", tmp_path / "log.jsonl")
    monkeypatch.setattr("extract.pdf_to_text.DATA_DIR", tmp_path / "text")
    monkeypatch.setattr("agent1.metadata_extractor.META_DIR", tmp_path / "meta")
    monkeypatch.setattr("aggregate.META_DIR", tmp_path / "meta")
    monkeypatch.setattr("aggregate.MASTER_PATH", tmp_path / "master.json")
    monkeypatch.setattr("aggregate.HISTORY_DIR", tmp_path / "history")
    monkeypatch.setattr("agent2.retrieval.TEXT_DIR", tmp_path / "text")
    monkeypatch.setattr("pipeline.OUTPUT_DIR", tmp_path / "out")

    monkeypatch.setattr(
        "agent1.metadata_extractor.MetadataExtractor.extract",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("extract called")),
    )
    monkeypatch.setattr(
        "aggregate.aggregate_metadata",
        lambda: (_ for _ in ()).throw(AssertionError("aggregate called")),
    )
    monkeypatch.setattr(
        "pipeline.generate_narrative",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("narrative called")),
    )

    pipeline.run_pipeline(str(pdf_dir), "drug", base_dir=tmp_path, batch=True)

    batch_file = tmp_path / "drug_batch_1.jsonl"
    assert batch_file.exists()
    assert batch_file.read_text().strip()


def test_batch_token_split(monkeypatch, tmp_path):
    text_dir = tmp_path / "text"
    text_dir.mkdir()
    long_text = "word " * 60
    for i in range(2):
        path = text_dir / f"{i}.json"
        path.write_text(
            orjson.dumps({"pages": [{"page": 1, "text": long_text}]}).decode()
        )

    monkeypatch.setattr("pipeline.TEXT_DIR", text_dir)

    batches = pipeline.write_agent1_batch("drug", tmp_path, token_limit=100)
    assert len(batches) == 2
    assert all(p.exists() for p in batches)
