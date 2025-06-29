from pathlib import Path
from shutil import which
import pytesseract

import pytest
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from extract.pdf_to_text import pdf_to_text


def create_digital_pdf(path: Path, pages: int = 2) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    for i in range(pages):
        c.drawString(100, 750, f"Page {i + 1} text")
        c.showPage()
    c.save()


def create_scanned_pdf(path: Path) -> None:
    img = Image.new("RGB", (200, 200), "white")
    d = ImageDraw.Draw(img)
    d.text((10, 10), "Scanned text", fill="black")
    img.save(path, "PDF")


def test_extract_digital_pdf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("extract.pdf_to_text.DATA_DIR", tmp_path)
    pdf = tmp_path / "digital.pdf"
    create_digital_pdf(pdf, pages=2)
    result = pdf_to_text(pdf)
    assert len(result.pages) == 2
    assert all(page.text for page in result.pages)


def test_ocr_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if which("tesseract") is None:
        pytest.skip("tesseract not available")
    monkeypatch.setattr("extract.pdf_to_text.DATA_DIR", tmp_path)
    pdf = tmp_path / "scan.pdf"
    create_scanned_pdf(pdf)
    result = pdf_to_text(pdf)
    assert any("Scanned text" in page.text for page in result.pages)


def test_no_tesseract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("extract.pdf_to_text.DATA_DIR", tmp_path)

    def raise_error(*args, **kwargs):
        raise pytesseract.TesseractNotFoundError()

    monkeypatch.setattr("pytesseract.get_tesseract_version", raise_error)

    pdf = tmp_path / "scan_missing.pdf"
    create_scanned_pdf(pdf)

    result = pdf_to_text(pdf)
    assert len(result.pages) == 1
