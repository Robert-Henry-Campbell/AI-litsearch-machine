from __future__ import annotations

import argparse
from pathlib import Path

from agent2.openai_index import build_openai_index


def main(argv: list[str] | None = None) -> int:
    """CLI for creating the embedding index under a base directory."""
    parser = argparse.ArgumentParser(description="Build embeddings index")
    parser.add_argument(
        "--base_dir",
        default="data",
        help="Pipeline base directory (default: data)",
    )
    parser.add_argument(
        "--model",
        default="text-embedding-3-small",
        help="OpenAI embedding model",
    )
    args = parser.parse_args(argv)

    base = Path(args.base_dir)
    text_dir = base / "text"
    index_path = base / "index.faiss"
    paths = list(text_dir.glob("*.json"))
    build_openai_index(paths, index_path, model=args.model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
