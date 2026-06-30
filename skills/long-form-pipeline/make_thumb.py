#!/usr/bin/env python3
"""
Step 6 — Fern-style thumbnail generator (Wikimedia base fallback)
Usage: python3 skills/long-form-pipeline/make_thumb.py <run_dir>
"""
import os, sys, math, json
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

RUN_DIR = sys.argv[1] if len(sys.argv) > 1 else "runs/v4-roanoke"
ASSETS_DIR = os.path.join(RUN_DIR, "assets/images")
THUMB_DIR = os.path.join(RUN_DIR, "flow_thumbs")
os.makedirs(THUMB_DIR, exist_ok=True)

# Use best available bold font (Liberation Sans Bold as Impact stand-in)
FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
W, H = 1280, 720
WARM_GOLD = "#E0B854"
WHITE = "#FFFFFF"
RED = "#D9343F"

CFG = {
    # Best Wikimedia base for CROATOAN: William Ludwell Sheppard engraving
    "src": os.path.join(ASSETS_DIR, "ch3_07_William_Ludwell_Sheppard_&_William_James_Linton_-_.jpg"),
    "out": os.path.join(THUMB_DIR, "voidline_v4_roanoke_thumb_A.jpg"),
    "headline": "JUST GONE",
    "date": "1587",
    "headline_size": 145,
    "date_size": 85,
    "headline_stroke": 9,
    "date_stroke": 5,
    # Arrow tip pointing toward where the carved word would be
    "arrow": {"tip": [860, 360], "length": 200, "angle": -150, "shaft_w": 52, "head_w": 120, "head_len": 100, "stroke_w": 6},
    "brightness": 0.92,
    "saturation": 0.80,
    "contrast": 1.12,
}

def base_image(src, brightness, saturation, contrast):
    img = Image.open(src).convert("RGB")
    img = ImageOps.fit(img, (W, H), Image.LANCZOS)
    # Apply sepia-like grade to simulate AI cinematic look
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Color(img).enhance(saturation)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    return img

def draw_text(img, text, x, y, size, color, stroke_w):
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, size)
    d.text((x, y), text, font=font, fill=color, stroke_width=stroke_w, stroke_fill="black")
    bbox = d.textbbox((x, y), text, font=font, stroke_width=stroke_w)
    return bbox[3]

def draw_arrow(img, tip, length=200, angle_deg=-35, shaft_w=52, head_w=120, head_len=100, stroke_w=6, **_):
    tx, ty = tip
    ang = math.radians(angle_deg)
    perp = (-math.sin(ang), math.cos(ang))
    tail_dx = -math.cos(ang) * length
    tail_dy = -math.sin(ang) * length
    head_back = (tx + math.cos(ang) * (-head_len), ty + math.sin(ang) * (-head_len))
    head_left  = (head_back[0] + perp[0] * head_w/2, head_back[1] + perp[1] * head_w/2)
    head_right = (head_back[0] - perp[0] * head_w/2, head_back[1] - perp[1] * head_w/2)
    shaft_tail = (tx + tail_dx, ty + tail_dy)
    sbr = (head_back[0] - perp[0]*shaft_w/2, head_back[1] - perp[1]*shaft_w/2)
    sbl = (head_back[0] + perp[0]*shaft_w/2, head_back[1] + perp[1]*shaft_w/2)
    str_ = (shaft_tail[0] - perp[0]*shaft_w/2, shaft_tail[1] - perp[1]*shaft_w/2)
    stl = (shaft_tail[0] + perp[0]*shaft_w/2, shaft_tail[1] + perp[1]*shaft_w/2)
    poly = [(tx,ty), head_right, sbr, str_, stl, sbl, head_left]
    d = ImageDraw.Draw(img)
    d.polygon(poly, fill=RED, outline="black", width=stroke_w)

def make_thumb(cfg):
    print(f"  Base: {cfg['src']}")
    if not os.path.exists(cfg["src"]):
        print(f"  ERROR: base image not found: {cfg['src']}")
        return False

    img = base_image(cfg["src"], cfg.get("brightness", 0.95), cfg.get("saturation", 0.85), cfg.get("contrast", 1.10))

    # Headline (gold, top-left)
    x, y = 40, 24
    bottom = draw_text(img, cfg["headline"], x, y, cfg["headline_size"], WARM_GOLD, cfg["headline_stroke"])

    # Date (white, below headline)
    if cfg.get("date"):
        draw_text(img, cfg["date"], x + 20, bottom + 4, cfg["date_size"], WHITE, cfg["date_stroke"])

    # Arrow
    if cfg.get("arrow"):
        draw_arrow(img, **cfg["arrow"])

    img.save(cfg["out"], "JPEG", quality=92, optimize=True)
    size_kb = os.path.getsize(cfg["out"]) // 1024
    print(f"  OK → {cfg['out']}  ({size_kb}KB)")
    return True

if __name__ == "__main__":
    print("=== Step 6: Thumbnail (Wikimedia-base fallback) ===")
    ok = make_thumb(CFG)
    if ok:
        print("  Note: Flow unavailable (country block + subscription required).")
        print("  Using Wikimedia engraving base. Swap to AI base post-ship if CTR <3%.")
    sys.exit(0 if ok else 1)
