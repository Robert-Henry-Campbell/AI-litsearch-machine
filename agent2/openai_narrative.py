from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import time
import orjson

from utils.logger import get_logger, format_exception

# openai imported lazily for tests
import openai

AuthError = getattr(openai, "error", type("error", (), {})).__dict__.get(
    "AuthenticationError", Exception
)
RateLimitError = getattr(openai, "error", type("error", (), {})).__dict__.get(
    "RateLimitError", Exception
)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "agent2_system.txt"


logger = get_logger(__name__)


class OpenAINarrative:
    """Helper for generating narrative reviews using OpenAI."""

    def __init__(self, model: str = "gpt-4-0125-preview") -> None:
        self.model = model
        self.prompt = PROMPT_PATH.read_text()

    @staticmethod
    def _format_input(metadata: List[Dict], snippets: List[str]) -> str:
        meta_json = orjson.dumps(metadata, option=orjson.OPT_INDENT_2).decode()
        snippet_text = "\n".join(f"- {s}" for s in snippets)
        return f"Metadata:\n```json\n{meta_json}\n```\n\nSnippets:\n{snippet_text}"

    def generate(
        self, metadata: List[Dict], snippets: List[str], *, max_retries: int = 2
    ) -> str:
        """Generate a narrative review from ``metadata`` and ``snippets``."""
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": self._format_input(metadata, snippets)},
        ]
        delay = 1.0
        for attempt in range(max_retries + 1):
            start_time = time.time()
            try:
                response = openai.ChatCompletion.create(
                    model=self.model, messages=messages
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
                    "Narrative generation failed on attempt %s after %.2fs (%s)",
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
            usage = response.get("usage")
            logger.info("API Call Duration: %.2fs", duration)
            if usage:
                logger.info(
                    "Tokens used: prompt=%s completion=%s total=%s",
                    usage.get("prompt_tokens"),
                    usage.get("completion_tokens"),
                    usage.get("total_tokens"),
                )
            content = response["choices"][0]["message"]["content"]
            logger.info("Narrative generation succeeded")
            return content
        raise RuntimeError("Failed to obtain narrative from OpenAI")
