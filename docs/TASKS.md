# Proposed Tasks
- Add unit tests for `utils.secrets.get_openai_api_key` covering env var, file, and missing key scenarios.
- Add unit tests for `ingest.list_pdfs` to verify it lists PDF filenames correctly.
- Add unit tests for `pipeline.generate_narrative` and `pipeline.timed_step` with mocks to avoid API calls.
- Add unit tests for `aggregate._log_error` and `_backup_master` helper functions.
