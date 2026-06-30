#!/usr/bin/env python3
"""
Step 6 (fallback path) — Long-form thumbnail from a Wikimedia source image.

Used when Flow Nano Banana 2 generation is unavailable/blocked (see
skills/voidline-manager/LEARNINGS.md). Same Fern-style visual language as
shorts/make_fern_thumb.py (gold headline top-left, white date, red arrow)
but pointed at a local bold font instead of the MCP-server-only Impact path,
since this script runs in the pipeline sandbox, not on the camoufox host.

Usage: python3 skills/long-form-pipeline/make_long_thumb.py <config.json>
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
W, H = 1280, 720

WARM_GOLD = "#E0B854"
WHITE = "#FFFFFF"
RED = "#D9343F"


def base(src: Path, brightness=0.9, saturation=0.55, contrast=1.15, sepia_teal=True):
    img = Image.open(src).convert("RGB")
    img = ImageOps.fit(img, (W, H), Image.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Color(img).enhance(saturation)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    if sepia_teal:
        # cheap split-tone: warm highlights, cool shadows (LEMMiNO/Fern palette)
        r, g, b = img.split()
        r = r.point(lambda v: min(255, int(v * 1.08 + 6)))
        b = b.point(lambda v: min(255, int(v * 1.04)))
        img = Image.merge("RGB", (r, g, b))
    return img


def draw_text(img, text, x, y, size, color, stroke_w, stroke_color="black"):
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, size)
    d.text((x, y), text, font=font, fill=color, stroke_width=stroke_w, stroke_fill=stroke_color)
    bbox = d.textbbox((x, y), text, font=font, stroke_width=stroke_w)
    return bbox[3]


def draw_arrow(img, *, tip, length=220, angle_deg=-35, shaft_w=50, head_w=110, head_len=95,
               color=RED, stroke="black", stroke_w=6):
    tx, ty = tip
    ang = math.radians(angle_deg)
    tail_dx, tail_dy = -math.cos(ang) * length, -math.sin(ang) * length
    perp = (-math.sin(ang), math.cos(ang))
    head_back = (tx + math.cos(ang) * (-head_len), ty + math.sin(ang) * (-head_len))
    head_left = (head_back[0] + perp[0] * head_w / 2, head_back[1] + perp[1] * head_w / 2)
    head_right = (head_back[0] - perp[0] * head_w / 2, head_back[1] - perp[1] * head_w / 2)
    shaft_back = head_back
    shaft_tail = (tx + tail_dx, ty + tail_dy)
    shaft_back_right = (shaft_back[0] - perp[0] * shaft_w / 2, shaft_back[1] - perp[1] * shaft_w / 2)
    shaft_back_left = (shaft_back[0] + perp[0] * shaft_w / 2, shaft_back[1] + perp[1] * shaft_w / 2)
    shaft_tail_right = (shaft_tail[0] - perp[0] * shaft_w / 2, shaft_tail[1] - perp[1] * shaft_w / 2)
    shaft_tail_left = (shaft_tail[0] + perp[0] * shaft_w / 2, shaft_tail[1] + perp[1] * shaft_w / 2)
    poly = [tip, head_right, shaft_back_right, shaft_tail_right, shaft_tail_left, shaft_back_left, head_left]
    ImageDraw.Draw(img).polygon(poly, fill=color, outline=stroke, width=stroke_w)


def make(cfg: dict) -> Path:
    src = Path(cfg["src"])
    out = Path(cfg["out"])
    img = base(src, brightness=cfg.get("brightness", 0.9), saturation=cfg.get("saturation", 0.55),
               contrast=cfg.get("contrast", 1.15))

    x = cfg.get("text_x", 40)
    y = cfg.get("text_y", 24)
    bottom = draw_text(img, cfg["headline"], x, y, size=cfg.get("headline_size", 130),
                        color=cfg.get("headline_color", WARM_GOLD), stroke_w=cfg.get("headline_stroke", 9))

    if cfg.get("date"):
        date_size = cfg.get("date_size", 72)
        date_x = cfg.get("date_x", x + 6)
        date_y = bottom + cfg.get("date_gap", -4)
        draw_text(img, cfg["date"], date_x, date_y, size=date_size, color=WHITE,
                  stroke_w=cfg.get("date_stroke", 5))

    arrow = cfg.get("arrow")
    if arrow:
        draw_arrow(img, tip=tuple(arrow["tip"]), length=arrow.get("length", 220),
                   angle_deg=arrow.get("angle", -35), shaft_w=arrow.get("shaft_w", 50),
                   head_w=arrow.get("head_w", 110), head_len=arrow.get("head_len", 95),
                   stroke_w=arrow.get("stroke_w", 6))

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "JPEG", quality=92, optimize=True)
    print(f"OK -> {out} ({out.stat().st_size // 1024} KB)")
    return out


if __name__ == "__main__":
    make(json.loads(Path(sys.argv[1]).read_text()))
