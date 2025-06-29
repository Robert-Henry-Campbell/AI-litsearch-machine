from __future__ import annotations

from pathlib import Path
import re
from typing import List

import orjson

TEXT_DIR = Path(__file__).resolve().parents[1] / "data" / "text"


def _safe_name(doi: str) -> str:
    return doi.replace("/", "_").replace(":", "_")


def load_pages(doi: str) -> List[dict]:
    path = TEXT_DIR / f"{_safe_name(doi)}.json"
    if not path.exists():
        return []
    data = orjson.loads(path.read_bytes())
    return data.get("pages", [])


def get_snippets(doi: str, keyword: str, *, window: int = 40) -> List[str]:
    pages = load_pages(doi)
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    results: List[str] = []
    for page in pages:
        text = page.get("text", "")
        for match in pattern.finditer(text):
            start = max(match.start() - window, 0)
            end = min(match.end() + window, len(text))
            snippet = text[start:end].strip()
            results.append(f"Page {page.get('page')}: {snippet}")
    return results
