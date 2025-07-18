from __future__ import annotations

import time
from hashlib import md5
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Union

import orjson
from pydantic import ValidationError

from utils.logger import get_logger, format_exception

from agent1.openai_client import OpenAIJSONCaller, _usage_get
from schemas.metadata import PaperMetadata

META_DIR = Path(__file__).resolve().parents[1] / "data" / "meta"


logger = get_logger(__name__)


class MetadataExtractor:
    """Extract metadata from text using OpenAI and validate against schema."""

    def __init__(
        self,
        client: Optional[OpenAIJSONCaller] = None,
        *,
        model: str = "gpt-4o-2024-05-13",
    ) -> None:
        self.client = client or OpenAIJSONCaller(model=model)
        META_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _join_pages(pages: Iterable[Dict[str, Any]]) -> str:
        return "\n".join(page.get("text", "") for page in pages)

    def _load_text(self, text_or_path: Union[str, Path]) -> tuple[str, Optional[Path]]:
        path = Path(text_or_path)
        if path.exists():
            data = orjson.loads(path.read_bytes())
            text = self._join_pages(data.get("pages", []))
            return text, path
        return str(text_or_path), None

    @staticmethod
    def _safe_name(doi: Optional[str], fallback: str) -> str:
        if doi:
            return doi.replace("/", "_").replace(":", "_")
        digest = md5(fallback.encode(), usedforsecurity=False).hexdigest()[:8]
        return f"no-doi-{digest}"

    def _save(
        self, metadata: PaperMetadata, text_path: Optional[Path], raw_text: str
    ) -> Path:
        name = self._safe_name(
            metadata.doi, text_path.stem if text_path else raw_text[:10]
        )
        out_path = META_DIR / f"{name}.json"
        out_path.write_bytes(orjson.dumps(metadata.model_dump()))

        if text_path is not None:
            new_text_path = text_path.with_name(f"{name}.json")
            if new_text_path != text_path:
                try:
                    text_path.rename(new_text_path)
                except FileExistsError:
                    pass
        return out_path

    def extract(
        self, text_or_path: Union[str, Path], drug_name: str | None = None
    ) -> Optional[PaperMetadata]:
        """Extract metadata from ``text_or_path``.

        If ``drug_name`` is provided, ``metadata.targets`` is set to ``[drug_name]``
        after validation.
        """
        text, src_path = self._load_text(text_or_path)
        for attempt in range(2):
            start = time.time()
            try:
                result = self.client.call(text)
                metadata = PaperMetadata.model_validate(result)
                if drug_name is not None:
                    metadata.targets = [drug_name]
            except (ValidationError, Exception) as exc:
                duration = time.time() - start
                logger.error(
                    "Validation failed on attempt %s after %.2fs (%s)",
                    attempt + 1,
                    duration,
                    format_exception(exc),
                )
                usage = getattr(self.client, "last_usage", None)
                if usage:
                    logger.info(
                        "Tokens used: prompt=%s completion=%s total=%s",
                        _usage_get(usage, "prompt_tokens"),
                        _usage_get(usage, "completion_tokens"),
                        _usage_get(usage, "total_tokens"),
                    )
                if attempt == 1:
                    return None
            else:
                duration = time.time() - start
                logger.info("API Call Duration: %.2fs", duration)
                usage = getattr(self.client, "last_usage", None)
                if usage:
                    logger.info(
                        "Tokens used: prompt=%s completion=%s total=%s",
                        _usage_get(usage, "prompt_tokens"),
                        _usage_get(usage, "completion_tokens"),
                        _usage_get(usage, "total_tokens"),
                    )
                self._save(metadata, src_path, text)
                return metadata
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract metadata using OpenAI")
    parser.add_argument("text", help="Raw text or path to text JSON")
    args = parser.parse_args()

    extractor = MetadataExtractor()
    result = extractor.extract(args.text, None)
    if result is None:
        print("Extraction failed")
    else:
        print(orjson.dumps(result.model_dump()).decode())
