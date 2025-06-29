# Proposed Tasks


- Add unit tests for `utils.secrets.get_openai_api_key` covering env var, file, and missing key scenarios.

- Add unit tests for `ingest.list_pdfs` to verify it lists PDF filenames correctly.

- Add unit tests for `pipeline.generate_narrative` and `pipeline.timed_step` with mocks to avoid API calls.
- Add unit tests for `aggregate._log_error` and `_backup_master` helper functions.



- Investigate why `OPENAI_API_KEY` is not detected during `test_openai_api_connection`.
- Document the repository directory layout in `AGENTS.md`.
- Decide on the supported `openai` version and update the code and documentation accordingly.
- Remove unused `pandas` from `requirements.txt`.

- Standardise narrative review filenames across the pipeline and synthesiser.

- Resolve the `fastapi` and `pydantic` version conflict reported by `pip check`.


- Fix `utils/data_wipe.py` so it can run directly without `ModuleNotFoundError`.

- Standardise narrative review filenames across the pipeline and synthesiser.

- Running `agent1/run.py` and `agent2/synthesiser.py` as scripts raises `ModuleNotFoundError`.
- Install `tesseract` so `test_ocr_fallback` is no longer skipped.

