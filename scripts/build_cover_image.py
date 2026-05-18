#!/usr/bin/env python3
"""Polaris cover image builder (1920x1080, 16:9) for the lablab.ai submission.

Composes a clean VC-style cover with:
- Left half: Polaris wordmark + tagline + brand accents + URL + metric strip
- Right half: a real dashboard screenshot in a white card frame
- Corner labels: project / Veea Trust Track · TechEx 2026

Run:
    uv run python scripts/build_cover_image.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DASH = ROOT / "docs" / "img" / "dashboard" / "recording" / "04_closed_loop_complete.png"
OUT = ROOT / "docs" / "img" / "cover.png"

# --- VC light palette (same as pitch deck) ---
BG = (250, 250, 252)          # cream
WHITE = (255, 255, 255)
INDIGO = (79, 70, 229)
INDIGO_LIGHT = (99, 102, 241)
INDIGO_DARK = (55, 48, 163)
TEXT_PRIMARY = (15, 23, 42)
TEXT_SECONDARY = (71, 85, 105)
TEXT_MUTED = (148, 163, 184)
BORDER = (226, 232, 240)
SUCCESS = (5, 150, 105)
WARNING = (217, 119, 6)

W, H = 1920, 1080
PAD = 80

FONT_DIRS = [
    Path.home() / "Library" / "Fonts",
    Path("/System/Library/Fonts/Supplemental"),
    Path("/System/Library/Fonts"),
]
FONT_CANDIDATES = {
    "bold": ["InterDisplay-Bold.otf", "Inter-Bold.otf", "Helvetica.ttc"],
    "semibold": ["InterDisplay-SemiBold.otf", "Inter-SemiBold.otf",
                 "Helvetica.ttc"],
    "regular": ["InterDisplay-Regular.otf", "Inter-Regular.otf",
                "Helvetica.ttc"],
    "mono": ["JetBrainsMono-Bold.ttf", "Menlo.ttc"],
}


def find_font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for name in FONT_CANDIDATES[kind]:
        for d in FONT_DIRS:
            p = d / name
            if p.exists():
                try:
                    return ImageFont.truetype(str(p), size)
                except Exception:
                    pass
    return ImageFont.load_default()


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # --- Corner labels ---
    f_corner = find_font("mono", 20)
    draw.text((PAD, 36), "POLARIS · AI AGENT FIREWALL",
              fill=TEXT_MUTED, font=f_corner)
    right = "VEEA TRUST TRACK · TECHEX 2026"
    rw = draw.textlength(right, font=f_corner)
    draw.text((W - PAD - rw, 36), right, fill=TEXT_MUTED, font=f_corner)

    # --- Left brand zone ---
    # Indigo accent strip far-left
    draw.rectangle([(0, 280), (10, 760)], fill=INDIGO)

    # Eyebrow tag
    f_eyebrow = find_font("mono", 22)
    draw.text((PAD, 240), "FROM PDF TO FIREWALL",
              fill=INDIGO, font=f_eyebrow)

    # Big wordmark
    f_huge = find_font("bold", 160)
    draw.text((PAD - 8, 280), "Polaris", fill=TEXT_PRIMARY, font=f_huge)

    # Tagline (2 lines)
    f_tagline = find_font("bold", 52)
    draw.text((PAD, 500),
              "SOC 2 PDF → live AI guardrail",
              fill=TEXT_PRIMARY, font=f_tagline)
    draw.text((PAD, 568),
              "in 60 seconds.",
              fill=INDIGO, font=f_tagline)

    # Sub-line / hero metric
    f_sub = find_font("regular", 30)
    draw.text((PAD, 670),
              "Built solo in seven days. AI guardrails at AI speed.",
              fill=TEXT_SECONDARY, font=f_sub)

    # URL
    f_url = find_font("mono", 22)
    draw.text((PAD, 730),
              "polaris--lucaslootan.replit.app",
              fill=INDIGO, font=f_url)

    # --- Right zone: dashboard screenshot ---
    if DASH.exists():
        dash = Image.open(DASH).convert("RGB")
        # Target box: right ~900px wide
        box_w = 880
        target_w = box_w
        target_h = int(dash.height * (target_w / dash.width))
        if target_h > 720:
            target_h = 720
            target_w = int(dash.width * (target_h / dash.height))
        dash = dash.resize((target_w, target_h), Image.LANCZOS)
        paste_x = W - PAD - target_w
        paste_y = (H - target_h) // 2 - 30
        # White card behind (subtle shadow effect with offset)
        shadow_offset = 8
        draw.rectangle(
            [(paste_x - 12 + shadow_offset, paste_y - 12 + shadow_offset),
             (paste_x + target_w + 12 + shadow_offset,
              paste_y + target_h + 12 + shadow_offset)],
            fill=(220, 224, 232),
        )
        draw.rectangle(
            [(paste_x - 12, paste_y - 12),
             (paste_x + target_w + 12, paste_y + target_h + 12)],
            fill=WHITE, outline=BORDER, width=2,
        )
        img.paste(dash, (paste_x, paste_y))

    # --- Bottom metric strip ---
    metric_y = H - 130
    metrics = [
        ("11 sec", "END-TO-END", INDIGO),
        ("66.7%", "RISK REDUCTION", SUCCESS),
        ("6 / 6", "LT ACTIONS", INDIGO_LIGHT),
        ("3M ×", "COST COMPRESSION", WARNING),
    ]
    f_metric_big = find_font("bold", 48)
    f_metric_cap = find_font("mono", 16)
    metric_x = PAD
    for big, cap, accent in metrics:
        draw.text((metric_x, metric_y), big, fill=accent, font=f_metric_big)
        draw.text((metric_x, metric_y + 64), cap,
                  fill=TEXT_SECONDARY, font=f_metric_cap)
        metric_x += 240

    # --- Bottom horizontal divider ---
    draw.line([(PAD, metric_y - 22), (W - PAD, metric_y - 22)],
              fill=BORDER, width=2)

    img.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT}  ·  {W}×{H} · {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
