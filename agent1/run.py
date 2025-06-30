from __future__ import annotations

import argparse
from pathlib import Path

from extract import pdf_to_text
from agent1.metadata_extractor import MetadataExtractor, META_DIR


def process_pdf(pdf_path: Path) -> bool:
    """Convert *pdf_path* to text and extract metadata."""
    pdf_to_text.pdf_to_text(pdf_path)
    text_path = pdf_to_text.DATA_DIR / f"{pdf_path.stem}.json"
    extractor = MetadataExtractor()
    metadata = extractor.extract(text_path, None)
    if metadata is None:
        print(f"Failed to extract metadata from {pdf_path}")
        return False
    name = MetadataExtractor._safe_name(metadata.doi, pdf_path.stem)
    out_path = META_DIR / f"{name}.json"
    print(f"Metadata saved to {out_path}")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Agent 1 on a PDF")
    parser.add_argument("--pdf", required=True, help="Path to PDF file")
    args = parser.parse_args(argv)
    success = process_pdf(Path(args.pdf))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
