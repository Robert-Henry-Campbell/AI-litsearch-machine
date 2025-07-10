from __future__ import annotations

import re
import unicodedata
from rapidfuzz.fuzz import token_set_ratio


_punct_re = re.compile(r"[^\w\s]")


def _normalize(title: str) -> str:
    text = unicodedata.normalize("NFD", title)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = _punct_re.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fuzzy_match_titles(title_a: str, title_b: str, threshold: int = 90) -> int | None:
    """Return the similarity score if ``title_a`` and ``title_b`` match."""
    score = token_set_ratio(_normalize(title_a), _normalize(title_b))
    return score if score >= threshold else None
