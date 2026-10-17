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
from PdfExtractor import PdfExtractor

def main():
    parser = argparse.ArgumentParser(description="Convert PDF files to text.")
    parser.add_argument("input", help="PDF file or folder containing PDFs")
    parser.add_argument("-o", "--output", help="Output .txt file (single file only)")
    parser.add_argument("--ocr", action="store_true", help="Use OCR for scanned PDFs")
    parser.add_argument("--lang", default="eng", help="OCR language (default: eng)")
    parser.add_argument("--pages", help="Page range, e.g. 1-5 or 3")
    args = parser.parse_args()

    path_argument = args.input
    argument_ocr = args.ocr
    argument_pages = args.pages
    argument_lang = args.lang
    argument_output = args.output

    pdf_extractor = PdfExtractor()

    src = Path(path_argument)
    if not src.exists():
        sys.exit(f"Error: '{src}' does not exist.")

    if src.is_dir():
        pdfs = sorted(src.glob("*.pdf"))
        if not pdfs:
            sys.exit(f"No PDF files found in '{src}'.")
        for pdf in pdfs:
            print(f"Converting {pdf.name}...")
            try:
                pdf_extractor.convert(pdf, pdf.with_suffix(".txt"), argument_ocr, argument_pages, args.lang)
            except Exception as e:
                print(f"  Failed: {e}", file=sys.stderr)
    else:
        out = Path(argument_output) if argument_output else src.with_suffix(".txt")
        pdf_extractor.convert(src, out, argument_ocr, argument_pages, argument_lang)

if __name__ == "__main__":
    main()