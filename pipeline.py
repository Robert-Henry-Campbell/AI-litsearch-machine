from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Literal
import time
from dataclasses import dataclass
from types import SimpleNamespace

try:  # resource is not available on Windows
    import resource  # type: ignore
except ImportError:  # pragma: no cover - platform specific
    resource = None  # type: ignore

try:  # fallback for memory metrics on Windows
    import psutil
except ImportError:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore

from utils.logger import get_logger

import orjson

from ingest.collector import ingest_pdf
import extract.pdf_to_text as pdf_to_text
from agent1.metadata_extractor import MetadataExtractor
import agent1.metadata_extractor as meta_mod
import aggregate
from agent2.openai_narrative import OpenAINarrative
from agent2 import retrieval


DEFAULT_TEXT_DIR = Path("data/text")
TEXT_DIR = DEFAULT_TEXT_DIR
DEFAULT_OUTPUT_DIR = Path("data/outputs")
OUTPUT_DIR = DEFAULT_OUTPUT_DIR
DEFAULT_META_DIR = meta_mod.META_DIR
DEFAULT_MASTER_PATH = aggregate.MASTER_PATH
DEFAULT_HISTORY_DIR = aggregate.HISTORY_DIR
DEFAULT_SNIPPETS_PATH = Path("data/snippets.json")
SNIPPETS_PATH = DEFAULT_SNIPPETS_PATH

logger = get_logger("pipeline")


def make_dirs(base_dir: Path) -> SimpleNamespace:
    """Return a namespace of all pipeline paths derived from ``base_dir``."""
    base = Path(base_dir)
    return SimpleNamespace(
        base=base,
        pdfs=base / "pdfs",
        text=base / "text",
        meta=base / "meta",
        outputs=base / "outputs",
        index=base / "index.faiss",
        master=base / "master.json",
        history=base / "master_history",
        snippets=base / "snippets.json",
    )


@dataclass
class StepMetrics:
    duration: float
    memory_kb: int


def get_memory_kb() -> int:
    """Return the current RSS in kilobytes."""
    if resource is not None:
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if psutil is not None:
        return int(psutil.Process().memory_info().rss / 1024)
    return 0


def ingest_pdfs(pdf_dir: str, dirs: SimpleNamespace) -> List[Path]:
    """Ingest all PDFs in *pdf_dir* and extract their text."""
    paths = []
    for pdf_path in sorted(Path(pdf_dir).glob("*.pdf")):
        entry = ingest_pdf(pdf_path)
        if entry is not None:
            paths.append(pdf_path)
        pdf_to_text.DATA_DIR = dirs.text
        pdf_to_text.pdf_to_text(pdf_path)
    return paths


def extract_metadata_from_text(
    drug_name: str, *, agent1_model: str | None = None
) -> List[Path]:
    """Run Agent 1 on all text files in ``TEXT_DIR`` using ``drug_name``."""
    extractor = (
        MetadataExtractor(model=agent1_model) if agent1_model else MetadataExtractor()
    )
    results = []
    for text_path in sorted(TEXT_DIR.glob("*.json")):
        meta = extractor.extract(text_path, drug_name)
        if meta is not None:
            results.append(text_path)
    return results


def write_agent1_batch(
    drug_name: str,
    batch_path: Path,
    *,
    agent1_model: str | None = None,
) -> Path:
    """Write a batch file for all Agent 1 requests and return the path."""
    extractor = (
        MetadataExtractor(model=agent1_model) if agent1_model else MetadataExtractor()
    )
    prompt = extractor.client.prompt
    model = extractor.client.model
    batch_path.parent.mkdir(parents=True, exist_ok=True)
    with batch_path.open("w", encoding="utf-8") as f:
        for text_path in sorted(TEXT_DIR.glob("*.json")):
            data = orjson.loads(text_path.read_bytes())
            text = extractor._join_pages(data.get("pages", []))
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ]
            entry = {
                "custom_id": text_path.stem,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": model,
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                },
            }
            f.write(orjson.dumps(entry).decode("utf-8"))
            f.write("\n")
    return batch_path


def generate_narrative(
    drug_name: str,
    *,
    agent2_model: str | None = None,
    embed_model: str | None = None,
    retrieval_method: Literal["faiss", "text"] = "faiss",
) -> Path:
    """Generate a narrative review from ``master.json`` using ``drug_name``."""
    master_path = aggregate.MASTER_PATH
    if not master_path.exists():
        raise FileNotFoundError("master.json not found. Run aggregation first.")
    metadata = orjson.loads(master_path.read_bytes())
    snippets: List[str] = []
    for record in metadata:
        doi = record.get("doi")
        if doi:
            snippets.extend(
                retrieval.get_snippets(
                    doi,
                    drug_name,
                    embed_model=embed_model,
                    method=retrieval_method,
                )
            )
    SNIPPETS_PATH.write_bytes(orjson.dumps(snippets))
    generator = (
        OpenAINarrative(model=agent2_model) if agent2_model else OpenAINarrative()
    )
    narrative = generator.generate(metadata, snippets)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / f"review_{drug_name.replace(' ', '_')}.md"
    out_file.write_text(narrative)
    return out_file


def timed_step(step_func, step_name: str, metrics: Dict[str, StepMetrics]) -> None:
    start = time.time()
    start_mem = get_memory_kb()
    step_func()
    duration = time.time() - start
    end_mem = get_memory_kb()
    mem_delta = end_mem - start_mem if end_mem and start_mem else 0
    logger.info("%s completed in %.2fs (%+d KB)", step_name, duration, mem_delta)
    metrics[step_name] = StepMetrics(duration=duration, memory_kb=mem_delta)


def run_pipeline(
    pdf_dir: str,
    drug_name: str,
    *,
    base_dir: Path = Path("data"),
    agent1_model: str | None = None,
    agent2_model: str | None = None,
    embed_model: str | None = None,
    retrieval_method: Literal["faiss", "text"] = "faiss",
    batch: bool = False,
) -> None:
    """Execute the full data processing pipeline."""
    dirs = make_dirs(base_dir)
    global TEXT_DIR, OUTPUT_DIR, SNIPPETS_PATH
    # Adjust helper module paths if they do not already point inside ``base_dir``.
    if not TEXT_DIR.resolve().is_relative_to(dirs.base):
        TEXT_DIR = dirs.text
    if not OUTPUT_DIR.resolve().is_relative_to(dirs.base):
        OUTPUT_DIR = dirs.outputs
    if not SNIPPETS_PATH.resolve().is_relative_to(dirs.base):
        SNIPPETS_PATH = dirs.snippets
    if not meta_mod.META_DIR.resolve().is_relative_to(dirs.base):
        meta_mod.META_DIR = dirs.meta
    if not aggregate.META_DIR.resolve().is_relative_to(dirs.base):
        aggregate.set_base_dir(dirs.base)
    retrieval.set_base_dir(dirs.base)
    metrics: Dict[str, StepMetrics] = {}
    timed_step(lambda: ingest_pdfs(pdf_dir, dirs), "Ingestion", metrics)
    if batch:
        batch_file = dirs.base / "agent1_batch.jsonl"
        timed_step(
            lambda: write_agent1_batch(
                drug_name, batch_file, agent1_model=agent1_model
            ),
            "Prepare Batch",
            metrics,
        )
        logger.info("Batch requests written to %s", batch_file)
        logger.info("Batch mode enabled - skipping API calls and downstream steps")
        return
    timed_step(
        lambda: extract_metadata_from_text(drug_name, agent1_model=agent1_model),
        "Metadata Extraction",
        metrics,
    )
    timed_step(lambda: aggregate.aggregate_metadata(), "Aggregation", metrics)
    timed_step(
        lambda: generate_narrative(
            drug_name,
            agent2_model=agent2_model,
            embed_model=embed_model,
            retrieval_method=retrieval_method,
        ),
        "Narrative Generation",
        metrics,
    )
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
    parser.add_argument(
        "--base-dir",
        default="data",
        help="Base output directory (default: data)",
    )
    parser.add_argument("--agent1-model", help="Model for metadata extraction")
    parser.add_argument("--agent2-model", help="Model for narrative generation")
    parser.add_argument("--embed-model", help="Model for text embeddings")
    parser.add_argument(
        "--retrieval",
        choices=["faiss", "text"],
        default="faiss",
        help="Snippet retrieval backend (default: faiss)",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Write an OpenAI batch file of Agent 1 requests and exit",
    )
    args = parser.parse_args()

    run_pipeline(
        args.pdf_dir,
        args.drug,
        base_dir=Path(args.base_dir),
        agent1_model=args.agent1_model,
        agent2_model=args.agent2_model,
        embed_model=args.embed_model,
        retrieval_method=args.retrieval,
        batch=args.batch,
    )
