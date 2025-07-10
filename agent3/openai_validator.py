from __future__ import annotations

from pathlib import Path
import time

import openai
from openai import OpenAI

from utils.logger import get_logger, format_exception
from utils.secrets import get_openai_api_key

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "agent3_system.txt"

logger = get_logger(__name__)

_client: OpenAI | None = None
_assistant_id: str | None = None
_assistant_model: str | None = None

try:  # OpenAI SDK v1.x
    AuthError = openai.AuthenticationError
    RateLimitError = openai.RateLimitError
except AttributeError:  # pragma: no cover - fallback
    errors = getattr(openai, "error", type("error", (), {}))
    AuthError = getattr(errors, "AuthenticationError", Exception)
    RateLimitError = getattr(errors, "RateLimitError", Exception)


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=get_openai_api_key())
    return _client


def _init_assistant(model: str) -> None:
    global _assistant_id, _assistant_model
    if _assistant_id is None or _assistant_model != model:
        with PROMPT_PATH.open("r", encoding="utf-8") as f:
            prompt = f.read()
        client = _get_client()
        assistant = client.beta.assistants.create(instructions=prompt, model=model)
        _assistant_id = assistant.id
        _assistant_model = model


def _wait_for_run(client: OpenAI, thread_id: str, run_id: str) -> None:
    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        status = run.status
        if status == "completed":
            return
        if status in {"failed", "cancelled", "expired"}:
            raise RuntimeError(f"Run {run_id} ended with status {status}")
        time.sleep(0.25)


# Create assistant at import using default model
_init_assistant("gpt-4o")


def is_conflict(
    value1: str,
    value2: str,
    field_name: str,
    model: str = "gpt-4o",
    *,
    max_retries: int = 2,
) -> bool:
    """Return ``True`` if the two values appear logically inconsistent."""
    _init_assistant(model)
    client = _get_client()
    user = f"Field: {field_name}\nValue 1: {value1}\nValue 2: {value2}"
    delay = 1.0
    for attempt in range(max_retries + 1):
        try:
            thread = client.beta.threads.create(
                messages=[{"role": "user", "content": user}]
            )
            run = client.beta.threads.runs.create(
                thread_id=thread.id, assistant_id=_assistant_id
            )
            _wait_for_run(client, thread.id, run.id)
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            answer = messages.data[0].content[0].text.value.strip().lower()
        except AuthError as exc:  # pragma: no cover - auth errors
            logger.error("Authentication failed on attempt %s: %s", attempt + 1, exc)
            raise
        except RateLimitError as exc:  # pragma: no cover - rate limit
            logger.warning("Rate limit hit on attempt %s: %s", attempt + 1, exc)
            if attempt >= max_retries:
                raise
        except Exception as exc:  # pragma: no cover - network errors
            logger.error(
                "OpenAI request failed on attempt %s (%s)",
                attempt + 1,
                format_exception(exc),
            )
            if attempt >= max_retries:
                raise
        else:
            if answer.startswith("yes"):
                return True
            if answer.startswith("no"):
                return False
            raise RuntimeError(f"Unexpected reply: {answer}")
        time.sleep(delay)
        delay *= 2
    raise RuntimeError("Failed to obtain conflict judgement")
