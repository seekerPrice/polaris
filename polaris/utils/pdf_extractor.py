from __future__ import annotations

import asyncio
from pathlib import Path

from pypdf import PdfReader


# H8 fix (deep-check 2026-05-13): bound the work we do on untrusted PDFs.
# Without these limits a 10k-page or zip-bomb PDF OOMs the demo machine.
MAX_PAGES = 500
MAX_BYTES = 50 * 1024 * 1024  # 50 MB


class PDFExtractError(RuntimeError):
    """Raised on encrypted, oversized, malformed, or empty-text PDFs.
    The API layer maps this to a 4xx response with a clear message instead of a 500."""


class PDFNoTextError(PDFExtractError):
    """Raised when a PDF parses but yields no extractable text (scanned / image-only).
    Surfaced so the dashboard can prompt the user for a text-layer PDF or run OCR."""


def _read_pages(pdf_path: Path) -> list[str]:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    if not pdf_path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")
    size = pdf_path.stat().st_size
    if size > MAX_BYTES:
        raise PDFExtractError(f"PDF too large: {size} bytes (max {MAX_BYTES})")
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as e:
        raise PDFExtractError(f"malformed PDF: {e}") from None
    if reader.is_encrypted:
        raise PDFExtractError("encrypted PDFs are not supported")
    pages_out: list[str] = []
    for i, p in enumerate(reader.pages):
        if i >= MAX_PAGES:
            raise PDFExtractError(f"PDF has more than {MAX_PAGES} pages; refusing to process")
        try:
            pages_out.append(p.extract_text() or "")
        except Exception:
            # One malformed page must not kill the whole doc.
            pages_out.append("")
    return pages_out


def _strip_recurring_lines(pages: list[str]) -> list[str]:
    """Remove lines that appear on >=70% of pages (probably headers/footers).

    L9 fix (deep-check 2026-05-13): skip stripping entirely for short docs (<4 pages)
    so a legitimate body line that happens to repeat on 2 of 3 pages isn't deleted.
    """
    if not pages or len(pages) < 4:
        return pages
    line_pages: dict[str, set[int]] = {}
    for i, page in enumerate(pages):
        for line in {ln.strip() for ln in page.splitlines() if ln.strip()}:
            line_pages.setdefault(line, set()).add(i)
    import math
    threshold = max(2, math.ceil(0.7 * len(pages)))
    recurring = {ln for ln, idxs in line_pages.items() if len(idxs) >= threshold}
    cleaned: list[str] = []
    for page in pages:
        kept: list[str] = []
        for ln in page.splitlines():
            stripped = ln.strip()
            if stripped and stripped not in recurring:
                kept.append(ln)
        cleaned.append("\n".join(kept))
    return cleaned


async def extract_text(pdf_path: Path, *, min_chars: int = 200) -> str:
    pages = await asyncio.to_thread(_read_pages, pdf_path)
    pages = _strip_recurring_lines(pages)
    text = "\n\n".join(pages).strip()
    # M21 fix (deep-check 2026-05-13): if the PDF has no text layer (scanned doc),
    # raise loudly instead of feeding Gemini an empty prompt that yields a vacuous
    # policy that nevertheless validates green. `min_chars` is configurable so
    # unit-test fixtures (tiny PDFs) can opt out.
    if len(text) < min_chars:
        raise PDFNoTextError(
            f"PDF yielded only {len(text)} characters of text — likely a scanned/image-only PDF. "
            "Please upload a PDF with an extractable text layer, or run OCR upstream."
        )
    return text
