from __future__ import annotations

import argparse

from pathlib import Path

import pipeline


def main(argv: list[str] | None = None) -> int:
    """Entry point for the pipeline CLI."""
    parser = argparse.ArgumentParser(description="Run MR literature pipeline.")
    parser.add_argument("--pdf_dir", required=True, help="Directory containing PDFs")
    parser.add_argument("--drug", required=True, help="Name of the drug for review")
    parser.add_argument(
        "--base_dir",
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
    args = parser.parse_args(argv)
    pipeline.run_pipeline(
        args.pdf_dir,
        args.drug,
        base_dir=Path(args.base_dir),
        agent1_model=args.agent1_model,
        agent2_model=args.agent2_model,
        embed_model=args.embed_model,
        retrieval_method=args.retrieval,
        batch=args.batch,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
