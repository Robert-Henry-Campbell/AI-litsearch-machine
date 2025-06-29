from __future__ import annotations

from pathlib import Path
from typing import List

import orjson

from ingest.collector import ingest_pdf
from extract.pdf_to_text import pdf_to_text, DATA_DIR as TEXT_DIR
from agent1.metadata_extractor import MetadataExtractor
import aggregate
from agent2.openai_narrative import OpenAINarrative
from agent2 import retrieval

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


def ingest_pdfs(pdf_dir: str) -> List[Path]:
    """Ingest all PDFs in *pdf_dir* and extract their text."""
    paths = []
    for pdf_path in sorted(Path(pdf_dir).glob("*.pdf")):
        entry = ingest_pdf(pdf_path)
        if entry is not None:
            paths.append(pdf_path)
        pdf_to_text(pdf_path)
    return paths


def extract_metadata_from_text() -> List[Path]:
    """Run Agent 1 on all text files in ``TEXT_DIR``."""
    extractor = MetadataExtractor()
    results = []
    for text_path in sorted(TEXT_DIR.glob("*.json")):
        meta = extractor.extract(text_path)
        if meta is not None:
            results.append(text_path)
    return results


def generate_narrative(drug_name: str) -> Path:
    """Generate a narrative review from ``master.json`` using ``drug_name``."""
    master_path = aggregate.MASTER_PATH
    if not master_path.exists():
        raise FileNotFoundError("master.json not found. Run aggregation first.")
    metadata = orjson.loads(master_path.read_bytes())
    snippets: List[str] = []
    for record in metadata:
        doi = record.get("doi")
        if doi:
            snippets.extend(retrieval.get_snippets(doi, drug_name))
    narrative = OpenAINarrative().generate(metadata, snippets)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / f"{drug_name.replace(' ', '_')}_review.md"
    out_file.write_text(narrative)
    return out_file


def run_pipeline(pdf_dir: str, drug_name: str) -> None:
    """Execute the full data processing pipeline."""
    ingest_pdfs(pdf_dir)
    extract_metadata_from_text()
    aggregate.aggregate_metadata()
    generate_narrative(drug_name)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the full pipeline")
    parser.add_argument("--pdf-dir", required=True, help="Directory with PDFs")
    parser.add_argument("--drug", required=True, help="Drug name for snippets")
    args = parser.parse_args()

    run_pipeline(args.pdf_dir, args.drug)
