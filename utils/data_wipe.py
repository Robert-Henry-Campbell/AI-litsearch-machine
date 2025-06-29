from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Allow running this file directly without installing the package
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import aggregate  # noqa: E402
from ingest.collector import LOG_PATH  # noqa: E402
from ingest.list_pdfs import DATA_DIR as PDF_DIR  # noqa: E402
from extract.pdf_to_text import DATA_DIR as TEXT_DIR  # noqa: E402
from agent1.metadata_extractor import META_DIR  # noqa: E402
from pipeline import OUTPUT_DIR  # noqa: E402


def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def wipe_data(delete_pdfs: bool = False) -> None:
    """Delete generated data files and directories.

    Parameters
    ----------
    delete_pdfs:
        If ``True``, also remove all PDFs under ``data/pdfs``.
    """

    targets = [
        META_DIR,
        TEXT_DIR,
        aggregate.HISTORY_DIR,
        OUTPUT_DIR,
    ]
    files = [
        aggregate.MASTER_PATH,
        aggregate.ERROR_LOG,
        LOG_PATH,
    ]
    for path in targets:
        _remove(path)
    for path in files:
        _remove(path)
    if delete_pdfs and PDF_DIR.exists():
        shutil.rmtree(PDF_DIR)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Remove generated data and logs")
    parser.add_argument(
        "--with-pdfs",
        action="store_true",
        help="Also delete files in data/pdfs",
    )
    args = parser.parse_args(argv)
    wipe_data(delete_pdfs=args.with_pdfs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
