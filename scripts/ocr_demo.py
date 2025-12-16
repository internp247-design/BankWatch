#!/usr/bin/env python3
"""Simple OCR demo: render first PDF page to image and run Tesseract via pytesseract.

Usage:
  python scripts/ocr_demo.py path/to/file.pdf

Notes:
- Requires system Tesseract OCR binary installed and accessible in PATH.
- Python deps: pytesseract, Pillow, PyMuPDF
"""
import sys
import tempfile
import os

try:
    import fitz  # PyMuPDF
    from PIL import Image
    import pytesseract
except Exception as e:
    print("Missing Python dependency:", e)
    print("Install with: pip install pytesseract PyMuPDF Pillow")
    sys.exit(2)


def ocr_pdf_first_page(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    if doc.page_count < 1:
        return "(no pages)"
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=200)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_name = tmp.name
    try:
        pix.save(tmp_name)
        img = Image.open(tmp_name)
        text = pytesseract.image_to_string(img, lang='eng')
        return text
    finally:
        try:
            os.remove(tmp_name)
        except Exception:
            pass


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/ocr_demo.py path/to/file.pdf")
        print("Defaulting to first PDF in media/statements if available.")
        default = os.path.join('media', 'statements', 'Bank_Statement_.pdf')
        path = default
    else:
        path = sys.argv[1]

    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)

    try:
        text = ocr_pdf_first_page(path)
        print("--- OCR OUTPUT START ---")
        print(text)
        print("--- OCR OUTPUT END ---")
    except pytesseract.pytesseract.TesseractNotFoundError:
        print("Tesseract binary not found. Install Tesseract and ensure it's on PATH.")
        print("See: https://github.com/tesseract-ocr/tesseract")
        sys.exit(3)
    except Exception as e:
        print("Error during OCR:", e)
        sys.exit(4)


if __name__ == '__main__':
    main()
