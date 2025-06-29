from __future__ import annotations

import logging
from hashlib import md5
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Union

import orjson
from pydantic import ValidationError

from agent1.openai_client import OpenAIJSONCaller
from schemas.metadata import PaperMetadata

META_DIR = Path(__file__).resolve().parents[1] / "data" / "meta"


class MetadataExtractor:
    """Extract metadata from text using OpenAI and validate against schema."""

    def __init__(self, client: Optional[OpenAIJSONCaller] = None) -> None:
        self.client = client or OpenAIJSONCaller()
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
        return out_path

    def extract(self, text_or_path: Union[str, Path]) -> Optional[PaperMetadata]:
        text, src_path = self._load_text(text_or_path)
        for attempt in range(2):
            try:
                result = self.client.call(text)
                metadata = PaperMetadata.model_validate(result)
            except (ValidationError, Exception) as exc:
                logging.error("Validation failed on attempt %s: %s", attempt + 1, exc)
                if attempt == 1:
                    return None
            else:
                self._save(metadata, src_path, text)
                return metadata
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract metadata using OpenAI")
    parser.add_argument("text", help="Raw text or path to text JSON")
    args = parser.parse_args()

    extractor = MetadataExtractor()
    result = extractor.extract(args.text)
    if result is None:
        print("Extraction failed")
    else:
        print(orjson.dumps(result.model_dump()).decode())
