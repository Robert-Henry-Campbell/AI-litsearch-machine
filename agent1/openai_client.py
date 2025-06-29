from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import orjson
import time

from utils.logger import get_logger, format_exception
from utils.secrets import get_openai_api_key

# openai is imported lazily in tests via a stub if not installed
import openai
from openai import OpenAI

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
except AttributeError:  # pragma: no cover - fallback for older SDKs
    errors = getattr(openai, "error", type("error", (), {}))
    AuthError = getattr(errors, "AuthenticationError", Exception)
    RateLimitError = getattr(errors, "RateLimitError", Exception)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "agent1_prompt.txt"


logger = get_logger(__name__)


class OpenAIJSONCaller:
    """Helper for calling OpenAI's chat completion API in JSON mode."""

    def __init__(self, model: str = "gpt-4-0125-preview") -> None:
        self.model = model
        with PROMPT_PATH.open("r", encoding="utf-8") as f:
            self.prompt = f.read()
        self.last_usage: Dict[str, int] | None = None

    def call(self, user_content: str, *, max_retries: int = 2) -> Dict[str, Any]:
        """Send ``user_content`` to the model and parse the JSON reply."""
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": user_content},
        ]
        delay = 1.0
        client = get_client()
        for attempt in range(max_retries + 1):
            start_time = time.time()
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                )
            except AuthError as exc:  # pragma: no cover - auth errors
                duration = time.time() - start_time
                logger.error(
                    "Authentication failed after %.2fs: %s",
                    duration,
                    exc,
                )
                raise
            except RateLimitError as exc:  # pragma: no cover - rate limit
                duration = time.time() - start_time
                logger.warning(
                    "Rate limit hit on attempt %s after %.2fs: %s",
                    attempt + 1,
                    duration,
                    exc,
                )
                if attempt >= max_retries:
                    raise
                time.sleep(delay)
                delay *= 2
                continue
            except Exception as exc:  # pragma: no cover - network errors
                duration = time.time() - start_time
                logger.error(
                    "OpenAI request failed on attempt %s after %.2fs (%s)",
                    attempt + 1,
                    duration,
                    format_exception(exc),
                )
                if attempt >= max_retries:
                    raise
                time.sleep(delay)
                delay *= 2
                continue

            duration = time.time() - start_time
            self.last_usage = response.usage
            logger.info("API Call Duration: %.2fs", duration)
            if self.last_usage:
                logger.info(
                    "Tokens used: prompt=%s completion=%s total=%s",
                    self.last_usage.get("prompt_tokens"),
                    self.last_usage.get("completion_tokens"),
                    self.last_usage.get("total_tokens"),
                )
            content = response.choices[0].message.content
            try:
                result = orjson.loads(content)
            except orjson.JSONDecodeError as exc:
                logger.error(
                    "JSON decode error on attempt %s (%s)",
                    attempt + 1,
                    format_exception(exc),
                )
                if attempt >= max_retries:
                    raise
                time.sleep(delay)
                delay *= 2
            else:
                logger.info("OpenAI call succeeded")
                return result
        # Should never reach here
        raise RuntimeError("Failed to obtain JSON from OpenAI")
