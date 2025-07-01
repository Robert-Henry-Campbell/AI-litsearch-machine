from __future__ import annotations

import orjson
from pathlib import Path

import run_pipeline
from schemas.metadata import PaperMetadata


class FakeNarrative:
    def __init__(self) -> None:
        self.calls: list[tuple[list[dict], list[str]]] = []

    def generate(self, metadata: list[dict], snippets: list[str]) -> str:
        self.calls.append((metadata, snippets))
        return "# Review"


class FakeExtractor:
    def __init__(self, meta_dir: Path) -> None:
        self.calls: list[Path] = []
        self.meta_dir = meta_dir

    def extract(self, text_path: Path, drug: str | None = None) -> PaperMetadata | None:
        self.calls.append(text_path)
        meta = PaperMetadata(
            title="T", doi="10.1/test", targets=[drug] if drug else None
        )
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.meta_dir / f"{text_path.stem}.json"
        out_path.write_bytes(orjson.dumps(meta.model_dump()))
        return meta


def test_full_pipeline_cli(monkeypatch, tmp_path: Path) -> None:
    pdf_dir = Path("tests/fixtures/sample_pdfs")

    monkeypatch.setattr("ingest.collector.LOG_PATH", tmp_path / "log.jsonl")
    monkeypatch.setattr("extract.pdf_to_text.DATA_DIR", tmp_path / "text")
    monkeypatch.setattr("agent1.metadata_extractor.META_DIR", tmp_path / "meta")
    monkeypatch.setattr("aggregate.META_DIR", tmp_path / "meta")
    monkeypatch.setattr("aggregate.MASTER_PATH", tmp_path / "master.json")
    monkeypatch.setattr("aggregate.HISTORY_DIR", tmp_path / "history")
    monkeypatch.setattr("agent2.retrieval.TEXT_DIR", tmp_path / "text")
    monkeypatch.setattr("pipeline.OUTPUT_DIR", tmp_path / "outputs")

    extractor = FakeExtractor(tmp_path / "meta")
    monkeypatch.setattr("pipeline.MetadataExtractor", lambda *a, **k: extractor)
    narrative = FakeNarrative()
    monkeypatch.setattr("pipeline.OpenAINarrative", lambda *a, **k: narrative)

    code = run_pipeline.main(
        [
            "--pdf_dir",
            str(pdf_dir),
            "--drug",
            "TestDrug",
            "--agent1-model",
            "a1",
            "--agent2-model",
            "a2",
            "--embed-model",
            "e",
        ]
    )
    assert code == 0

    master_path = tmp_path / "master.json"
    assert master_path.exists()
    data = orjson.loads(master_path.read_bytes())
    assert isinstance(data, list)
    for record in data:
        PaperMetadata.model_validate(record)
        assert record.get("targets") == ["TestDrug"]

    out_file = tmp_path / "outputs" / "review_TestDrug.md"
    assert out_file.exists()
