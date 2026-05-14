from pathlib import Path
import pytest
from polaris.utils.pdf_extractor import extract_text


@pytest.mark.asyncio
async def test_extract_text_from_simple_pdf(tmp_path: Path) -> None:
    from reportlab.pdfgen import canvas
    pdf = tmp_path / "tiny.pdf"
    c = canvas.Canvas(str(pdf))
    c.drawString(72, 720, "SOC 2 CC6.1 Logical Access Controls")
    c.drawString(72, 700, "The entity restricts access to information assets.")
    c.showPage()
    c.save()

    # Tiny fixture intentionally below the 200-char production min. Opt out via min_chars=0.
    text = await extract_text(pdf, min_chars=0)
    assert "SOC 2 CC6.1" in text
    assert "restricts access" in text
