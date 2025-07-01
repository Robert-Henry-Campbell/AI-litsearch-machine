from __future__ import annotations

from pathlib import Path
import re
from typing import List, Literal

import orjson

from .openai_index import query_index

BASE_DIR = Path("data")
TEXT_DIR = BASE_DIR / "text"
INDEX_PATH = BASE_DIR / "index.faiss"


def set_base_dir(base_dir: Path) -> None:
    global BASE_DIR, TEXT_DIR, INDEX_PATH
    BASE_DIR = Path(base_dir)
    TEXT_DIR = BASE_DIR / "text"
    INDEX_PATH = BASE_DIR / "index.faiss"


def _safe_name(doi: str) -> str:
    return doi.replace("/", "_").replace(":", "_")


def load_pages(doi: str) -> List[dict]:
    path = TEXT_DIR / f"{_safe_name(doi)}.json"
    if not path.exists():
        return []
    data = orjson.loads(path.read_bytes())
    return data.get("pages", [])


def _keyword_snippets(doi: str, keyword: str, *, window: int = 40) -> List[str]:
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


def get_snippets(
    doi: str,
    drug_name: str,
    *,
    k: int = 5,
    embed_model: str | None = None,
    method: Literal["faiss", "text"] = "faiss",
) -> List[str]:
    """Return up to ``k`` snippets mentioning ``drug_name`` from ``doi``.

    ``method`` selects the retrieval backend. ``faiss`` uses the embedding index
    and fails if the index is missing. ``text`` searches the extracted page text
    directly without requiring the index. ``embed_model`` is only used when
    ``method`` is ``faiss``.
    """
    if method not in {"faiss", "text"}:
        raise ValueError("method must be 'faiss' or 'text'")

    if method == "faiss":
        if not INDEX_PATH.exists():
            raise FileNotFoundError(INDEX_PATH)
        try:
            emb = query_index(
                doi,
                drug_name,
                k=k,
                index_path=INDEX_PATH,
                model=embed_model or "text-embedding-3-small",
            )
            return [r.get("text", "").strip() for r in emb if r.get("text")][:k]
        except Exception:
            return []

    # method == "text"
    return _keyword_snippets(doi, drug_name)[:k]
