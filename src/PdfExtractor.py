import sys
from pathlib import Path
from typing import List, Optional

import pdfplumber
import pytesseract
from pypdf import PdfReader
from pdf2image import convert_from_path


class PdfExtractor:
    @staticmethod
    def _parse_page_range(spec: str, total: int) -> List[int]:
        """Turn '1-5' or '3' into a list of zero-based page indexes."""
        if not spec:
            return list(range(total))
        
        try:
            if "-" in spec:
                start_str, end_str = spec.split("-", 1)
                start = int(start_str) if start_str else 1
                end = int(end_str) if end_str else total
            else:
                start = end = int(spec)
            
            start = max(start, 1)
            end = min(end, total)
            return list(range(start - 1, end))
        except ValueError:
            # Fallback to all pages if spec is malformed
            print(f"Warning: Invalid page range '{spec}', processing all pages.", file=sys.stderr)
            return list(range(total))

    @staticmethod
    def _extract_with_pdfplumber(pdf_path, pages_spec=None):
        chunks = []
        with pdfplumber.open(pdf_path) as pdf:
            for i in PdfExtractor._parse_page_range(pages_spec, len(pdf.pages)):
                text = pdf.pages[i].extract_text() or ""
                chunks.append(f"--- Page {i + 1} ---\n{text}")
        return "\n\n".join(chunks)

    @staticmethod
    def _extract_with_pypdf(pdf_path, pages_spec=None):
        reader = PdfReader(pdf_path)
        chunks = []
        for i in PdfExtractor._parse_page_range(pages_spec, len(reader.pages)):
            text = reader.pages[i].extract_text() or ""
            chunks.append(f"--- Page {i + 1} ---\n{text}")
        return "\n\n".join(chunks)

    @staticmethod
    def _extract_with_ocr(pdf_path, pages_spec=None, lang="eng"):
        images = convert_from_path(pdf_path, dpi=300)
        chunks = []
        for i in PdfExtractor._parse_page_range(pages_spec, len(images)):
            text = pytesseract.image_to_string(images[i], lang=lang)
            chunks.append(f"--- Page {i + 1} ---\n{text}")
        return "\n\n".join(chunks)

    @staticmethod
    def _has_real_text(text: str) -> bool:
        """True if extraction produced more than just page markers."""
        body = "\n".join(
            line for line in text.splitlines() if not line.startswith("--- Page ")
        )
        return len(body.strip()) > 20

    @staticmethod
    def _unwrap_lines(text: str) -> str:
        """Replace line breaks with a space when the next line does not
        start with an uppercase letter. Blank lines (paragraph breaks) are preserved."""
        result = []

        for line in text.splitlines():
            line = line.strip()

            # First line, blank lines, or a line following a blank line: keep as-is
            if not result or not line or not result[-1]:
                result.append(line)
            # Next line starts with uppercase: keep the line break
            elif line and line[0].isupper():
                result.append(line)
            # Otherwise: continuation of the previous line, join with a space
            else:
                if result:  # Safety check for empty list
                    result[-1] += " " + line

        return "\n".join(result)


    def convert(self, pdf_path, out_path: Path, use_ocr=False, pages_spec=None, lang="eng"):
        """Main entry point to extract and save PDF text."""
        
        if use_ocr:
            text = PdfExtractor._extract_with_ocr(pdf_path, pages_spec, lang)
        else:
            try:
                text = PdfExtractor._extract_with_pdfplumber(pdf_path, pages_spec)
            except Exception as e:
                print(f"  pdfplumber failed ({e}); trying pypdf...", file=sys.stderr)
                text = PdfExtractor._extract_with_pypdf(pdf_path, pages_spec)

            if not self._has_real_text(text):
                print(
                    "  Warning: little or no text found. This may be a scanned PDF; "
                    "try again with --ocr.",
                    file=sys.stderr,
                )

        text = PdfExtractor._unwrap_lines(text)

        out_path.write_text(text, encoding="utf-8")
        print(f"Saved: {out_path}")