from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

import orjson
import pytesseract
from PIL import Image
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextContainer
from pydantic import BaseModel

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "text"


class Page(BaseModel):
    page: int
    text: str


class PDFText(BaseModel):
    pages: List[Page]
    extracted_at: datetime


def extract_text(pdf_path: Path) -> list[str]:
    laparams = LAParams()
    texts: list[str] = []
    for page_layout in extract_pages(str(pdf_path), laparams=laparams):
        page_text = "".join(
            element.get_text()
            for element in page_layout
            if isinstance(element, LTTextContainer)
        ).strip()
        texts.append(page_text)
    return texts


def ocr_text(pdf_path: Path, existing: list[str]) -> list[str]:
    with Image.open(pdf_path) as img:
        for i in range(img.n_frames):
            img.seek(i)
            text = pytesseract.image_to_string(img)
            if i < len(existing):
                existing[i] = text.strip()
            else:
                existing.append(text.strip())
    return existing


def pdf_to_text(path: str | Path) -> PDFText:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = Path(path)
    texts = extract_text(pdf_path)
    blank_pages = sum(1 for t in texts if not t)
    if texts and blank_pages / len(texts) > 0.5:
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            pass
        else:
            texts = ocr_text(pdf_path, texts)
    data = PDFText(
        pages=[Page(page=i + 1, text=txt) for i, txt in enumerate(texts)],
        extracted_at=datetime.utcnow(),
    )
    out_path = DATA_DIR / f"{pdf_path.stem}.json"
    out_path.write_bytes(orjson.dumps(data.model_dump()))
    return data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract text from PDF")
    parser.add_argument("pdf", type=str)
    args = parser.parse_args()
    result = pdf_to_text(args.pdf)
    print(orjson.dumps(result.model_dump()).decode())
