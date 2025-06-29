# AGENTS Guide

This document provides instructions for AI agents working in this repository.

## Project Purpose
Automate extraction of structured metadata from academic PDFs and generate narrative reviews of Mendelian Randomization (MR) studies.

## Directory Layout
This repository is organized into the following top-level folders:

- `agent1/` – metadata extraction helpers that call the OpenAI API.
- `agent2/` – tools for generating narrative summaries from metadata.
- `ingest/` – utilities for collecting PDFs and listing files to process.
- `extract/` – converts PDFs into JSON files of page text.
- `data/` – stores intermediate outputs such as `meta/`, `text/` and
  `master.json`.
- `outputs/` – final narrative reviews written by the synthesiser.
- `prompts/` – system prompts and templates for the agents.
- `schemas/` – pydantic models describing data structures.
- `tests/` – unit and integration tests.
- `utils/` – shared helper modules including logging and secrets management.

Key entry points include `pipeline.py` and `run_pipeline.py` which orchestrate
the full ingestion and synthesis flow.

## Coding Conventions
- Use **Python 3.12+**.
- Adhere to **PEP 8**.
- Use **pydantic** for data validation and **orjson** for JSON operations.
- Format with **black** and lint with **ruff**.

## Testing Protocols
- Run `pytest` for all tests.
- Add unit tests for new features.
- Validate JSON outputs against pydantic schemas.

## Development Workflow
1. Install dependencies with `pip install -r requirements.txt`.
2. Format and lint: `black .` and `ruff .`.
3. Run tests: `pytest`.
4. Ensure all checks pass before committing.
5. Ensure your OpenAI API key is available. When a human user runs code in this
   repository, the key should be set as the `OPENAI_API_KEY` environment
   variable. When the agent runs autonomously, the key is provided as a secret
   named `OPENAI_API_KEY`, not an environment variable. If the key is missing,
   instruct the user to add it as a secret. The agent must never insert the key
   itself, and it cannot be stored in the repository.

## Pull Request Guidelines
- Use clear, descriptive titles.
- Summarize changes and testing performed in the PR description.
- Ensure all tests pass.

## Documentation Updates
- Whenever new functionality or files are added, update `README.md` with a brief explanation of how they work.
- If `README.md` marked a feature as "under development" and you implement it, remove that notice.

These instructions apply to all files in the repository.

## Task Tracking
- When you discover a repository issue that isn't necessary for completing your current task, add a concise entry to `docs/TASKS.md` so it can be addressed later.
- Remove any item from `docs/TASKS.md` after implementing it.
