from __future__ import annotations

import run_pipeline


def test_main_invokes_pipeline(monkeypatch):
    calls = {}

    def fake_run(
        pdf_dir: str,
        drug: str,
        *,
        agent1_model: str | None,
        agent2_model: str | None,
        embed_model: str | None,
    ) -> None:
        calls["pdf_dir"] = pdf_dir
        calls["drug"] = drug
        calls["agent1_model"] = agent1_model
        calls["agent2_model"] = agent2_model
        calls["embed_model"] = embed_model

    monkeypatch.setattr("pipeline.run_pipeline", fake_run)

    code = run_pipeline.main(
        [
            "--pdf_dir",
            "data/pdfs",
            "--drug",
            "rapa",
            "--agent1-model",
            "a1",
            "--agent2-model",
            "a2",
            "--embed-model",
            "e",
        ]
    )
    assert code == 0
    assert calls == {
        "pdf_dir": "data/pdfs",
        "drug": "rapa",
        "agent1_model": "a1",
        "agent2_model": "a2",
        "embed_model": "e",
    }
