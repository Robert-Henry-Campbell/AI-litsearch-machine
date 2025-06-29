# Proposed Tasks

- Investigate why `OPENAI_API_KEY` is not detected during `test_openai_api_connection`.
- Document the repository directory layout in `AGENTS.md`.
- Decide on the supported `openai` version and update the code and documentation accordingly.
- Remove unused `pandas` from `requirements.txt`.
- Resolve the `fastapi` and `pydantic` version conflict reported by `pip check`.
- Standardise narrative review filenames across the pipeline and synthesiser.
- Fix `utils/data_wipe.py` so it can run directly without `ModuleNotFoundError`.
- Running `agent1/run.py` and `agent2/synthesiser.py` as scripts raises `ModuleNotFoundError`.
- Install `tesseract` so `test_ocr_fallback` is no longer skipped.
