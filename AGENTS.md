# AGENTS Guide

This document provides instructions for AI agents working in this repository.

## Project Purpose
Automate extraction of structured metadata from academic PDFs and generate narrative reviews of Mendelian Randomization (MR) studies.

## Directory Layout
incomplete-- to be written at a later date. 

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
