from __future__ import annotations

import argparse
from pathlib import Path

from agent2.openai_index import build_openai_index


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for building the OpenAI embedding index."""
    parser = argparse.ArgumentParser(description="Create text embedding index")
    parser.add_argument(
        "--text-dir",
        default="data/text",
        help="Directory containing extracted text JSON files",
    )
    parser.add_argument(
        "--index",
        default="data/index.faiss",
        help="Path to write the FAISS index",
    )
    parser.add_argument(
        "--model",
        default="text-embedding-3-small",
        help="OpenAI embedding model",
    )
    args = parser.parse_args(argv)

    text_dir = Path(args.text_dir)
    index_path = Path(args.index)
    paths = list(text_dir.glob("*.json"))
    build_openai_index(paths, index_path, model=args.model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
