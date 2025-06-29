from __future__ import annotations

import argparse

import pipeline


def main(argv: list[str] | None = None) -> int:
    """Entry point for the pipeline CLI."""
    parser = argparse.ArgumentParser(description="Run MR literature pipeline.")
    parser.add_argument("--pdf_dir", required=True, help="Directory containing PDFs")
    parser.add_argument("--drug", required=True, help="Name of the drug for review")
    args = parser.parse_args(argv)
    pipeline.run_pipeline(args.pdf_dir, args.drug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
