from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import orjson
import time

# openai is imported lazily in tests via a stub if not installed
import openai

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "agent1_prompt.txt"


class OpenAIJSONCaller:
    """Helper for calling OpenAI's chat completion API in JSON mode."""

    def __init__(self, model: str = "gpt-4-0125-preview") -> None:
        self.model = model
        self.prompt = PROMPT_PATH.read_text()

    def call(self, user_content: str, *, max_retries: int = 2) -> Dict[str, Any]:
        """Send ``user_content`` to the model and parse the JSON reply."""
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": user_content},
        ]
        delay = 1.0
        for attempt in range(max_retries + 1):
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            content = response["choices"][0]["message"]["content"]
            try:
                return orjson.loads(content)
            except orjson.JSONDecodeError:
                if attempt >= max_retries:
                    raise
                time.sleep(delay)
                delay *= 2
        # Should never reach here
        raise RuntimeError("Failed to obtain JSON from OpenAI")
