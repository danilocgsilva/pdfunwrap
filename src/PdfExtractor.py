import sys
from pathlib import Path
import pdfplumber
import pytesseract
from pypdf import PdfReader
from pdf2image import convert_from_path

class PdfExtractor:
    def parse_page_range(self, spec, total):
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


    def extract_with_pdfplumber(self, pdf_path, pages_spec=None):
        chunks = []
        with pdfplumber.open(pdf_path) as pdf:
            for i in self.parse_page_range(pages_spec, len(pdf.pages)):
                text = pdf.pages[i].extract_text() or ""
                chunks.append(f"--- Page {i + 1} ---\n{text}")
        return "\n\n".join(chunks)


    def extract_with_pypdf(self, pdf_path, pages_spec=None):
        reader = PdfReader(pdf_path)
        chunks = []
        for i in self.parse_page_range(pages_spec, len(reader.pages)):
            text = reader.pages[i].extract_text() or ""
            chunks.append(f"--- Page {i + 1} ---\n{text}")
        return "\n\n".join(chunks)


    def extract_with_ocr(self, pdf_path, pages_spec=None, lang="eng"):
        images = convert_from_path(pdf_path, dpi=300)
        chunks = []
        for i in self.parse_page_range(pages_spec, len(images)):
            text = pytesseract.image_to_string(images[i], lang=lang)
            chunks.append(f"--- Page {i + 1} ---\n{text}")
        return "\n\n".join(chunks)


    def has_real_text(self, text):
        """True if extraction produced more than just page markers."""
        body = "\n".join(
            line for line in text.splitlines() if not line.startswith("--- Page ")
        )
        return len(body.strip()) > 20

    def unwrap_lines(self, text: str) -> str:
        """Replace line breaks with a space when the next line does not
        start with an uppercase letter. Blank lines (paragraph breaks) are preserved."""
        result = []

        for line in text.splitlines():
            line = line.strip()

            # First line, blank lines, or a line following a blank line: keep as-is
            if not result or not line or not result[-1]:
                result.append(line)
            # Next line starts with uppercase: keep the line break
            elif line[0].isupper():
                result.append(line)
            # Otherwise: continuation of the previous line, join with a space
            else:
                result[-1] += " " + line

        return "\n".join(result)


    def convert(self, pdf_path, out_path, use_ocr=False, pages_spec=None, lang="eng"):
        if use_ocr:
            text = self.extract_with_ocr(pdf_path, pages_spec, lang)
        else:
            try:
                text = self.extract_with_pdfplumber(pdf_path, pages_spec)
            except Exception as e:
                print(f"  pdfplumber failed ({e}); trying pypdf...", file=sys.stderr)
                text = self.extract_with_pypdf(pdf_path, pages_spec)

            if not self.has_real_text(text):
                print(
                    "  Warning: little or no text found. This may be a scanned PDF; "
                    "try again with --ocr.",
                    file=sys.stderr,
                )

        text = self.unwrap_lines(text)

        out_path.write_text(text, encoding="utf-8")
        print(f"Saved: {out_path}")
