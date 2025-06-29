from __future__ import annotations

from pathlib import Path
from typing import List, Dict
import time
import orjson

# openai imported lazily for tests
import openai

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "agent2_system.txt"


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
            try:
                response = openai.ChatCompletion.create(
                    model=self.model, messages=messages
                )
                content = response["choices"][0]["message"]["content"]
                return content
            except Exception:
                if attempt >= max_retries:
                    raise
                time.sleep(delay)
                delay *= 2
        raise RuntimeError("Failed to obtain narrative from OpenAI")
