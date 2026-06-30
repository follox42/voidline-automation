#!/usr/bin/env python3
"""Voidline Shorts cutter v2 — viral retention principles applied.

Improvements over v1:
1. **HOOK CARD frame 0** — first 1.5s = SOLID BLACK with massive question
   in gold Impact, fullscreen, no image. This is the scroll-stopper.
2. **Pattern interrupt** — caption changes every 1.5-2s (was 3-7s) for the
   first 30s. Cuts re-trigger attention reset.
3. **DEBATE OUTRO** — last 4s = solid gradient + "WHAT'S YOUR THEORY?\nCOMMENT ↓"
   in gold + red. Drives comments which boosts algo signal.
4. Keeps the v1 cutter base (crop, scale, ASS, blur band) for body.

Usage: python3 short_cutter_v2.py config.json
"""
import json
import os
import subprocess
import sys
from pathlib import Path

FONT_IMPACT = "/usr/share/fonts/truetype/impact-alt/impact.ttf"
FONT_NAME = "Anton"   # Anton is the Impact-style fallback available in container
GOLD = "&H0000D7FF"   # BGR format
WHITE = "&H00FFFFFF"
RED = "&H003F34D9"    # #D9343F red


def t(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"


def build_ass(cfg, ass_path):
    """Generate ASS with: hook card (0-1.5s) + body captions + outro card."""
    duration = float(cfg["duration_s"])
    hook_end = cfg.get("hook_duration_s", 1.5)
    outro_start = duration - cfg.get("outro_duration_s", 4.0)

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        # HookCard: massive gold question, vertical center, FULL stack
        f"Style: HookCard, Anton, 220, {GOLD}, {WHITE}, &H00000000, &H80000000, -1, 0, 0, 0, 100, 100, 0, 0, 1, 14, 8, 5, 60, 60, 0, 1",
        # Header: gold cap top, persists through body
        f"Style: Header, Anton, 56, {GOLD}, {WHITE}, &H00000000, &H80000000, -1, 0, 0, 0, 100, 100, 4, 0, 1, 4, 2, 8, 60, 60, 80, 1",
        # Big captions during body
        f"Style: Big, Anton, 140, {WHITE}, {WHITE}, &H00000000, &H80000000, -1, 0, 0, 0, 100, 100, 0, 0, 1, 10, 6, 5, 80, 80, 0, 1",
        # OutroQ: massive gold question at top (drives comments)
        f"Style: OutroQ, Anton, 110, {GOLD}, {WHITE}, &H00000000, &H80000000, -1, 0, 0, 0, 100, 100, 0, 0, 1, 12, 6, 8, 80, 80, 120, 1",
        # OutroCTA: smaller red below the question
        f"Style: OutroCTA, Anton, 96, {RED}, {WHITE}, &H00000000, &H80000000, -1, 0, 0, 0, 100, 100, 0, 0, 1, 10, 4, 2, 80, 80, 200, 1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    # 1. HOOK CARD — frame 0 to hook_end (~1.5s)
    hook_q = cfg.get("hook_question", "").replace("\n", "\\N")
    if hook_q:
        lines.append(
            f"Dialogue: 0,{t(0)},{t(hook_end)},HookCard,,0,0,0,,{{\\fad(0,120)}}{hook_q}"
        )

    # 2. Header during body (hook_end to outro_start)
    header = cfg.get("header_text", "")
    if header:
        lines.append(
            f"Dialogue: 0,{t(hook_end)},{t(outro_start)},Header,,0,0,0,,{header.upper()}"
        )

    # 3. Body captions — these run with body video (which keeps full 0..dur)
    # Captions start at hook_end so they don't compete with the hook card
    for c in cfg.get("captions", []):
        s = c["start"] + hook_end
        e = min(c["end"] + hook_end, outro_start)
        if e <= s:
            continue
        text = c["text"].replace("\n", "\\N")
        lines.append(f"Dialogue: 0,{t(s)},{t(e)},Big,,0,0,0,,{{\\fad(120,120)}}{text}")

    # 4. Outro card — last outro_duration_s
    outro_q = cfg.get("outro_question", "WHAT'S YOUR\\NTHEORY?")
    outro_cta = cfg.get("outro_cta", "COMMENT ↓")
    lines.append(
        f"Dialogue: 0,{t(outro_start)},{t(duration)},OutroQ,,0,0,0,,{{\\fad(200,0)}}{outro_q}"
    )
    lines.append(
        f"Dialogue: 0,{t(outro_start + 0.3)},{t(duration)},OutroCTA,,0,0,0,,{{\\fad(300,0)}}{outro_cta}"
    )

    Path(ass_path).write_text("\n".join(lines))


def cut_short(cfg):
    source = cfg["source"]
    start = float(cfg["start_s"])
    dur = float(cfg["duration_s"])
    out = cfg["out"]
    ass = cfg.get("ass_path") or out.replace(".mp4", ".ass")
    hook_end = cfg.get("hook_duration_s", 1.5)
    outro_dur = cfg.get("outro_duration_s", 4.0)
    outro_start = dur - outro_dur

    build_ass(cfg, ass)
    ass_escaped = ass.replace(":", "\\:").replace("'", "\\'")

    # During hook (0..hook_end): black solid background
    # During body (hook_end..outro_start): cropped video, slight blur band when needed
    # During outro (outro_start..dur): cropped video darkened
    mask_until = float(cfg.get("mask_until_s", 0))

    if mask_until > 0:
        body_chain = (
            f"[0:v]crop=405:720:438:0,scale=1080:1920:flags=lanczos,vignette=PI/5,split=2[basevid][forblur];"
            f"[forblur]crop=1080:680:0:420,boxblur=25:3[bluredband];"
            f"[basevid][bluredband]overlay=0:420:enable='lt(t,{mask_until})'[masked];"
        )
        last_label = "[masked]"
    else:
        body_chain = (
            "[0:v]crop=405:720:438:0,scale=1080:1920:flags=lanczos,vignette=PI/5[basevid];"
        )
        last_label = "[basevid]"

    filter_complex = (
        body_chain +
        # Lower-third dim across body
        f"{last_label}drawbox=x=0:y=720:w=1080:h=560:color=black@0.45:t=fill[dimmed];"
        # Black overlay on first hook_end seconds (the hook card backing)
        f"[dimmed]drawbox=x=0:y=0:w=1080:h=1920:color=black:t=fill:enable='lt(t,{hook_end})'[hooked];"
        # Outro dark gradient on the last outro_dur seconds
        f"[hooked]drawbox=x=0:y=0:w=1080:h=1920:color=black@0.55:t=fill:enable='gte(t,{outro_start})'[finalvid];"
        # ASS captions on top (fontsdir points to Anton/Impact-alt fonts)
        f"[finalvid]ass='{ass_escaped}':fontsdir=/usr/share/fonts/truetype/impact-alt[vout]"
    )

    # Audio: extract from start..duration of source. During hook (first 1.5s)
    # we want LOW audio (the black card with no sound feels off), so fade-in.
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start}", "-t", f"{dur}",
        "-i", source,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "0:a",
        "-af", f"afade=t=in:st=0:d={hook_end},afade=t=out:st={outro_start + 1}:d={outro_dur - 1}",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", "-r", "30",
        out,
    ]
    print(" ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("=== STDERR ===")
        print(r.stderr[-2000:])
        sys.exit(1)
    sz = os.path.getsize(out) / 1024 / 1024
    print(f"OK → {out}  ({sz:.1f} MB)")


if __name__ == "__main__":
    cfg = json.loads(Path(sys.argv[1]).read_text())
    cut_short(cfg)
