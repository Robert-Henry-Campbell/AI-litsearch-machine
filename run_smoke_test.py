from pathlib import Path

from extract.pdf_to_text import pdf_to_text
from ingest.collector import ingest_pdf


def smoke_test(pdf_path: Path) -> None:
    ingest_pdf(pdf_path)
    data = pdf_to_text(pdf_path)
    for page in data.pages:
        snippet = page.text[:300].replace("\n", " ")
        print(f"Page {page.page}: {snippet}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run smoke test")
    parser.add_argument("pdf", type=str)
    args = parser.parse_args()
    smoke_test(Path(args.pdf))
