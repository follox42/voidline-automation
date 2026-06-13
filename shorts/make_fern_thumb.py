#!/usr/bin/env python3
"""Voidline thumbnail in v1 thumb_A template (Fern-style with red arrow).

v1 thumb_A reference pattern:
- Cinematic image, LIGHTLY graded
- Gold headline TOP-LEFT (not centered), warm gold #E0B854
- White date subtitle directly below headline
- Hand-drawn RED arrow pointing to a key element in the image
- No vignette

Usage: python3 make_fern_thumb.py <config.json>
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

FONT = "/host/home/follox/clover-build/camoufox/bundle/fonts/windows/impact.ttf"
W, H = 1280, 720

WARM_GOLD = "#E0B854"   # warmer than pure #FFD700 — matches v1 thumb_A
WHITE = "#FFFFFF"
RED = "#D9343F"


def base(src: Path, brightness=0.95, saturation=0.85, contrast=1.10):
    img = Image.open(src).convert("RGB")
    img = ImageOps.fit(img, (W, H), Image.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Color(img).enhance(saturation)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    return img


def draw_text(img, text, x, y, size, color, stroke_w, stroke_color="black"):
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, size)
    d.text((x, y), text, font=font, fill=color,
           stroke_width=stroke_w, stroke_fill=stroke_color)
    bbox = d.textbbox((x, y), text, font=font, stroke_width=stroke_w)
    return bbox[3]  # bottom y


def draw_arrow(img, *, tip, length=220, angle_deg=-35,
               shaft_w=58, head_w=130, head_len=110,
               color=RED, stroke="black", stroke_w=6):
    """Draw a hand-drawn arrow with tip at (tx, ty), pointing in angle_deg
    direction (0=right, -90=up, 90=down). The tail extends `length` from the
    tip in the *opposite* direction.

    angle_deg=-35 → arrow comes from upper-left, points to lower-right of tip.
    """
    tx, ty = tip
    ang = math.radians(angle_deg)
    # Tail = opposite direction from tip
    tail_dx = -math.cos(ang) * length
    tail_dy = -math.sin(ang) * length
    # Perpendicular vector (unit) for width
    perp = (-math.sin(ang), math.cos(ang))

    # Tip triangle: extends head_len behind tip
    head_back = (tx + math.cos(ang) * (-head_len),
                 ty + math.sin(ang) * (-head_len))
    head_left = (head_back[0] + perp[0] * head_w / 2,
                 head_back[1] + perp[1] * head_w / 2)
    head_right = (head_back[0] - perp[0] * head_w / 2,
                  head_back[1] - perp[1] * head_w / 2)

    # Shaft rectangle: from shaft_back (near head_back) to tail
    shaft_back = head_back
    shaft_tail = (tx + tail_dx, ty + tail_dy)

    # Build polygon: tip → head_right → shaft_back_right → shaft_tail_right →
    #                shaft_tail_left → shaft_back_left → head_left → tip
    shaft_back_right = (shaft_back[0] - perp[0] * shaft_w / 2,
                        shaft_back[1] - perp[1] * shaft_w / 2)
    shaft_back_left = (shaft_back[0] + perp[0] * shaft_w / 2,
                       shaft_back[1] + perp[1] * shaft_w / 2)
    shaft_tail_right = (shaft_tail[0] - perp[0] * shaft_w / 2,
                        shaft_tail[1] - perp[1] * shaft_w / 2)
    shaft_tail_left = (shaft_tail[0] + perp[0] * shaft_w / 2,
                       shaft_tail[1] + perp[1] * shaft_w / 2)

    poly = [
        tip,
        head_right,
        shaft_back_right,
        shaft_tail_right,
        shaft_tail_left,
        shaft_back_left,
        head_left,
    ]

    d = ImageDraw.Draw(img)
    d.polygon(poly, fill=color, outline=stroke, width=stroke_w)


def make(cfg: dict) -> Path:
    src = Path(cfg["src"])
    out = Path(cfg["out"])
    img = base(src,
               brightness=cfg.get("brightness", 0.95),
               saturation=cfg.get("saturation", 0.85),
               contrast=cfg.get("contrast", 1.10))

    # Headline (gold, top-left)
    x = cfg.get("text_x", 40)
    y = cfg.get("text_y", 24)
    bottom = draw_text(img, cfg["headline"], x, y,
                       size=cfg.get("headline_size", 145),
                       color=cfg.get("headline_color", WARM_GOLD),
                       stroke_w=cfg.get("headline_stroke", 9))

    # Date subtitle (white, below headline)
    if cfg.get("date"):
        date_size = cfg.get("date_size", 80)
        date_x = cfg.get("date_x", x + 20)
        date_y = bottom + cfg.get("date_gap", -8)
        draw_text(img, cfg["date"], date_x, date_y,
                  size=date_size, color=WHITE,
                  stroke_w=cfg.get("date_stroke", 5))

    # Red arrow pointing to key element
    arrow = cfg.get("arrow")
    if arrow:
        draw_arrow(img,
                   tip=tuple(arrow["tip"]),
                   length=arrow.get("length", 220),
                   angle_deg=arrow.get("angle", -35),
                   shaft_w=arrow.get("shaft_w", 58),
                   head_w=arrow.get("head_w", 130),
                   head_len=arrow.get("head_len", 110),
                   stroke_w=arrow.get("stroke_w", 6))

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "JPEG", quality=92, optimize=True)
    print(f"OK → {out}  ({out.stat().st_size//1024} KB)")
    return out


if __name__ == "__main__":
    make(json.loads(Path(sys.argv[1]).read_text()))
