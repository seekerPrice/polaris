#!/usr/bin/env python3
"""Polaris pitch deck builder.

Generates docs/PITCH_DECK.pptx — 15 core + 3 appendix = 18 slides — styled
with the Polaris brand palette (dark navy + cyan glow, Space Grotesk +
JetBrains Mono) matching the Zacht "VC Pitch Deck" template layout
structure.

Content + citations sourced from docs/PITCH_DECK.md (the canonical brief).
Two parallel research agents verified every numeric claim against public
sources on 2026-05-18.

Usage:
    uv run python scripts/build_pitch_deck.py
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
DOCS_IMG = ROOT / "docs" / "img"
OUT = ROOT / "docs" / "PITCH_DECK.pptx"

# Brand palette — from dashboard/app/globals.css
NAVY = RGBColor(0x0B, 0x0D, 0x14)
PANEL = RGBColor(0x13, 0x16, 0x1F)
PANEL_2 = RGBColor(0x1B, 0x20, 0x2A)
PANEL_3 = RGBColor(0x25, 0x2B, 0x38)
CYAN = RGBColor(0x5D, 0xE3, 0xF5)
CYAN_DIM = RGBColor(0x1A, 0xA8, 0xC7)
CYAN_GLOW = RGBColor(0x7A, 0xF0, 0xFF)
ROSE = RGBColor(0xF2, 0x5C, 0x5C)
EMERALD = RGBColor(0x3D, 0xD9, 0xA0)
AMBER = RGBColor(0xF5, 0xC2, 0x5E)
VIOLET = RGBColor(0xA0, 0x77, 0xFF)
WHITE = RGBColor(0xF4, 0xF5, 0xF8)
TEXT_1 = RGBColor(0xB8, 0xBC, 0xC9)
TEXT_2 = RGBColor(0x7E, 0x84, 0x99)
TEXT_3 = RGBColor(0x44, 0x4B, 0x5C)

FONT_SANS = "Space Grotesk"
FONT_MONO = "JetBrains Mono"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


# --- helpers ------------------------------------------------------------

def set_bg(slide, color: RGBColor) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_text(
    slide, text, left, top, width, height, *,
    font=FONT_SANS, size=14, color=WHITE, bold=False,
    align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.15,
):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    lines = text.split("\n") if isinstance(text, str) else [str(text)]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        run = p.add_run()
        run.text = line
        run.font.name = font
        run.font.size = Pt(size)
        run.font.color.rgb = color
        run.font.bold = bold
    return tb


def add_rect(slide, left, top, width, height, fill, *,
             line=None, line_width=Pt(0.75)):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = line_width
    return shape


def add_oval(slide, left, top, width, height, fill, *,
             line=None, line_width=Pt(0.75)):
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = line_width
    return shape


def add_tag(slide, text, left, top, *, color=CYAN, size=11):
    return add_text(
        slide, text.upper(), left, top, Inches(8), Inches(0.35),
        font=FONT_MONO, size=size, color=color, bold=True,
    )


def add_headline(slide, text, left, top, width, height, *,
                 color=WHITE, size=44, align=PP_ALIGN.LEFT):
    return add_text(
        slide, text, left, top, width, height,
        font=FONT_SANS, size=size, color=color, bold=True,
        line_spacing=1.05, align=align,
    )


def add_body(slide, text, left, top, width, height, *,
             color=TEXT_1, size=14, align=PP_ALIGN.LEFT):
    return add_text(
        slide, text, left, top, width, height,
        font=FONT_SANS, size=size, color=color,
        line_spacing=1.35, align=align,
    )


def add_bullets(slide, bullets, left, top, width, height, *,
                color=TEXT_1, size=13, marker_color=CYAN):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    for i, bullet in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.35
        p.space_after = Pt(8)
        m = p.add_run()
        m.text = "▸  "
        m.font.name = FONT_MONO
        m.font.size = Pt(size)
        m.font.color.rgb = marker_color
        m.font.bold = True
        t = p.add_run()
        t.text = bullet
        t.font.name = FONT_SANS
        t.font.size = Pt(size)
        t.font.color.rgb = color
    return tb


def add_footer(slide, citations):
    text = "  ·  ".join(citations) if isinstance(citations, list) else citations
    return add_text(
        slide, text, Inches(0.5), Inches(7.1), Inches(12.5), Inches(0.3),
        font=FONT_MONO, size=8, color=TEXT_2,
    )


def add_top_corners(
    slide, left_tag="POLARIS", right_tag="VEEA TRUST TRACK · TECHEX 2026"
) -> None:
    add_text(
        slide, left_tag, Inches(0.5), Inches(0.3), Inches(3), Inches(0.3),
        font=FONT_MONO, size=9, color=TEXT_2,
    )
    add_text(
        slide, right_tag, Inches(9.8), Inches(0.3), Inches(3.2), Inches(0.3),
        font=FONT_MONO, size=9, color=TEXT_2, align=PP_ALIGN.RIGHT,
    )


def style_table_cell(cell, *, fill, text_color=WHITE, bold=False, size=12,
                     align=PP_ALIGN.LEFT, font=FONT_SANS):
    cell.fill.solid()
    cell.fill.fore_color.rgb = fill
    cell.margin_left = Inches(0.12)
    cell.margin_right = Inches(0.12)
    cell.margin_top = Inches(0.06)
    cell.margin_bottom = Inches(0.06)
    tf = cell.text_frame
    tf.word_wrap = True
    for p in tf.paragraphs:
        p.alignment = align
        for r in p.runs:
            r.font.name = font
            r.font.size = Pt(size)
            r.font.color.rgb = text_color
            r.font.bold = bold


# --- slide builders -----------------------------------------------------

def slide_1_cover(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    add_top_corners(s)
    # Cyan accent strip left
    add_rect(s, Inches(0), Inches(1.8), Inches(0.08), Inches(4.0), CYAN)
    # Title
    add_headline(s, "POLARIS", Inches(0.6), Inches(1.8),
                 Inches(8), Inches(1.8), size=120, color=WHITE)
    add_text(s, "PITCH DECK", Inches(0.65), Inches(3.6),
             Inches(8), Inches(0.7),
             font=FONT_SANS, size=30, color=CYAN, bold=True)
    add_text(s, "From SOC 2 PDF to live AI guardrail in 60 seconds.",
             Inches(0.65), Inches(4.5), Inches(7.5), Inches(0.5),
             font=FONT_SANS, size=18, color=TEXT_1)
    add_text(s, "MAY 2026  ·  AI & BIG DATA EXPO  ·  SAN JOSE",
             Inches(0.65), Inches(5.15), Inches(8), Inches(0.4),
             font=FONT_MONO, size=11, color=TEXT_2)
    # Hero image right
    img = DOCS_IMG / "demo_thumbnail.png"
    if img.exists():
        try:
            s.shapes.add_picture(str(img), Inches(7.6), Inches(1.6),
                                 width=Inches(5.5))
        except Exception:
            pass
    add_text(s, "Live: polaris--lucaslootan.replit.app",
             Inches(0.65), Inches(6.7), Inches(8), Inches(0.35),
             font=FONT_MONO, size=11, color=CYAN_DIM)


def slide_2_mission(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    # Outer panel with cyan border
    add_rect(s, Inches(0.5), Inches(0.5), Inches(12.33), Inches(6.5), PANEL,
             line=CYAN_DIM, line_width=Pt(0.5))
    # Cyan glow accent strip top
    add_rect(s, Inches(0.5), Inches(0.5), Inches(12.33), Inches(0.08), CYAN)
    add_text(s, "MISSION", Inches(1), Inches(1.5), Inches(11.3), Inches(0.4),
             font=FONT_MONO, size=14, color=CYAN, bold=True, align=PP_ALIGN.CENTER)
    add_headline(s, "Compile compliance documents\ninto running AI firewalls.",
                 Inches(1), Inches(2.3), Inches(11.3), Inches(2.6),
                 size=54, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, "At AI speed.",
             Inches(1), Inches(4.9), Inches(11.3), Inches(0.8),
             font=FONT_SANS, size=36, color=CYAN, bold=True, align=PP_ALIGN.CENTER)
    add_text(
        s,
        "Polaris is the only end-to-end loop from compliance PDF → deployed runtime policy → continuous adversarial verification.",
        Inches(1.5), Inches(5.9), Inches(10.3), Inches(0.8),
        font=FONT_SANS, size=15, color=TEXT_1, align=PP_ALIGN.CENTER,
    )


def slide_3_overview(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    add_top_corners(s)
    add_tag(s, "OVERVIEW", Inches(0.6), Inches(0.95))
    add_headline(s, "A 4-agent closed loop that\ncompiles compliance into\nruntime enforcement.",
                 Inches(0.6), Inches(1.5), Inches(7), Inches(3.2),
                 size=36, color=WHITE)

    # Highlights panel right top
    add_rect(s, Inches(7.8), Inches(1.4), Inches(5.0), Inches(2.5), PANEL,
             line=PANEL_3)
    add_tag(s, "HIGHLIGHTS", Inches(8.0), Inches(1.55), color=CYAN, size=10)
    add_bullets(s, [
        "Compiles SOC 2 / HIPAA / EU AI Act / PCI-DSS PDFs into deployable Lobster Trap YAML in ~11s (60s SLA).",
        "Red Team agent continuously stress-tests deployed policy; auto-patches on gap.",
        "Audit-defensible chain of custody mapped to SOC 2 CC8.1.",
    ], Inches(8.0), Inches(1.95), Inches(4.7), Inches(2.0), size=10.5)

    # Industry & market panel
    add_rect(s, Inches(7.8), Inches(4.05), Inches(5.0), Inches(1.5), PANEL,
             line=PANEL_3)
    add_tag(s, "INDUSTRY & MARKET", Inches(8.0), Inches(4.2), color=CYAN, size=10)
    add_text(s, "Enterprise AI Trust, Risk & Security Management (TRiSM)",
             Inches(8.0), Inches(4.55), Inches(4.7), Inches(0.4),
             font=FONT_SANS, size=11, color=TEXT_1)
    add_text(s, "$2.34B → $7.44B",
             Inches(8.0), Inches(4.85), Inches(4.7), Inches(0.5),
             font=FONT_SANS, size=24, color=CYAN, bold=True)
    add_text(s, "2024 → 2030  ·  21.6% CAGR",
             Inches(8.0), Inches(5.30), Inches(4.7), Inches(0.3),
             font=FONT_MONO, size=10, color=TEXT_2)

    # Team
    add_rect(s, Inches(0.6), Inches(4.9), Inches(7), Inches(2.0), PANEL,
             line=PANEL_3)
    add_tag(s, "TEAM", Inches(0.8), Inches(5.05), color=CYAN, size=10)
    add_text(s, "Lucas Loo Tan Yu Heng — Founder & Lead AI Engineer",
             Inches(0.8), Inches(5.4), Inches(6.7), Inches(0.4),
             font=FONT_SANS, size=14, color=WHITE, bold=True)
    add_body(s, "Day job: Hoppi (M) Sdn Bhd — Hotseller V5 (25+ orchestrated Gemini agents in production).",
             Inches(0.8), Inches(5.8), Inches(6.7), Inches(1.0),
             color=TEXT_1, size=11)

    # Hero-metric bar chart panel (manual rectangles)
    add_rect(s, Inches(7.8), Inches(5.7), Inches(5.0), Inches(1.2), PANEL,
             line=PANEL_3)
    add_tag(s, "HERO METRIC", Inches(8.0), Inches(5.85), color=CYAN, size=10)
    add_text(s, "60s SLA", Inches(8.0), Inches(6.15), Inches(1.5), Inches(0.25),
             font=FONT_MONO, size=9, color=TEXT_2)
    add_rect(s, Inches(9.2), Inches(6.18), Inches(0.3), Inches(0.18), CYAN_DIM)
    add_text(s, "11s actual", Inches(9.6), Inches(6.13), Inches(2), Inches(0.25),
             font=FONT_MONO, size=10, color=CYAN, bold=True)
    add_text(s, "vs status quo: 3 weeks of legal review", Inches(8.0), Inches(6.5),
             Inches(4.7), Inches(0.3), font=FONT_MONO, size=9, color=ROSE)
    add_rect(s, Inches(9.2), Inches(6.53), Inches(3), Inches(0.18), ROSE)

    add_footer(s, [
        "Grand View Research · grandviewresearch.com/press-release/global-ai-trust-risk-security-management-market",
    ])


def slide_4_problem_why_now(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    add_top_corners(s)

    # Left panel (Problem)
    add_rect(s, Inches(0.5), Inches(1.0), Inches(6.1), Inches(5.9), PANEL,
             line=PANEL_3)
    add_tag(s, "THE PROBLEM", Inches(0.8), Inches(1.25), color=ROSE, size=11)
    add_headline(s,
                 "Compliance lives in PDFs.\nAI agents run in production.\nThe wire between is hand-written.",
                 Inches(0.8), Inches(1.7), Inches(5.6), Inches(2.5),
                 size=20, color=WHITE)
    add_bullets(s, [
        "23% of enterprises scaling AI agents; 39% experimenting. (McKinsey State of AI 2025)",
        "233 AI security incidents in 2024 → 362 in 2025, +55% YoY. (Stanford HAI AI Index)",
        "Median compliance / business-formation counsel: $378 / hr. (Clio Legal Trends 2026)",
    ], Inches(0.8), Inches(4.3), Inches(5.6), Inches(2.5), size=12,
       marker_color=ROSE)

    # Right panel (Why Now) — cyan-emphasis
    add_rect(s, Inches(6.8), Inches(1.0), Inches(6.0), Inches(5.9), PANEL_2,
             line=CYAN_DIM)
    add_rect(s, Inches(6.8), Inches(1.0), Inches(6.0), Inches(0.06), CYAN)
    add_tag(s, "WHY NOW", Inches(7.0), Inches(1.25), color=CYAN, size=11)
    add_headline(s,
                 "Regulators are catching up.\nEvery enterprise running an\nAI agent is non-conformant\nby default.",
                 Inches(7.0), Inches(1.7), Inches(5.6), Inches(2.5),
                 size=20, color=WHITE)
    add_bullets(s, [
        "EU AI Act high-risk obligations: 2 Aug 2026 statutory. Digital Omnibus (7 May 2026) defers Annex III to 2 Dec 2027 — not yet enacted.",
        "Colorado AI Act (SB24-205): postponed to 30 Jun 2026; enforcement currently stayed pending federal litigation.",
        "NIST AI RMF 1.0 — voluntary framework, Jan 2023.",
        "OWASP LLM Top 10 v1.1 — prompt injection ranked #1.",
    ], Inches(7.0), Inches(4.1), Inches(5.6), Inches(2.7), size=10.5,
       marker_color=CYAN)

    add_footer(s, [
        "mckinsey.com/state-of-ai",
        "hai.stanford.edu/ai-index",
        "clio.com/resources/legal-trends",
        "artificialintelligenceact.eu",
        "leg.colorado.gov/bills/sb24-205",
        "nist.gov · owasp.org",
    ])


def slide_5_solution(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    add_top_corners(s)
    add_tag(s, "SOLUTION", Inches(0.6), Inches(0.95))
    add_headline(s,
                 "Polaris compiles compliance documents\ninto runtime AI guardrails — and verifies them.",
                 Inches(0.6), Inches(1.45), Inches(12.5), Inches(1.5),
                 size=26, color=WHITE)
    add_text(s, "Four Gemini agents. One Veea Lobster Trap firewall. One closed loop.",
             Inches(0.6), Inches(2.95), Inches(12.5), Inches(0.4),
             font=FONT_SANS, size=14, color=CYAN)

    # 3 feature cards
    cards = [
        ("READER AGENT", "gemini-3.1-flash-lite",
         "Extracts compliance requirements from PDF text.",
         "~3s per doc", CYAN),
        ("SYNTHESIZER", "gemini-3.1-flash-lite + thinking_level=low",
         "Schema-first synthesis: passes LobsterTrapPolicy Pydantic class as response_schema.",
         "~4.6s median", EMERALD),
        ("RED TEAM", "gemini-3.1-pro-preview",
         "Generates adversarial probes; triggers Synthesizer regeneration on gap.",
         "~10s / round", AMBER),
    ]
    card_w, card_h = Inches(4.0), Inches(3.5)
    spacing = Inches(0.2)
    total_w = card_w * 3 + spacing * 2
    start_x = (SLIDE_W - total_w) / 2

    for i, (tag, model, body, latency, accent) in enumerate(cards):
        x = start_x + (card_w + spacing) * i
        y = Inches(3.7)
        add_rect(s, x, y, card_w, card_h, PANEL, line=PANEL_3)
        # Accent strip top
        add_rect(s, x, y, card_w, Inches(0.06), accent)
        add_text(s, tag, x + Inches(0.3), y + Inches(0.3),
                 card_w - Inches(0.6), Inches(0.4),
                 font=FONT_MONO, size=12, color=accent, bold=True)
        add_text(s, model, x + Inches(0.3), y + Inches(0.8),
                 card_w - Inches(0.6), Inches(0.4),
                 font=FONT_MONO, size=10, color=TEXT_2)
        add_text(s, body, x + Inches(0.3), y + Inches(1.4),
                 card_w - Inches(0.6), Inches(1.5),
                 font=FONT_SANS, size=12.5, color=TEXT_1)
        add_text(s, latency, x + Inches(0.3), y + card_h - Inches(0.6),
                 card_w - Inches(0.6), Inches(0.4),
                 font=FONT_MONO, size=14, color=accent, bold=True)

    add_footer(s, [
        "ai.google.dev/gemini-api/docs/pricing",
        "github.com/veeainc/lobstertrap",
    ])


def slide_6_product(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    add_top_corners(s)
    add_tag(s, "PRODUCT · LIVE DASHBOARD", Inches(0.6), Inches(0.95))
    add_headline(s, "Drag-drop.\n11 seconds.\nLive firewall.",
                 Inches(0.6), Inches(1.5), Inches(6.5), Inches(3.0),
                 size=48, color=WHITE)
    add_body(s,
             "Phase-9 schema-first Synthesizer cuts latency 5× while tying with the larger Pro model on intrinsic accuracy (6.0/11 LT corpus). Same architectural pattern shipped at scale in Hoppi's Hotseller V5 (25+ orchestrated agents).",
             Inches(0.6), Inches(4.6), Inches(6.3), Inches(2.0),
             color=TEXT_1, size=14)

    img = DOCS_IMG / "demo_thumbnail.png"
    if img.exists():
        try:
            add_rect(s, Inches(7.05), Inches(1.45), Inches(5.85), Inches(4.3),
                     PANEL, line=CYAN_DIM, line_width=Pt(0.75))
            s.shapes.add_picture(str(img), Inches(7.15), Inches(1.55),
                                 width=Inches(5.65))
        except Exception:
            pass

    add_footer(s, [
        "Source: docs/MODEL_BAKEOFF.md (48-run model bake-off, Phase 9, 2026-05-13)",
        "github.com/seekerPrice/polaris",
    ])


def slide_7_closed_loop(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    # Full-bleed cyan-bordered emphasis panel
    add_rect(s, Inches(0.5), Inches(0.5), Inches(12.33), Inches(6.5), PANEL,
             line=CYAN_DIM, line_width=Pt(0.5))
    add_rect(s, Inches(0.5), Inches(0.5), Inches(12.33), Inches(0.08), CYAN)
    add_tag(s, "THE CLOSED LOOP", Inches(1.0), Inches(1.0),
            color=CYAN, size=12)
    add_headline(s, "This loop closes itself.",
                 Inches(1.0), Inches(1.5), Inches(11), Inches(0.9),
                 size=36, color=WHITE)

    # 5-step horizontal flow
    steps = [
        ("1", "Reader", "~3s", CYAN),
        ("2", "Synthesizer", "4.6s · schema-first", EMERALD),
        ("3", "Validation gate", "11/11 LT corpus", VIOLET),
        ("4", "Lobster Trap DPI", "_lobstertrap intent", AMBER),
        ("5", "Red Team", "~10s · auto-patch", ROSE),
    ]
    box_w, box_h = Inches(2.2), Inches(2.4)
    arrow_w = Inches(0.18)
    total_w = box_w * 5 + arrow_w * 4
    start_x = (SLIDE_W - total_w) / 2

    for i, (n, label, sub, accent) in enumerate(steps):
        x = start_x + (box_w + arrow_w) * i
        y = Inches(3.0)
        add_rect(s, x, y, box_w, box_h, PANEL_2, line=accent, line_width=Pt(1))
        add_text(s, n, x + Inches(0.2), y + Inches(0.25),
                 Inches(1.5), Inches(0.6),
                 font=FONT_MONO, size=36, color=accent, bold=True)
        add_text(s, label, x + Inches(0.2), y + Inches(0.95),
                 box_w - Inches(0.4), Inches(0.5),
                 font=FONT_SANS, size=14, color=WHITE, bold=True)
        add_text(s, sub, x + Inches(0.2), y + Inches(1.5),
                 box_w - Inches(0.4), Inches(0.5),
                 font=FONT_MONO, size=10, color=TEXT_1)
        if i < 4:
            ax = x + box_w
            add_text(s, "→", ax, y + Inches(0.95),
                     arrow_w, Inches(0.5),
                     font=FONT_MONO, size=18, color=CYAN_DIM, bold=True,
                     align=PP_ALIGN.CENTER)

    # Loop-back arrow underneath
    add_text(s, "↻  Synthesizer regenerates on gap → hot-reload → same probe now blocked",
             Inches(1), Inches(5.7), Inches(11.3), Inches(0.5),
             font=FONT_MONO, size=13, color=CYAN, bold=True, align=PP_ALIGN.CENTER)
    add_text(s, "Lobster Trap _lobstertrap declared-vs-detected mismatches feed the Red Team — humans on the audit trail.",
             Inches(1), Inches(6.2), Inches(11.3), Inches(0.4),
             font=FONT_SANS, size=11, color=TEXT_2, align=PP_ALIGN.CENTER)

    add_footer(s, ["Source: github.com/veeainc/lobstertrap"])


def slide_8_market(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    add_top_corners(s)
    add_tag(s, "MARKET OPPORTUNITY", Inches(0.6), Inches(0.95))
    add_headline(s, "A $7.44B market,\nexpanding 21.6% per year.",
                 Inches(0.6), Inches(1.5), Inches(7), Inches(1.8),
                 size=30, color=WHITE)

    bullets = [
        ("TAM", "$7.44B by 2030",
         "Global AI TRiSM. $2.34B (2024) → $7.44B at 21.6% CAGR. (Grand View Research, 2025)"),
        ("SAM", "Billion-dollar (Gartner Feb 2026)",
         "AI governance platforms. Precedence: $309M → $3.59B by 2033 at 36% CAGR."),
        ("TARGET", "$740M serviceable",
         "US SOC 2 / HIPAA enterprises with AI agents in production (subset of 822k HIPAA-covered + 1M associates × 23% McKinsey AI-in-prod rate)."),
        ("ENTRY", "$74M ARR potential",
         "1% capture × $500–$2,499 / mo / policy ARPU."),
    ]
    y = Inches(3.2)
    for tag, big, body in bullets:
        add_text(s, tag, Inches(0.6), y,
                 Inches(1.0), Inches(0.35),
                 font=FONT_MONO, size=10, color=CYAN, bold=True)
        add_text(s, big, Inches(1.65), y - Inches(0.04),
                 Inches(5.5), Inches(0.45),
                 font=FONT_SANS, size=18, color=WHITE, bold=True)
        add_text(s, body, Inches(0.6), y + Inches(0.42),
                 Inches(6.8), Inches(0.45),
                 font=FONT_SANS, size=11, color=TEXT_1)
        y += Inches(0.95)

    # Concentric circles right
    cx = Inches(10.0)
    cy = Inches(4.5)
    sizes = [
        (5.5, PANEL, CYAN_DIM, "TAM\n$7.44B", 0.7),
        (4.0, PANEL_2, CYAN_DIM, "SAM\n$3.6B", 1.4),
        (2.5, CYAN_DIM, CYAN, "TARGET\n$740M", 2.0),
        (1.2, CYAN, NAVY, "$74M", 2.65),
    ]
    for d, fill, line, label, ty_inch in sizes:
        diam = Inches(d)
        add_oval(s, cx - diam / 2, cy - diam / 2, diam, diam, fill,
                 line=line, line_width=Pt(0.75))
        if "$74M" in label:
            text_color = NAVY
            font_size = 12
        else:
            text_color = WHITE
            font_size = 9
        add_text(s, label, cx - Inches(1.5), cy - Inches(d/2) + Inches(ty_inch),
                 Inches(3), Inches(0.6),
                 font=FONT_MONO, size=font_size, color=text_color, bold=True,
                 align=PP_ALIGN.CENTER, line_spacing=1.05)

    add_footer(s, [
        "grandviewresearch.com · gartner.com (Feb 2026 PR)",
        "precedenceresearch.com",
        "mckinsey.com/state-of-ai",
        "hhs.gov/hipaa",
    ])


def slide_9_competitive(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    add_top_corners(s)
    add_tag(s, "COMPETITIVE LANDSCAPE", Inches(0.6), Inches(0.95))
    add_headline(s, "Polaris is the only end-to-end\nPDF → Deploy → Verify → Patch loop.",
                 Inches(0.6), Inches(1.5), Inches(12), Inches(1.4),
                 size=26, color=WHITE)

    headers = ["Capability", "Polaris", "MS Purview\nAI Hub", "Lakera\nGuard",
               "F5 AI Guardrails\n(ex-CalypsoAI)", "Cisco AI Defense\n(ex-Robust Intelligence)"]
    rows = [
        ("Auto-synthesize policy from compliance PDF",
         "✓", "✗", "✗", "✗", "✗"),
        ("Runtime inline enforcement on LLM I/O",
         "✓", "✗*", "✓", "✓", "✓"),
        ("Closed-loop continuous Red Team",
         "✓", "✗", "✗", "✗", "✗"),
        ("Auto-generated compliance PDF",
         "✓", "partial", "✗", "✗", "partial"),
        ("Open-source DPI substrate",
         "✓ (Veea LT)", "✗", "✗", "✗", "✗"),
    ]
    n_rows = len(rows) + 1
    n_cols = len(headers)
    table_left = Inches(0.6)
    table_top = Inches(3.2)
    table_w = Inches(12.1)
    table_h = Inches(3.1)

    table_shape = s.shapes.add_table(n_rows, n_cols, table_left, table_top,
                                     table_w, table_h)
    table = table_shape.table

    # Column widths
    col_widths = [3.6, 1.6, 1.4, 1.4, 2.0, 2.1]
    for i, w in enumerate(col_widths):
        table.columns[i].width = Inches(w)

    # Header row
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        style_table_cell(cell, fill=PANEL_2, text_color=CYAN,
                         bold=True, size=10, align=PP_ALIGN.CENTER, font=FONT_MONO)

    for r_idx, row in enumerate(rows, start=1):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = val
            if c_idx == 0:
                style_table_cell(cell, fill=PANEL, text_color=WHITE,
                                 size=11, align=PP_ALIGN.LEFT)
            else:
                # Polaris column gets cyan accent
                is_polaris = (c_idx == 1)
                if val == "✓":
                    color = CYAN if is_polaris else EMERALD
                    style_table_cell(cell, fill=PANEL, text_color=color,
                                     bold=True, size=14, align=PP_ALIGN.CENTER,
                                     font=FONT_MONO)
                elif val.startswith("✗"):
                    style_table_cell(cell, fill=PANEL, text_color=ROSE,
                                     bold=True, size=14, align=PP_ALIGN.CENTER,
                                     font=FONT_MONO)
                elif val == "partial":
                    style_table_cell(cell, fill=PANEL, text_color=AMBER,
                                     bold=True, size=10, align=PP_ALIGN.CENTER,
                                     font=FONT_MONO)
                else:
                    style_table_cell(cell, fill=PANEL, text_color=CYAN,
                                     bold=True, size=10, align=PP_ALIGN.CENTER,
                                     font=FONT_MONO)

    add_text(s, "* Microsoft Purview AI Hub provides endpoint browser DLP + post-hoc audit only — not inline blocking on LLM outputs.",
             Inches(0.6), Inches(6.4), Inches(12.5), Inches(0.3),
             font=FONT_SANS, size=10, color=TEXT_2)
    add_text(s, "None of the four funded incumbents combine auto-synthesis + runtime enforcement + closed-loop verification.",
             Inches(0.6), Inches(6.7), Inches(12.5), Inches(0.3),
             font=FONT_SANS, size=11, color=CYAN, bold=True)

    add_footer(s, [
        "learn.microsoft.com/purview",
        "lakera.ai/lakera-guard",
        "f5.com/products/ai-guardrails",
        "cisco.com/products/security/ai-defense",
    ])


def slide_10_business_model(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    add_top_corners(s)
    add_tag(s, "BUSINESS MODEL", Inches(0.6), Inches(0.95))
    add_headline(s, "Per-policy subscription.\nSOC 2-defensible.\n>95% gross margin.",
                 Inches(0.6), Inches(1.5), Inches(6.5), Inches(3.5),
                 size=28, color=WHITE)
    add_body(s,
             "Tiered SaaS + per-inference overage. Self-hosted Lobster Trap option for compliance-strict tenants. Pricing is a draft model pending design-partner validation (Q3 2026 pilots).",
             Inches(0.6), Inches(5.2), Inches(6.3), Inches(1.6),
             color=TEXT_1, size=12)

    # Pricing table
    headers = ["", "Starter", "Pro"]
    rows = [
        ("Compliance packs", "1", "Unlimited"),
        ("AI agents protected", "1", "Unlimited"),
        ("Continuous Red Team", "weekly", "continuous"),
        ("Drift detection (v0.2)", "—", "✓"),
        ("Slack / Linear alerts", "—", "✓"),
        ("Compliance PDF auto-gen", "✓", "✓"),
        ("Self-hosted LT option", "—", "✓"),
        ("Audience", "SOC 2 design partners", "Multi-policy enterprises"),
        ("Price", "$499 / mo", "$2,499 / mo + $0.10/1k"),
    ]
    n_rows = len(rows) + 1
    n_cols = 3

    table_shape = s.shapes.add_table(n_rows, n_cols,
                                     Inches(7.3), Inches(1.4),
                                     Inches(5.5), Inches(5.2))
    table = table_shape.table
    table.columns[0].width = Inches(2.2)
    table.columns[1].width = Inches(1.5)
    table.columns[2].width = Inches(1.8)

    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        style_table_cell(cell, fill=PANEL_2, text_color=CYAN if i > 0 else TEXT_2,
                         bold=True, size=14, align=PP_ALIGN.CENTER, font=FONT_MONO)

    for r_idx, row in enumerate(rows, start=1):
        is_price = (row[0] == "Price")
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = val
            if c_idx == 0:
                style_table_cell(cell, fill=PANEL,
                                 text_color=WHITE if is_price else TEXT_1,
                                 bold=is_price, size=11)
            else:
                color = CYAN if is_price else (CYAN_DIM if val == "✓" else TEXT_1)
                if val == "—":
                    color = TEXT_3
                style_table_cell(cell, fill=PANEL,
                                 text_color=color,
                                 bold=is_price or val == "✓",
                                 size=12 if not is_price else 13,
                                 align=PP_ALIGN.CENTER, font=FONT_MONO)

    add_text(s,
             "Marginal cost / policy ≈ $0.005 in Gemini compute (gemini-3.1-flash-lite). Gross margin >95%.",
             Inches(0.6), Inches(6.7), Inches(6.5), Inches(0.4),
             font=FONT_MONO, size=10, color=CYAN_DIM)

    add_footer(s, ["ai.google.dev/gemini-api/docs/pricing"])


def slide_11_unit_economics(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    add_top_corners(s)
    add_tag(s, "UNIT ECONOMICS", Inches(0.6), Inches(0.95))
    add_headline(s, "Why the math works.",
                 Inches(0.6), Inches(1.5), Inches(12), Inches(0.9),
                 size=36, color=WHITE)

    tiles = [
        ("11 SECONDS", "END-TO-END  ·  60s SLA", CYAN),
        ("$0.005", "GEMINI COST / POLICY", EMERALD),
        ("3,000,000×", "COST COMPRESSION", AMBER),
        ("$15K–$45K", "COMPLIANCE COUNSEL REPLACED", VIOLET),
        ("11 / 11", "LOBSTER TRAP CORPUS PASS", CYAN_DIM),
        ("62 / 62", "UNIT TESTS PASS", EMERALD),
    ]
    cols = 3
    tile_w, tile_h = Inches(4.0), Inches(1.95)
    spacing_x = Inches(0.15)
    spacing_y = Inches(0.2)
    total_w = tile_w * cols + spacing_x * (cols - 1)
    start_x = (SLIDE_W - total_w) / 2
    start_y = Inches(2.6)

    for i, (big, cap, accent) in enumerate(tiles):
        r, c = divmod(i, cols)
        x = start_x + (tile_w + spacing_x) * c
        y = start_y + (tile_h + spacing_y) * r
        add_rect(s, x, y, tile_w, tile_h, PANEL, line=PANEL_3)
        add_rect(s, x, y, Inches(0.08), tile_h, accent)
        add_text(s, big, x + Inches(0.4), y + Inches(0.3),
                 tile_w - Inches(0.6), Inches(0.9),
                 font=FONT_SANS, size=32, color=WHITE, bold=True)
        add_text(s, cap, x + Inches(0.4), y + Inches(1.25),
                 tile_w - Inches(0.6), Inches(0.5),
                 font=FONT_MONO, size=10, color=accent, bold=True)

    add_text(s,
             "Counsel-cost floor: Drata SOC 2 framework (3-wk observation + 2-5wk audit) × Clio's $378/hr 2026 median compliance rate × FTE ≈ $45K per policy cycle.",
             Inches(0.6), Inches(6.8), Inches(12.1), Inches(0.4),
             font=FONT_SANS, size=10, color=TEXT_2, align=PP_ALIGN.CENTER)

    add_footer(s, [
        "drata.com/grc-central/soc-2",
        "clio.com/resources/legal-trends",
        "ai.google.dev/gemini-api/docs/pricing",
        "github.com/seekerPrice/polaris",
    ])


def slide_12_roadmap(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    add_top_corners(s)
    add_tag(s, "ROADMAP", Inches(0.6), Inches(0.95))
    add_headline(s, "Where we go after the hackathon.",
                 Inches(0.6), Inches(1.5), Inches(12), Inches(0.9),
                 size=28, color=WHITE)

    quarters = [
        ("Q3 2026", "next · pilots", [
            "Per-agent declared_intent verdicts (v0.2)",
            "SOC 2 design-partner pilot (3-5 enterprises)",
            "Drift detection v0.1",
        ], CYAN),
        ("Q4 2026", "GA", [
            "HIPAA + PCI-DSS pack hardening",
            "Pricing GA (Starter + Pro)",
            "Slack / Linear alerts",
        ], EMERALD),
        ("Q1 2027", "SEED · $2M", [
            "Multi-tenant SaaS architecture",
            "$2M Seed target",
        ], AMBER),
        ("Q2 2027", "scale", [
            "EU AI Act Annex III templates",
            "25 paying tenants",
        ], VIOLET),
        ("Q3 2027", "channel", [
            "Self-service Veea DevKit deploy",
            "100+ tenants",
        ], CYAN_DIM),
    ]
    col_w = Inches(2.4)
    gap = Inches(0.05)
    total_w = col_w * 5 + gap * 4
    start_x = (SLIDE_W - total_w) / 2
    col_y = Inches(2.7)
    col_h = Inches(3.8)

    for i, (q, sub, items, accent) in enumerate(quarters):
        x = start_x + (col_w + gap) * i
        add_rect(s, x, col_y, col_w, col_h, PANEL, line=PANEL_3)
        add_rect(s, x, col_y, col_w, Inches(0.06), accent)
        add_text(s, q, x + Inches(0.2), col_y + Inches(0.2),
                 col_w - Inches(0.4), Inches(0.5),
                 font=FONT_SANS, size=18, color=WHITE, bold=True)
        add_text(s, sub, x + Inches(0.2), col_y + Inches(0.75),
                 col_w - Inches(0.4), Inches(0.4),
                 font=FONT_MONO, size=10, color=accent, bold=True)
        add_bullets(s, items,
                    x + Inches(0.2), col_y + Inches(1.3),
                    col_w - Inches(0.4), col_h - Inches(1.5),
                    color=TEXT_1, size=10, marker_color=accent)

    # Fundraising bar under Q1 2027 column
    bar_x = start_x + (col_w + gap) * 2
    bar_y = col_y + col_h + Inches(0.15)
    add_rect(s, bar_x, bar_y, col_w, Inches(0.18), AMBER)
    add_text(s, "FUNDRAISING", bar_x, bar_y + Inches(0.22),
             col_w, Inches(0.3),
             font=FONT_MONO, size=10, color=AMBER, bold=True, align=PP_ALIGN.CENTER)


def slide_13_team(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    add_top_corners(s)
    add_tag(s, "TEAM", Inches(0.6), Inches(0.95))
    add_headline(s, "Sole engineer, with the\nproduction playbook already shipped.",
                 Inches(0.6), Inches(1.5), Inches(12), Inches(1.4),
                 size=26, color=WHITE)

    # Lucas card — full width
    add_rect(s, Inches(0.6), Inches(3.2), Inches(7.5), Inches(3.6), PANEL,
             line=CYAN_DIM)
    add_rect(s, Inches(0.6), Inches(3.2), Inches(0.08), Inches(3.6), CYAN)
    # Monogram avatar
    add_oval(s, Inches(0.9), Inches(3.5), Inches(1.5), Inches(1.5), CYAN_DIM,
             line=CYAN, line_width=Pt(1.5))
    add_text(s, "LT", Inches(0.9), Inches(3.78), Inches(1.5), Inches(1.0),
             font=FONT_MONO, size=42, color=NAVY, bold=True,
             align=PP_ALIGN.CENTER)
    add_text(s, "Lucas — Loo Tan Yu Heng",
             Inches(2.6), Inches(3.5), Inches(5.3), Inches(0.5),
             font=FONT_SANS, size=22, color=WHITE, bold=True)
    add_text(s, "FOUNDER & LEAD AI ENGINEER  ·  KUALA LUMPUR, MY",
             Inches(2.6), Inches(4.0), Inches(5.3), Inches(0.4),
             font=FONT_MONO, size=10, color=CYAN, bold=True)
    add_body(s,
             "Lead AI Engineer at Hoppi (M) Sdn Bhd on Hotseller V5 — 25+ orchestrated Gemini agents, multi-tier model routing, semantic cache invalidation, taxonomy classifier across 51 categories × 100K+ multilingual records. Authored 26-entry LLM Production Anti-Pattern Registry. Polaris's 4-agent loop is the same pattern, applied to compliance.",
             Inches(2.6), Inches(4.5), Inches(5.4), Inches(2.2),
             color=TEXT_1, size=11)

    # 3 open advisor seats
    advisors = [
        ("CISO ADVISOR", "OPEN"),
        ("COMPLIANCE COUNSEL", "OPEN"),
        ("VEEA PARTNERSHIPS", "OPEN"),
    ]
    card_w = Inches(1.55)
    card_h = Inches(3.6)
    card_y = Inches(3.2)
    start_x = Inches(8.4)
    gap = Inches(0.2)
    for i, (role, status) in enumerate(advisors):
        x = start_x + (card_w + gap) * i
        add_rect(s, x, card_y, card_w, card_h, PANEL_2, line=PANEL_3)
        # Dashed-look avatar circle
        add_oval(s, x + Inches(0.275), card_y + Inches(0.5),
                 Inches(1.0), Inches(1.0), PANEL_3, line=TEXT_2, line_width=Pt(0.75))
        add_text(s, "?", x + Inches(0.275), card_y + Inches(0.65),
                 Inches(1.0), Inches(0.8),
                 font=FONT_SANS, size=36, color=TEXT_2, bold=True,
                 align=PP_ALIGN.CENTER)
        add_text(s, role, x + Inches(0.15), card_y + Inches(1.8),
                 card_w - Inches(0.3), Inches(0.7),
                 font=FONT_MONO, size=10, color=TEXT_1, bold=True,
                 align=PP_ALIGN.CENTER, line_spacing=1.1)
        add_text(s, status, x + Inches(0.15), card_y + Inches(2.6),
                 card_w - Inches(0.3), Inches(0.4),
                 font=FONT_MONO, size=11, color=AMBER, bold=True,
                 align=PP_ALIGN.CENTER)
        add_text(s, "recruiting", x + Inches(0.15), card_y + Inches(3.0),
                 card_w - Inches(0.3), Inches(0.4),
                 font=FONT_MONO, size=9, color=TEXT_2, align=PP_ALIGN.CENTER)

    add_footer(s, ["github.com/seekerPrice/polaris", "linkedin.com/in/lucasloo"])


def slide_14_ask(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    add_top_corners(s)
    add_tag(s, "WHAT WE'RE ASKING", Inches(0.6), Inches(0.95))
    add_headline(s,
                 "Hackathon-first.\nPilot deployments next.\n$2M Seed in Q1 2027.",
                 Inches(0.6), Inches(1.5), Inches(7), Inches(3.0),
                 size=30, color=WHITE)
    add_body(s,
             "Today's ask is operational, not financial: deploy Polaris as a Veea DevKit pilot in your enterprise. Goal: 3–5 SOC 2 design partners in Q3 2026.",
             Inches(0.6), Inches(4.5), Inches(6.5), Inches(1.5),
             color=TEXT_1, size=14)

    # Future seed allocation (donut substitute: 3 stacked horizontal bars)
    bars = [
        ("ENGINEERING (3 FTE)", 50, CYAN),
        ("SALES & PARTNERSHIPS", 30, EMERALD),
        ("R&D · drift + multi-tenant", 20, AMBER),
    ]
    add_text(s, "Future Seed allocation ($2M)",
             Inches(0.6), Inches(6.2), Inches(7), Inches(0.4),
             font=FONT_MONO, size=11, color=TEXT_2, bold=True)
    bar_total_w = Inches(6.5)
    bar_h = Inches(0.45)
    bar_y = Inches(6.6)
    bar_x = Inches(0.6)
    for label, pct, accent in bars:
        w = bar_total_w * (pct / 100)
        add_rect(s, bar_x, bar_y, w, bar_h, accent)
        add_text(s, f"{pct}%", bar_x + w / 2 - Inches(0.3), bar_y + Inches(0.08),
                 Inches(0.6), Inches(0.3),
                 font=FONT_MONO, size=12, color=NAVY, bold=True,
                 align=PP_ALIGN.CENTER)
        bar_x += w

    # Ideal partner right column
    add_rect(s, Inches(8.3), Inches(1.5), Inches(4.5), Inches(5.0), PANEL,
             line=CYAN_DIM)
    add_rect(s, Inches(8.3), Inches(1.5), Inches(4.5), Inches(0.06), CYAN)
    add_tag(s, "IDEAL PARTNER", Inches(8.5), Inches(1.75), color=CYAN)
    add_bullets(s, [
        "A Veea ecosystem deployment lead (Lobster Trap is the substrate).",
        "A regulated-industry early-adopter (Fortune 2000 in healthcare or fintech).",
        "A counsel-side advisor on EU AI Act high-risk classification (Annex III).",
    ], Inches(8.5), Inches(2.4), Inches(4.1), Inches(4.0), size=12.5)


def slide_15_thank_you(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    # Cyan-bordered emphasis frame
    add_rect(s, Inches(0.3), Inches(0.3), Inches(12.73), Inches(6.9), PANEL,
             line=CYAN, line_width=Pt(1))
    add_text(s, "POLARIS", Inches(0.5), Inches(0.6), Inches(3), Inches(0.4),
             font=FONT_MONO, size=11, color=CYAN)
    add_text(s, "VEEA TRUST TRACK  ·  TECHEX 2026", Inches(9.8), Inches(0.6),
             Inches(3.5), Inches(0.4),
             font=FONT_MONO, size=10, color=TEXT_2, align=PP_ALIGN.RIGHT)
    add_headline(s, "THANK YOU",
                 Inches(0.5), Inches(2.6), Inches(12.33), Inches(2.2),
                 size=130, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, "polaris--lucaslootan.replit.app",
             Inches(0.5), Inches(4.9), Inches(12.33), Inches(0.6),
             font=FONT_MONO, size=22, color=CYAN, bold=True, align=PP_ALIGN.CENTER)
    add_text(s, "lucaslootan@gmail.com  ·  github.com/seekerPrice/polaris",
             Inches(0.5), Inches(5.7), Inches(12.33), Inches(0.5),
             font=FONT_MONO, size=14, color=TEXT_1, align=PP_ALIGN.CENTER)
    add_text(s, "Drop your SOC 2 PDF. Watch the firewall deploy in 11 seconds.",
             Inches(0.5), Inches(6.3), Inches(12.33), Inches(0.5),
             font=FONT_SANS, size=15, color=TEXT_2, align=PP_ALIGN.CENTER)


def slide_a1_qr(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    add_top_corners(s)
    add_tag(s, "APPENDIX  ·  LIVE DEMO", Inches(0.6), Inches(0.95))
    add_headline(s, "Try Polaris yourself.",
                 Inches(0.6), Inches(1.5), Inches(12), Inches(1.0),
                 size=40, color=WHITE)
    add_text(s, "Drop your SOC 2 PDF. Watch the firewall deploy in 11 seconds.",
             Inches(0.6), Inches(2.5), Inches(12), Inches(0.5),
             font=FONT_SANS, size=18, color=TEXT_1)

    # QR centered, white panel behind for scanning contrast
    qr_path = DOCS_IMG / "polaris_qr.png"
    qr_size = Inches(3.5)
    qr_x = (SLIDE_W - qr_size) / 2
    qr_y = Inches(3.4)
    add_rect(s, qr_x - Inches(0.2), qr_y - Inches(0.2),
             qr_size + Inches(0.4), qr_size + Inches(0.4),
             WHITE, line=CYAN, line_width=Pt(2))
    if qr_path.exists():
        try:
            s.shapes.add_picture(str(qr_path), qr_x, qr_y, width=qr_size)
        except Exception:
            pass

    add_text(s, "polaris--lucaslootan.replit.app",
             Inches(0.5), Inches(6.9), Inches(12.33), Inches(0.45),
             font=FONT_MONO, size=20, color=CYAN, bold=True,
             align=PP_ALIGN.CENTER)


def slide_a2_architecture(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    add_top_corners(s)
    add_tag(s, "APPENDIX  ·  ARCHITECTURE", Inches(0.6), Inches(0.95))
    add_headline(s, "The 4-agent + Lobster Trap loop.",
                 Inches(0.6), Inches(1.5), Inches(12), Inches(1.0),
                 size=30, color=WHITE)

    # Hand-drawn architecture using shapes
    boxes = [
        # (label, x, y, w, h, accent)
        ("Compliance\nPDF", 0.6, 3.0, 1.7, 1.3, TEXT_2),
        ("READER\nAGENT", 2.7, 3.0, 1.7, 1.3, CYAN),
        ("SYNTHESIZER\nAGENT", 4.8, 3.0, 1.7, 1.3, EMERALD),
        ("policy.yaml\n+ schemas", 6.9, 3.0, 1.7, 1.3, VIOLET),
        ("LOBSTER\nTRAP DPI", 9.0, 3.0, 1.7, 1.3, AMBER),
        ("Demo\nAgent", 11.1, 3.0, 1.7, 1.3, TEXT_2),
        ("MISMATCH\nDETECTOR", 5.85, 4.9, 1.7, 1.0, VIOLET),
        ("RED TEAM\nAGENT", 8.0, 4.9, 1.7, 1.0, ROSE),
    ]
    for label, x, y, w, h, accent in boxes:
        add_rect(s, Inches(x), Inches(y), Inches(w), Inches(h),
                 PANEL, line=accent, line_width=Pt(1))
        add_text(s, label, Inches(x), Inches(y) + Inches(0.15),
                 Inches(w), Inches(h),
                 font=FONT_MONO, size=10, color=accent, bold=True,
                 align=PP_ALIGN.CENTER, line_spacing=1.2)

    # Forward flow arrows
    arrow_specs = [
        (2.3, 3.65, 0.4),
        (4.4, 3.65, 0.4),
        (6.5, 3.65, 0.4),
        (8.6, 3.65, 0.4),
        (10.7, 3.65, 0.4),
    ]
    for x, y, w in arrow_specs:
        add_text(s, "→", Inches(x), Inches(y - 0.1),
                 Inches(w), Inches(0.3),
                 font=FONT_MONO, size=18, color=CYAN, bold=True,
                 align=PP_ALIGN.CENTER)
    # Loop back: lobster trap → mismatch → red team → synthesizer
    add_text(s, "audit log →", Inches(8.0), Inches(4.4),
             Inches(1.5), Inches(0.3),
             font=FONT_MONO, size=9, color=TEXT_2, bold=True)
    add_text(s, "↓", Inches(9.85), Inches(4.3),
             Inches(0.3), Inches(0.4),
             font=FONT_MONO, size=18, color=AMBER, bold=True,
             align=PP_ALIGN.CENTER)
    add_text(s, "regenerate ↑", Inches(5.5), Inches(4.4),
             Inches(2), Inches(0.3),
             font=FONT_MONO, size=9, color=ROSE, bold=True, align=PP_ALIGN.RIGHT)

    add_text(s,
             "Full architecture in CLAUDE.md §3. The Mismatch Detector compares Lobster Trap's _lobstertrap declared-intent vs detected — gaps fire the Red Team probe loop.",
             Inches(0.6), Inches(6.4), Inches(12.1), Inches(0.6),
             font=FONT_SANS, size=11, color=TEXT_2, align=PP_ALIGN.CENTER)

    add_footer(s, [
        "github.com/seekerPrice/polaris",
        "github.com/veeainc/lobstertrap",
    ])


def slide_a3_compliance(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, NAVY)
    add_top_corners(s)
    add_tag(s, "APPENDIX  ·  COMPLIANCE COVERAGE", Inches(0.6), Inches(0.95))
    add_headline(s, "Every rule traces to a named, citable control.",
                 Inches(0.6), Inches(1.5), Inches(12), Inches(1.0),
                 size=24, color=WHITE)

    headers = ["Source control", "Polaris rule examples", "LT action"]
    rows = [
        ("SOC 2 CC6.1 (Logical access)",
         "block_credential_exfiltration", "DENY"),
        ("SOC 2 CC8.1 (Change management)",
         "ApprovalGate consent before deploy", "HUMAN_REVIEW"),
        ("HIPAA §164.312(a)(2) (Access control)",
         "block_phi_unauthorized", "DENY"),
        ("EU AI Act Art. 9 (Risk management)",
         "quarantine_borderline_credential", "QUARANTINE"),
        ("OWASP LLM01 (Prompt Injection)",
         "block_obfuscation_attempts", "DENY"),
        ("OWASP LLM06 (Sensitive Info Disclosure)",
         "egress DPI scan rules", "LOG + DENY"),
    ]
    n_rows = len(rows) + 1
    n_cols = 3
    table_shape = s.shapes.add_table(n_rows, n_cols,
                                     Inches(0.6), Inches(2.8),
                                     Inches(12.1), Inches(3.6))
    table = table_shape.table
    table.columns[0].width = Inches(4.5)
    table.columns[1].width = Inches(5.0)
    table.columns[2].width = Inches(2.6)
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        style_table_cell(cell, fill=PANEL_2, text_color=CYAN, bold=True,
                         size=11, align=PP_ALIGN.LEFT, font=FONT_MONO)
    for r_idx, row in enumerate(rows, start=1):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = val
            if c_idx == 0:
                style_table_cell(cell, fill=PANEL, text_color=TEXT_1, size=11)
            elif c_idx == 1:
                style_table_cell(cell, fill=PANEL, text_color=WHITE,
                                 size=11, font=FONT_MONO)
            else:
                color = ROSE if "DENY" in val else (
                    AMBER if "HUMAN" in val else (
                        VIOLET if "QUARANTINE" in val else EMERALD))
                style_table_cell(cell, fill=PANEL, text_color=color,
                                 bold=True, size=11, font=FONT_MONO,
                                 align=PP_ALIGN.CENTER)

    add_footer(s, [
        "aicpa-cima.com (SOC 2 TSC)",
        "hhs.gov/hipaa · 45 CFR §164.312",
        "artificialintelligenceact.eu",
        "owasp.org",
    ])


# --- main ---------------------------------------------------------------

def main() -> None:
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    slide_1_cover(prs)
    slide_2_mission(prs)
    slide_3_overview(prs)
    slide_4_problem_why_now(prs)
    slide_5_solution(prs)
    slide_6_product(prs)
    slide_7_closed_loop(prs)
    slide_8_market(prs)
    slide_9_competitive(prs)
    slide_10_business_model(prs)
    slide_11_unit_economics(prs)
    slide_12_roadmap(prs)
    slide_13_team(prs)
    slide_14_ask(prs)
    slide_15_thank_you(prs)
    slide_a1_qr(prs)
    slide_a2_architecture(prs)
    slide_a3_compliance(prs)

    OUT.parent.mkdir(exist_ok=True)
    prs.save(str(OUT))
    print(f"Wrote {OUT}  ·  {len(prs.slides)} slides")


if __name__ == "__main__":
    main()
