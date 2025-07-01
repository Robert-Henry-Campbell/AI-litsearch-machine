from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import orjson
import faiss

from .embeddings import chunk_text, embed_chunks


def build_openai_index(
    text_json_paths: List[Path],
    index_path: Path,
    *,
    model: str = "text-embedding-3-small",
    batch_size: int = 100,
) -> None:
    """Build a FAISS index from text files using OpenAI embeddings."""
    chunks: List[Dict[str, Any]] = []
    for path in text_json_paths:
        data = orjson.loads(path.read_bytes())
        pages = data.get("pages", [])
        text = " ".join(p.get("text", "") for p in pages)
        for idx, chunk in enumerate(chunk_text(text)):
            chunks.append(
                {
                    "text": chunk,
                    "chunk_id": f"{path.stem}_{idx}",
                    "doi": path.stem,
                }
            )

    if not chunks:
        return

    embeddings: List[List[float]] = []
    for start in range(0, len(chunks), batch_size):
        batch = [c["text"] for c in chunks[start : start + batch_size]]
        embeddings.extend(embed_chunks(batch, model=model))

    matrix = np.array(embeddings, dtype="float32")
    faiss.normalize_L2(matrix)
    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(matrix)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    index_path.with_suffix(".meta.json").write_bytes(orjson.dumps(chunks))


def query_index(
    doi: str,
    query: str,
    *,
    k: int = 5,
    index_path: Path | None = None,
    model: str = "text-embedding-3-small",
) -> List[Dict[str, Any]]:
    """Return top-k snippets for ``doi`` most similar to ``query``."""
    if index_path is None:
        raise ValueError("index_path is required")
    if not index_path.exists():
        raise FileNotFoundError(index_path)

    index = faiss.read_index(str(index_path))
    chunks = orjson.loads(index_path.with_suffix(".meta.json").read_bytes())

    query_vec = np.array([embed_chunks([query], model=model)[0]], dtype="float32")
    faiss.normalize_L2(query_vec)
    scores, indices = index.search(query_vec, len(chunks))

    safe = doi.replace("/", "_").replace(":", "_")
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
