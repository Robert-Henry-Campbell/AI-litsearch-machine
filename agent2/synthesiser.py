from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Dict

import orjson

from agent2 import retrieval
from agent2.openai_narrative import OpenAINarrative

BASE_DIR = Path("data")
MASTER_PATH = BASE_DIR / "master.json"
OUTPUT_DIR = BASE_DIR / "outputs"
SNIPPETS_PATH = BASE_DIR / "snippets.json"


def set_base_dir(base_dir: Path) -> None:
    global BASE_DIR, MASTER_PATH, OUTPUT_DIR, SNIPPETS_PATH
    BASE_DIR = Path(base_dir)
    MASTER_PATH = BASE_DIR / "master.json"
    OUTPUT_DIR = BASE_DIR / "outputs"
    SNIPPETS_PATH = BASE_DIR / "snippets.json"


def load_master() -> List[Dict]:
    """Load and return list of metadata records from ``master.json``."""
    if not MASTER_PATH.exists():
        raise FileNotFoundError(f"Master file not found: {MASTER_PATH}")
    data = orjson.loads(MASTER_PATH.read_bytes())
    if not isinstance(data, list):
        raise ValueError("master.json must contain a list")
    return data


def filter_by_drug(records: List[Dict], drug: str) -> List[Dict]:
    """Return records where ``drug`` is listed in ``targets``."""
    result: List[Dict] = []
    for rec in records:
        targets = rec.get("targets") or []
        if any(drug.lower() == str(t).lower() for t in targets):
            result.append(rec)
    return result


def collect_snippets(records: List[Dict], drug: str) -> List[str]:
    snippets: List[str] = []
    for rec in records:
        doi = rec.get("doi")
        if doi:
            snippets.extend(retrieval.get_snippets(doi, drug))
    return snippets


def synthesise(drug: str) -> Path:
    """Generate a narrative review for ``drug`` and return output path."""
    records = filter_by_drug(load_master(), drug)
    if not records:
        raise ValueError(f"No studies found for {drug}")
    snippets = collect_snippets(records, drug)
    SNIPPETS_PATH.write_bytes(orjson.dumps(snippets))
    generator = OpenAINarrative()
    narrative = generator.generate(records, snippets)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"review_{drug.replace(' ', '_')}.md"
    out_path.write_text(narrative)
    return out_path


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a narrative review")
    parser.add_argument("--drug", required=True, help="Drug name")
    args = parser.parse_args(argv)
    try:
        synthesise(args.drug)
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
