from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any
import pickle

import orjson
from sklearn.feature_extraction.text import TfidfVectorizer
import faiss


def _safe_name(doi: str) -> str:
    return doi.replace("/", "_").replace(":", "_")


def _chunk_text(text: str, size: int = 200) -> List[str]:
    words = text.split()
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)]


def build_vector_index(text_json_paths: List[Path], index_path: Path) -> None:
    """Build a FAISS embedding index from extracted text JSON files."""
    chunks: List[Dict[str, Any]] = []
    for path in text_json_paths:
        data = orjson.loads(path.read_bytes())
        pages = data.get("pages", [])
        text = " ".join(p.get("text", "") for p in pages)
        for idx, chunk in enumerate(_chunk_text(text)):
            chunks.append(
                {
                    "text": chunk,
                    "chunk_id": f"{path.stem}_{idx}",
                    "doi": path.stem,
                }
            )

    if not chunks:
        return

    corpus = [c["text"] for c in chunks]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(corpus)
    embeddings = matrix.toarray().astype("float32")
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    index_path.with_suffix(".meta.json").write_bytes(orjson.dumps(chunks))
    with open(index_path.with_suffix(".vec"), "wb") as f:
        pickle.dump(vectorizer, f)


def query_index(
    doi: str, query: str, k: int = 5, index_path: Path | None = None
) -> List[Dict[str, Any]]:
    """Retrieve top-k semantically relevant text snippets from a single document identified by DOI."""
    if index_path is None:
        raise ValueError("index_path is required")
    if not index_path.exists():
        raise FileNotFoundError(index_path)

    index = faiss.read_index(str(index_path))
    chunks = orjson.loads(index_path.with_suffix(".meta.json").read_bytes())
    with open(index_path.with_suffix(".vec"), "rb") as f:
        vectorizer: TfidfVectorizer = pickle.load(f)

    query_vec = vectorizer.transform([query]).toarray().astype("float32")
    faiss.normalize_L2(query_vec)
    scores, indices = index.search(query_vec, len(chunks))

    safe = _safe_name(doi)
    results: List[Dict[str, Any]] = []
    for idx, score in zip(indices[0], scores[0]):
        if idx == -1:
            continue
        meta = chunks[idx]
        if meta["doi"] != safe:
            continue
        results.append(
            {
                "text": meta["text"],
                "score": float(score),
                "chunk_id": meta["chunk_id"],
            }
        )
        if len(results) >= k:
            break
    return results
