# AGENTS Guide

This document provides instructions for AI agents working in this repository.

## Project Purpose
Automate extraction of structured metadata from academic PDFs and generate narrative reviews of Mendelian Randomization (MR) studies.

## Directory Layout
- `data/pdfs/` – raw PDF files.
- `data/text/` – page wise JSON text extracted from PDFs.
- `data/meta/` – JSON metadata produced by Agent 1.
- `data/master.json` – combined metadata across papers.
- `outputs/` – narrative reviews with citations.
- `prompts/` – prompt templates for the agents.
- `agent1/` – scripts for metadata extraction.
- `agent2/` – scripts for generating reviews.
- `tests/` – unit tests.

Directories not present should be created as needed. Avoid committing large binaries such as PDFs.

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

These instructions apply to all files in the repository.
