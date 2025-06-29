from __future__ import annotations

import run_pipeline


def test_main_invokes_pipeline(monkeypatch):
    calls = {}

    def fake_run(pdf_dir: str, drug: str) -> None:
        calls["pdf_dir"] = pdf_dir
        calls["drug"] = drug

    monkeypatch.setattr("pipeline.run_pipeline", fake_run)

    code = run_pipeline.main(["--pdf_dir", "data/pdfs", "--drug", "rapa"])
    assert code == 0
    assert calls == {"pdf_dir": "data/pdfs", "drug": "rapa"}
