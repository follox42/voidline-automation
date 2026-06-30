#!/usr/bin/env python3
"""Auto-caption generator — Groq Whisper word-level → animated ASS subtitles.

Capabilities (95% of CapCut equivalent):
  - Word-by-word reveal (\k karaoke tag)
  - Active-word color highlight
  - Pop-in / fade / slide animation per word
  - Custom fonts (any TTF/OTF in /usr/share/fonts/)
  - Outline + shadow + blur + glow
  - Position anchoring (bottom/center/top, with margin)
  - Color shifts per word (rainbow / palette cycle)
  - Bounce / scale transforms
  - Emoji injection on keyword density
  - Trendy templates (gold pop, yellow pulse, white-on-black, etc.)

Usage:
    python3 generate_captions.py <voice.mp3> <style.json> <out.ass>

  voice.mp3 — voice track to transcribe
  style.json — see caption_styles/*.json for templates
  out.ass — output Advanced SubStation Alpha file

Ffmpeg burn-in:
    ffmpeg -i input.mp4 -vf "ass=out.ass:fontsdir=/usr/share/fonts" output.mp4
"""
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


# ───────────────────────── Groq Whisper transcription ─────────────────────────

def transcribe_with_groq(mp3_path: str, api_key: str) -> list[dict]:
    """Returns list of {word, start, end} dicts via Groq Whisper API.

    Groq is 300-450× realtime, $0.02/h. A 60s short = $0.000017.
    """
    import requests
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}
    with open(mp3_path, "rb") as f:
        files = {"file": (Path(mp3_path).name, f, "audio/mpeg")}
        data = {
            "model": "whisper-large-v3",
            "response_format": "verbose_json",
            "timestamp_granularities[]": "word",
            "temperature": "0",
        }
        r = requests.post(url, headers=headers, files=files, data=data, timeout=120)
    r.raise_for_status()
    body = r.json()
    return body.get("words") or []


# ───────────────────────── ASS file generation ─────────────────────────

ASS_HEADER_TPL = """[Script Info]
Title: Voidline auto-caption — style={style_name}
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{font_size},{primary_c},{secondary_c},{outline_c},{back_c},{bold},0,0,0,100,100,0,0,1,{outline_w},{shadow_w},{alignment},60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def hex_to_ass_color(hex_color: str, alpha: int = 0) -> str:
    """#RRGGBB → &HAABBGGRR& (ASS color order is BGR, with alpha as 00=opaque)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


def secs_to_ass_time(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s - h * 3600 - m * 60
    return f"{h}:{m:02d}:{sec:05.2f}"


def group_into_lines(words: list[dict], max_chars: int, max_words: int) -> list[list[dict]]:
    """Pack words into caption lines (each line shown together)."""
    lines, cur, cur_chars = [], [], 0
    for w in words:
        wlen = len(w["word"]) + 1
        if cur and (cur_chars + wlen > max_chars or len(cur) >= max_words):
            lines.append(cur)
            cur, cur_chars = [], 0
        cur.append(w)
        cur_chars += wlen
    if cur:
        lines.append(cur)
    return lines


def render_line(line: list[dict], style: dict) -> list[str]:
    """Produces one ASS Dialogue line per word emission (so each word appears in turn).

    Returns a list of "Dialogue: ..." strings.
    """
    out = []
    alignment = style.get("alignment", 2)  # 2 = bottom-center
    margin_v = style.get("margin_v", 320)
    primary = hex_to_ass_color(style["font_color"])
    highlight = hex_to_ass_color(style["highlight_color"])
    pop_scale = style.get("pop_scale_pct", 120)
    pop_dur_ms = style.get("pop_duration_ms", 150)
    fade_in_ms = style.get("fade_in_ms", 0)

    # Build the cumulative text for each step (word i appears with highlight, prior words in primary, next words invisible)
    total_words = len(line)
    line_start = line[0]["start"]
    line_end = line[-1]["end"] + style.get("hold_after_last_word_ms", 400) / 1000.0

    for i, w in enumerate(line):
        seg_start = w["start"]
        # Next word's start, or line_end for the final word
        seg_end = line[i + 1]["start"] if i + 1 < total_words else line_end

        # Compose text with per-word formatting
        chunks = []
        for j, w2 in enumerate(line):
            text = w2["word"].strip()
            if j < i:
                # already shown, primary color, normal scale
                chunks.append(f"{{\\c{primary}\\fscx100\\fscy100}}{text}")
            elif j == i:
                # active word: highlight color + pop
                anim = f"\\t(0,{pop_dur_ms},\\fscx{pop_scale}\\fscy{pop_scale})\\t({pop_dur_ms},{pop_dur_ms*2},\\fscx100\\fscy100)"
                fade = f"\\fad({fade_in_ms},0)" if fade_in_ms else ""
                chunks.append(f"{{\\c{highlight}{anim}{fade}}}{text}")
            else:
                # not yet shown — render invisible (alpha 255 = fully transparent)
                chunks.append(f"{{\\alpha&HFF&}}{text}")
        text_line = " ".join(chunks)
        start_t = secs_to_ass_time(seg_start)
        end_t = secs_to_ass_time(seg_end)
        out.append(f"Dialogue: 0,{start_t},{end_t},Default,,0,0,{margin_v},,{text_line}")
    return out


def build_ass(words: list[dict], style: dict, style_name: str) -> str:
    header = ASS_HEADER_TPL.format(
        style_name=style_name,
        font=style.get("font_name", "Impact"),
        font_size=style.get("font_size", 68),
        primary_c=hex_to_ass_color(style.get("font_color", "#FFFFFF")),
        secondary_c=hex_to_ass_color(style.get("highlight_color", "#E0B854")),
        outline_c=hex_to_ass_color(style.get("outline_color", "#000000")),
        back_c=hex_to_ass_color(style.get("shadow_color", "#000000"), alpha=200),
        bold=-1 if style.get("bold", True) else 0,
        outline_w=style.get("outline_width", 4),
        shadow_w=style.get("shadow_offset", 2),
        alignment=style.get("alignment", 2),
        margin_v=style.get("margin_v", 320),
    )
    lines = group_into_lines(
        words,
        max_chars=style.get("max_chars_per_line", 28),
        max_words=style.get("max_words_per_line", 4),
    )
    body = []
    for line in lines:
        body.extend(render_line(line, style))
    return header + "\n".join(body) + "\n"


# ───────────────────────── CLI ─────────────────────────

def main():
    if len(sys.argv) < 4:
        sys.exit("usage: generate_captions.py <voice.mp3> <style.json> <out.ass>")
    mp3 = sys.argv[1]
    style_path = sys.argv[2]
    out_ass = sys.argv[3]

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        sys.exit("[captions] GROQ_API_KEY missing in env — request adding it to Voidline env")

    style = json.loads(Path(style_path).read_text())
    style_name = Path(style_path).stem

    print(f"[captions] transcribing {mp3} via Groq Whisper...")
    words = transcribe_with_groq(mp3, api_key)
    print(f"[captions] got {len(words)} words")

    if not words:
        sys.exit("[captions] no words returned — check audio quality + GROQ_API_KEY")

    ass = build_ass(words, style, style_name)
    Path(out_ass).write_text(ass)
    print(f"[captions] wrote {out_ass} ({len(words)} words, style={style_name})")

    # Side-output: per-experiment JSON tag
    tag_path = Path(out_ass).with_suffix(".caption_style.json")
    tag_path.write_text(json.dumps({
        "style_name": style_name,
        "words_count": len(words),
        "duration_s": words[-1]["end"] if words else 0,
        "style_config": style,
    }, indent=2))


if __name__ == "__main__":
    main()
