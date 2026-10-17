#!/usr/bin/env python3
"""
pdf_to_text.py - Convert PDF files to plain text.

Usage:
    python pdf_to_text.py input.pdf                  # writes input.txt
    python pdf_to_text.py input.pdf -o output.txt    # custom output path
    python pdf_to_text.py folder/                    # converts every PDF in a folder
    python pdf_to_text.py scanned.pdf --ocr          # OCR for scanned/image PDFs
    python pdf_to_text.py input.pdf --pages 1-5      # only pages 1 to 5

Install:
    pip install pdfplumber pypdf
    # Only for --ocr:
    pip install pytesseract pdf2image
    # plus system packages: tesseract-ocr and poppler-utils
"""

import argparse
import sys
from pathlib import Path


def parse_page_range(spec, total):
    """Turn '1-5' or '3' into a list of zero-based page indexes."""
    if not spec:
        return list(range(total))
    if "-" in spec:
        start, end = spec.split("-", 1)
        start = int(start) if start else 1
        end = int(end) if end else total
    else:
        start = end = int(spec)
    start = max(start, 1)
    end = min(end, total)
    return list(range(start - 1, end))


def extract_with_pdfplumber(pdf_path, pages_spec=None):
    import pdfplumber

    chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for i in parse_page_range(pages_spec, len(pdf.pages)):
            text = pdf.pages[i].extract_text() or ""
            chunks.append(f"--- Page {i + 1} ---\n{text}")
    return "\n\n".join(chunks)


def extract_with_pypdf(pdf_path, pages_spec=None):
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    chunks = []
    for i in parse_page_range(pages_spec, len(reader.pages)):
        text = reader.pages[i].extract_text() or ""
        chunks.append(f"--- Page {i + 1} ---\n{text}")
    return "\n\n".join(chunks)


def extract_with_ocr(pdf_path, pages_spec=None, lang="eng"):
    import pytesseract
    from pdf2image import convert_from_path

    images = convert_from_path(pdf_path, dpi=300)
    chunks = []
    for i in parse_page_range(pages_spec, len(images)):
        text = pytesseract.image_to_string(images[i], lang=lang)
        chunks.append(f"--- Page {i + 1} ---\n{text}")
    return "\n\n".join(chunks)


def has_real_text(text):
    """True if extraction produced more than just page markers."""
    body = "\n".join(
        line for line in text.splitlines() if not line.startswith("--- Page ")
    )
    return len(body.strip()) > 20


def convert(pdf_path, out_path, use_ocr=False, pages_spec=None, lang="eng"):
    if use_ocr:
        text = extract_with_ocr(pdf_path, pages_spec, lang)
    else:
        try:
            text = extract_with_pdfplumber(pdf_path, pages_spec)
        except Exception as e:
            print(f"  pdfplumber failed ({e}); trying pypdf...", file=sys.stderr)
            text = extract_with_pypdf(pdf_path, pages_spec)

        if not has_real_text(text):
            print(
                "  Warning: little or no text found. This may be a scanned PDF; "
                "try again with --ocr.",
                file=sys.stderr,
            )

    out_path.write_text(text, encoding="utf-8")
    print(f"Saved: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Convert PDF files to text.")
    parser.add_argument("input", help="PDF file or folder containing PDFs")
    parser.add_argument("-o", "--output", help="Output .txt file (single file only)")
    parser.add_argument("--ocr", action="store_true", help="Use OCR for scanned PDFs")
    parser.add_argument("--lang", default="eng", help="OCR language (default: eng)")
    parser.add_argument("--pages", help="Page range, e.g. 1-5 or 3")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        sys.exit(f"Error: '{src}' does not exist.")

    if src.is_dir():
        pdfs = sorted(src.glob("*.pdf"))
        if not pdfs:
            sys.exit(f"No PDF files found in '{src}'.")
        for pdf in pdfs:
            print(f"Converting {pdf.name}...")
            try:
                convert(pdf, pdf.with_suffix(".txt"), args.ocr, args.pages, args.lang)
            except Exception as e:
                print(f"  Failed: {e}", file=sys.stderr)
    else:
        out = Path(args.output) if args.output else src.with_suffix(".txt")
        convert(src, out, args.ocr, args.pages, args.lang)


if __name__ == "__main__":
    main()