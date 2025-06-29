from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import time
import resource
from dataclasses import dataclass

from utils.logger import get_logger

import orjson

from ingest.collector import ingest_pdf
from extract.pdf_to_text import pdf_to_text, DATA_DIR as TEXT_DIR
from agent1.metadata_extractor import MetadataExtractor
import aggregate
from agent2.openai_narrative import OpenAINarrative
from agent2 import retrieval

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"

logger = get_logger("pipeline")


@dataclass
class StepMetrics:
    duration: float
    memory_kb: int


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
    out_file = OUTPUT_DIR / f"review_{drug_name.replace(' ', '_')}.md"
    out_file.write_text(narrative)
    return out_file


def timed_step(step_func, step_name: str, metrics: Dict[str, StepMetrics]) -> None:
    start = time.time()
    start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    step_func()
    duration = time.time() - start
    end_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    mem_delta = end_mem - start_mem
    logger.info("%s completed in %.2fs (%+d KB)", step_name, duration, mem_delta)
    metrics[step_name] = StepMetrics(duration=duration, memory_kb=mem_delta)


def run_pipeline(pdf_dir: str, drug_name: str) -> None:
    """Execute the full data processing pipeline."""
    metrics: Dict[str, StepMetrics] = {}
    timed_step(lambda: ingest_pdfs(pdf_dir), "Ingestion", metrics)
    timed_step(extract_metadata_from_text, "Metadata Extraction", metrics)
    timed_step(aggregate.aggregate_metadata, "Aggregation", metrics)
    timed_step(lambda: generate_narrative(drug_name), "Narrative Generation", metrics)
    logger.info("-- Performance Summary --")
    for name, data in sorted(
        metrics.items(), key=lambda x: x[1].duration, reverse=True
    ):
        logger.info("%-20s %.2fs %+d KB", name, data.duration, data.memory_kb)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the full pipeline")
    parser.add_argument("--pdf-dir", required=True, help="Directory with PDFs")
    parser.add_argument("--drug", required=True, help="Drug name for snippets")
    args = parser.parse_args()

    run_pipeline(args.pdf_dir, args.drug)
