from __future__ import annotations

from pathlib import Path
import os


def get_openai_api_key() -> str:
    """Return the OpenAI API key from env or secret file.

    The function first checks the ``OPENAI_API_KEY`` environment variable. If not
    set, it looks for a file specified by ``OPENAI_API_KEY_FILE`` or the Docker
    secret ``/run/secrets/openai_api_key``. If the key cannot be found, a
    ``RuntimeError`` is raised.
    """

    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key.strip()

    file_env = os.getenv("OPENAI_API_KEY_FILE")
    paths = [Path(file_env)] if file_env else []
    paths.append(Path("/run/secrets/openai_api_key"))

    for path in paths:
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()

    raise RuntimeError(
        "OPENAI_API_KEY not found as environment variable or secret file"
    )
