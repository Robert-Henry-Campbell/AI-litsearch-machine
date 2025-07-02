from __future__ import annotations

from pathlib import Path

import run_pipeline


def test_main_invokes_pipeline(monkeypatch):
    calls = {}

    def fake_run(
        pdf_dir: str,
        drug: str,
        *,
        base_dir: Path,
        agent1_model: str | None,
        agent2_model: str | None,
        embed_model: str | None,
        retrieval_method: str,
        batch: bool,
    ) -> None:
        calls["pdf_dir"] = pdf_dir
        calls["drug"] = drug
        calls["base_dir"] = base_dir
        calls["agent1_model"] = agent1_model
        calls["agent2_model"] = agent2_model
        calls["embed_model"] = embed_model
        calls["retrieval_method"] = retrieval_method
        calls["batch"] = batch

    monkeypatch.setattr("pipeline.run_pipeline", fake_run)

    code = run_pipeline.main(
        [
            "--pdf_dir",
            "data/pdfs",
            "--drug",
            "rapa",
            "--base_dir",
            "data",
            "--agent1-model",
            "a1",
            "--agent2-model",
            "a2",
            "--embed-model",
            "e",
            "--retrieval",
            "faiss",
        ]
    )
    assert code == 0
    assert calls == {
        "pdf_dir": "data/pdfs",
        "drug": "rapa",
        "agent1_model": "a1",
        "agent2_model": "a2",
        "embed_model": "e",
        "retrieval_method": "faiss",
        "batch": False,
        "base_dir": Path("data"),
    }


def test_batch_flag(monkeypatch):
    calls = {}

    def fake_run(
        pdf_dir: str,
        drug: str,
        *,
        base_dir: Path,
        agent1_model: str | None,
        agent2_model: str | None,
        embed_model: str | None,
        retrieval_method: str,
        batch: bool,
    ) -> None:
        calls["batch"] = batch

    monkeypatch.setattr("pipeline.run_pipeline", fake_run)

    code = run_pipeline.main(
        [
            "--pdf_dir",
            "data/pdfs",
            "--drug",
            "rapa",
            "--batch",
        ]
    )

    assert code == 0
    assert calls == {"batch": True}
