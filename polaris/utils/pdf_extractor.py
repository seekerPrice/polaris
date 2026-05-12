from __future__ import annotations

import asyncio
from pathlib import Path

from pypdf import PdfReader


def _read_pages(pdf_path: Path) -> list[str]:
    reader = PdfReader(str(pdf_path))
    return [p.extract_text() or "" for p in reader.pages]


def _strip_recurring_lines(pages: list[str]) -> list[str]:
    """Remove lines that appear on >=70% of pages (probably headers/footers)."""
    if not pages:
        return pages
    line_pages: dict[str, set[int]] = {}
    for i, page in enumerate(pages):
        for line in {ln.strip() for ln in page.splitlines() if ln.strip()}:
            line_pages.setdefault(line, set()).add(i)
    threshold = max(2, int(0.7 * len(pages)))
    recurring = {ln for ln, idxs in line_pages.items() if len(idxs) >= threshold}
    cleaned = []
    for page in pages:
        kept = [ln for ln in page.splitlines() if ln.strip() not in recurring]
        cleaned.append("\n".join(kept))
    return cleaned


async def extract_text(pdf_path: Path) -> str:
    pages = await asyncio.to_thread(_read_pages, pdf_path)
    pages = _strip_recurring_lines(pages)
    return "\n\n".join(pages).strip()
