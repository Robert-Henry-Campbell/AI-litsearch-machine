# Proposed Tasks

- Add unit tests for `pipeline.generate_narrative` and `pipeline.timed_step` with mocks to avoid API calls.
- Running `agent1/run.py` and `agent2/synthesiser.py` as scripts raises `ModuleNotFoundError`.
- Install `tesseract` so `test_ocr_fallback` is no longer skipped.
- Provide `OPENAI_API_KEY` to enable live integration tests against the OpenAI API.
- Pin `pydantic>=2` in requirements to avoid test failures with older versions.
