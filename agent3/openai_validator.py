from __future__ import annotations

from pathlib import Path
import time

from openai import OpenAI

from utils.logger import get_logger
from utils.secrets import get_openai_api_key

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "agent3_system.txt"

logger = get_logger(__name__)

_client: OpenAI | None = None
_assistant_id: str | None = None
_assistant_model: str | None = None


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
    value1: str, value2: str, field_name: str, model: str = "gpt-4o"
) -> bool:
    """Return ``True`` if the two values appear logically inconsistent."""
    _init_assistant(model)
    client = _get_client()
    user = f"Field: {field_name}\nValue 1: {value1}\nValue 2: {value2}"
    thread = client.beta.threads.create(messages=[{"role": "user", "content": user}])
    run = client.beta.threads.runs.create(
        thread_id=thread.id, assistant_id=_assistant_id
    )
    _wait_for_run(client, thread.id, run.id)
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    answer = messages.data[0].content[0].text.value.strip().lower()
    if answer.startswith("yes"):
        return True
    if answer.startswith("no"):
        return False
    raise RuntimeError(f"Unexpected reply: {answer}")
