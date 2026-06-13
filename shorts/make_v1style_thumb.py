#!/usr/bin/env python3
"""Voidline thumbnail in v1-winner template.

v1 winner pattern (from voidline_thumb_B.jpg):
- Image fills full frame, LIGHTLY graded (not crushed dark)
- Question headline gold + black stroke, positioned at TOP (~5% from top)
- Red factual subtitle directly below the question, smaller
- No vignette, no watermark
- Image stays the visual lead, text is the hook

Usage: python3 make_v1style_thumb.py <config.json>

config.json:
    {
      "src": "/path/to/archive/photo.jpg",
      "out": "/path/to/output.jpg",
      "brightness": 0.95,
      "saturation": 0.85,
      "question": "WHO KILLED THE 9?",
      "question_size": 140,
      "fact": "BAREFOOT IN -30°C",
      "fact_size": 70
    }
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

FONT_IMPACT = "/host/home/follox/clover-build/camoufox/bundle/fonts/windows/impact.ttf"
W, H = 1280, 720
GOLD = "#FFD700"
RED = "#E63946"


def base(src: Path, brightness=0.95, saturation=0.85, sepia=False) -> Image.Image:
    """Crop + scale + LIGHT grading (preserve image energy)."""
    img = Image.open(src).convert("RGB")
    img = ImageOps.fit(img, (W, H), Image.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Color(img).enhance(saturation)
    img = ImageEnhance.Contrast(img).enhance(1.10)
    if sepia:
        r, g, b = img.split()
        r = r.point(lambda i: min(255, int(i * 1.06)))
        b = b.point(lambda i: int(i * 0.86))
        img = Image.merge("RGB", (r, g, b))
    return img


def draw_top_text(img: Image.Image, text: str, *, y: int, size: int,
                  color: str, stroke_w: int, stroke_color="black",
                  font_path=FONT_IMPACT) -> int:
    """Draw centered text at y, return bottom y for stacking."""
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, size)
    bbox = d.textbbox((0, 0), text, font=font, stroke_width=stroke_w)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (W - tw) // 2 - bbox[0]
    d.text((x, y), text, font=font, fill=color,
           stroke_width=stroke_w, stroke_fill=stroke_color)
    return y + th + 8  # bottom + small gap


def make(cfg: dict) -> Path:
    src = Path(cfg["src"])
    out = Path(cfg["out"])
    img = base(src,
               brightness=cfg.get("brightness", 0.95),
               saturation=cfg.get("saturation", 0.85),
               sepia=cfg.get("sepia", False))

    # Question at TOP — gold + thick black stroke
    y = cfg.get("text_top", 20)
    q_size = cfg.get("question_size", 140)
    next_y = draw_top_text(img, cfg["question"],
                            y=y, size=q_size,
                            color=GOLD,
                            stroke_w=cfg.get("question_stroke", 12))

    # Fact subtitle just below — red
    if cfg.get("fact"):
        draw_top_text(img, cfg["fact"],
                      y=next_y - 4, size=cfg.get("fact_size", 70),
                      color=cfg.get("fact_color", RED),
                      stroke_w=cfg.get("fact_stroke", 6))

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "JPEG", quality=92, optimize=True)
    print(f"OK → {out}  ({out.stat().st_size//1024} KB)")
    return out


if __name__ == "__main__":
    make(json.loads(Path(sys.argv[1]).read_text()))
