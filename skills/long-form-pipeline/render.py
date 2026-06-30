#!/usr/bin/env python3
"""
Step 5 — Long-form render via ffmpeg
Usage: python3 skills/long-form-pipeline/render.py <run_dir>

Strategy: concat-demuxer approach — create a concat list of per-slide clips,
then concatenate + mux audio. Avoids complex filtergraph label collisions.
"""
import os, sys, json, subprocess, shutil
from pathlib import Path

RUN_DIR = sys.argv[1] if len(sys.argv) > 1 else "runs/v4-roanoke"
TIMELINE_PATH = os.path.join(RUN_DIR, "timeline.json")
RENDER_DIR = os.path.join(RUN_DIR, "render")
SLIDES_DIR = os.path.join(RENDER_DIR, "slides")
OUT_PATH = os.path.join(RENDER_DIR, "voidline.mp4")
CONCAT_AUDIO = os.path.join(RENDER_DIR, "audio_concat.mp3")

W, H = 1920, 1080
CHAPTER_CARD_DURATION = 2.5

CHAPTER_TITLES = [
    "A Colony Gone",
    "The 1587 Expedition",
    "Three Missing Years",
    "CROATOAN: The Only Clue",
    "400 Years of Theories",
    "What Archaeology Found",
]


def build_concat_audio(chapters, out_path):
    """Concatenate per-chapter voice files into one audio track."""
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
        print(f"  [SKIP] audio already concatenated")
        return True
    list_file = out_path.replace(".mp3", "_list.txt")
    with open(list_file, "w") as f:
        for ch in chapters:
            voice = ch["voice_path"]
            if os.path.exists(voice):
                f.write(f"file '{os.path.abspath(voice)}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
           "-i", list_file, "-c", "copy", out_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("Audio concat error:", r.stderr[-300:])
        return False
    print(f"  Audio OK → {out_path} ({os.path.getsize(out_path)//1024}KB)")
    return True


def render_slide(asset_path, duration_s, out_path, chapter_id=None, slide_idx_in_chapter=0):
    """Render one slide: image → graded+scaled MP4 clip (no audio)."""
    if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
        return True

    # Color grade: sepia/warm + teal shadows
    grade = (
        "colorchannelmixer=rr=0.9:rg=0.1:rb=0.0:"
        "gr=0.06:gg=0.85:gb=0.09:"
        "br=0.06:bg=0.05:bb=0.89,"
        "eq=contrast=1.08:brightness=-0.02:saturation=0.70"
    )

    # Chapter title card on first slide of each chapter
    title_overlay = ""
    if slide_idx_in_chapter == 0 and chapter_id is not None and chapter_id < len(CHAPTER_TITLES):
        ch_num = f"Chapter {chapter_id + 1}"
        title_txt = CHAPTER_TITLES[chapter_id].replace("'", "\\'").replace(":", "\\:")
        ch_num_txt = ch_num.replace("'", "\\'")
        t_start = 0.3
        t_end = min(CHAPTER_CARD_DURATION, duration_s - 0.1)
        title_overlay = (
            f",drawbox=x=0:y=850:w={W}:h=130:color=black@0.65:t=fill:enable='between(t,{t_start:.2f},{t_end:.2f})'"
            f",drawtext=text='{ch_num_txt}':fontcolor=0xE0B854:fontsize=36:x=60:y=860:enable='between(t,{t_start:.2f},{t_end:.2f})'"
            f",drawtext=text='{title_txt}':fontcolor=white:fontsize=52:x=60:y=905:enable='between(t,{t_start:.2f},{t_end:.2f})'"
        )

    if asset_path:
        vf = (
            f"scale={W}:{H}:flags=lanczos:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"format=yuv420p,{grade}{title_overlay}"
        )
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-t", str(duration_s), "-i", asset_path,
            "-vf", vf,
            "-fps_mode", "cfr", "-r", "25",
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-an", out_path,
        ]
    else:
        # Black frame
        vf = f"scale={W}:{H},format=yuv420p{title_overlay}"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-t", str(duration_s),
            "-i", f"color=black:size={W}x{H}:rate=25",
            "-vf", vf,
            "-fps_mode", "cfr", "-r", "25",
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-an", out_path,
        ]

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  Slide render error: {r.stderr[-400:]}")
        return False
    return True


def build_slideshow_video(timeline, out_path):
    """Render each slide individually, then concatenate."""
    os.makedirs(SLIDES_DIR, exist_ok=True)
    slide_paths = []
    total = 0
    for ch in timeline["chapters"]:
        ch_id = ch["chapter_id"]
        for s_idx, slide in enumerate(ch["slides"]):
            total += 1
            slide_name = f"ch{ch_id}_s{s_idx:03d}.mp4"
            slide_path = os.path.join(SLIDES_DIR, slide_name)
            print(f"  [{total}] ch{ch_id} slide {s_idx}: {slide['duration_s']:.1f}s", end="", flush=True)
            ok = render_slide(
                slide.get("asset"),
                slide["duration_s"],
                slide_path,
                chapter_id=ch_id,
                slide_idx_in_chapter=s_idx,
            )
            if ok:
                print(f" OK")
                slide_paths.append(slide_path)
            else:
                print(f" FAILED")

    if not slide_paths:
        return False

    # Write concat list
    concat_list = os.path.join(SLIDES_DIR, "concat.txt")
    with open(concat_list, "w") as f:
        for p in slide_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")

    print(f"  Concatenating {len(slide_paths)} slide clips...")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-fps_mode", "cfr", "-r", "25",
        "-c:v", "libx264", "-crf", "22", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-an", out_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        print("Concat error:", r.stderr[-400:])
        return False
    sz = os.path.getsize(out_path)
    print(f"  Slideshow OK → {out_path} ({sz//1024//1024}MB)")
    return True


def mux_audio(video_path, audio_path, out_path):
    """Mux video + audio into final MP4."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path, "-i", audio_path,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest", "-movflags", "+faststart",
        out_path,
    ]
    print("  Muxing video + audio...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("Mux error:", r.stderr[-300:])
        return False
    sz = os.path.getsize(out_path)
    print(f"  Final OK → {out_path} ({sz//1024//1024}MB)")
    return True


def main():
    os.makedirs(RENDER_DIR, exist_ok=True)

    if os.path.exists(OUT_PATH) and os.path.getsize(OUT_PATH) > 1_000_000:
        print(f"[SKIP] Render already exists: {OUT_PATH}")
        return

    with open(TIMELINE_PATH) as f:
        timeline = json.load(f)

    chapters = timeline["chapters"]
    print("=== Step 5: Render (concat-demuxer) ===")

    print("\n--- Step 5a: Audio ---")
    ok = build_concat_audio(chapters, CONCAT_AUDIO)
    if not ok:
        sys.exit(1)

    raw_video = os.path.join(RENDER_DIR, "slideshow_raw.mp4")
    print("\n--- Step 5b: Per-slide render + concat ---")
    ok = build_slideshow_video(timeline, raw_video)
    if not ok:
        sys.exit(1)

    print("\n--- Step 5c: Mux ---")
    ok = mux_audio(raw_video, CONCAT_AUDIO, OUT_PATH)
    if not ok:
        sys.exit(1)

    # Probe
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", OUT_PATH],
        capture_output=True, text=True,
    )
    if probe.returncode == 0:
        info = json.loads(probe.stdout)
        dur = float(info.get("format", {}).get("duration", 0))
        sz = int(info.get("format", {}).get("size", 0))
        print(f"\n=== Render Complete: {dur:.1f}s ({dur/60:.1f}min), {sz//1024//1024}MB ===")


if __name__ == "__main__":
    main()
