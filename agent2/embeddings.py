from __future__ import annotations

from typing import List
import time

import openai
from openai import OpenAI

from utils.logger import get_logger, format_exception
from utils.secrets import get_openai_api_key

_client: OpenAI | None = None


def get_client() -> OpenAI:
    """Return a cached OpenAI client."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=get_openai_api_key())
    return _client


try:  # OpenAI SDK v1.x
    AuthError = openai.AuthenticationError
    RateLimitError = openai.RateLimitError
except AttributeError:  # pragma: no cover - fallback
    errors = getattr(openai, "error", type("error", (), {}))
    AuthError = getattr(errors, "AuthenticationError", Exception)
    RateLimitError = getattr(errors, "RateLimitError", Exception)


logger = get_logger(__name__)


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    """Split text into overlapping chunks of approximately ``chunk_size`` tokens."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap >= chunk_size or overlap < 0:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    tokens = text.split()
    chunks: List[str] = []
    step = chunk_size - overlap
    for start in range(0, len(tokens), step):
        end = start + chunk_size
        chunk = " ".join(tokens[start:end])
        if chunk:
            chunks.append(chunk)
    return chunks


def embed_chunks(
    chunks: List[str], *, model: str = "text-embedding-3-small"
) -> List[List[float]]:
    """Generate embeddings for each text chunk using OpenAI's embeddings API."""
    if not chunks:
        return []

    client = get_client()
    delay = 1.0
    for attempt in range(3):
        start_time = time.time()
        try:
            response = client.embeddings.create(
                model=model,
                input=chunks,
            )
        except AuthError as exc:  # pragma: no cover - auth errors
            duration = time.time() - start_time
            logger.error("Authentication failed after %.2fs: %s", duration, exc)
            raise
        except RateLimitError as exc:  # pragma: no cover - rate limit
            duration = time.time() - start_time
            logger.warning(
                "Rate limit hit on attempt %s after %.2fs: %s",
                attempt + 1,
                duration,
                exc,
            )
            if attempt >= 2:
                raise
            time.sleep(delay)
            delay *= 2
            continue
        except Exception as exc:  # pragma: no cover - network errors
            duration = time.time() - start_time
            logger.error(
                "Embedding request failed on attempt %s after %.2fs (%s)",
                attempt + 1,
                duration,
                format_exception(exc),
            )
            if attempt >= 2:
                raise
            time.sleep(delay)
            delay *= 2
            continue

        duration = time.time() - start_time
        logger.info("Embedding generation succeeded in %.2fs", duration)
        return [d.embedding for d in response.data]

    raise RuntimeError("Failed to generate embeddings")
