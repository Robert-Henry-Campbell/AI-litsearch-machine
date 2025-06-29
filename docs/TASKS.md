# Proposed Tasks

The newly added integration tests in `tests/integration/test_real_pdfs.py` fail because `agent1.openai_client.OpenAIJSONCaller` reads its prompt using the platform default encoding. When the default is not UTF-8, `Path.read_text()` throws a `UnicodeDecodeError` for `prompts/agent1_prompt.txt`.

## Task: enforce UTF-8 when loading prompts
- Update `agent1/openai_client.py` to read `PROMPT_PATH` using an explicit UTF-8 decode.
- Add a similar explicit decode in `agent2/openai_narrative.py`.
- Verify that the integration tests pass after these changes.

### Status
Completed – integration tests now succeed on systems with non-UTF‑8 defaults.
