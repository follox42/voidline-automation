#!/usr/bin/env python3
"""
Step 5 — ffmpeg Render Pipeline (v2, subprocess list args)
Usage: python3 skills/long-form-pipeline/render.py <run_dir>
"""
import os, sys, json, subprocess, time, shutil

RUN_DIR = sys.argv[1] if len(sys.argv) > 1 else "runs/v4-roanoke"
TIMELINE_PATH = os.path.join(RUN_DIR, "timeline.json")
RENDER_DIR = os.path.join(RUN_DIR, "render")
VOICE_DIR = os.path.join(RUN_DIR, "voice")
SCRATCH_DIR = os.path.join(RUN_DIR, "render", "scratch")
OUTPUT_MP4 = os.path.join(RENDER_DIR, "voidline_v4_roanoke.mp4")
FPS = 30
W, H = 1280, 720
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

os.makedirs(RENDER_DIR, exist_ok=True)
os.makedirs(SCRATCH_DIR, exist_ok=True)

def run_ffmpeg(args, label="", timeout=300):
    """Run ffmpeg with list args (safe for special chars)."""
    start = time.time()
    cmd = ["ffmpeg", "-y"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    elapsed = time.time() - start
    if result.returncode != 0:
        print(f"  ERROR [{label}]: {result.stderr[-400:]}")
        return False
    print(f"  OK [{label}] {elapsed:.1f}s")
    return True

def get_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True
    )
    try:
        return float(json.loads(result.stdout)["format"]["duration"])
    except Exception:
        return 0.0

def make_image_clip(asset_path, duration_s, out_path, chapter_title, first_in_chapter):
    """Render one image as a video clip with Ken Burns + grade."""
    frames = int(duration_s * FPS)

    # Build vf chain
    # 1. Scale + pad to 1280x720
    scale_pad = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black"
    # 2. Ken Burns slow zoom
    zoompan = f"zoompan=z='min(zoom+0.0003,1.10)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}"
    # 3. Sepia + teal grade (simplified, avoids single-quote issues)
    grade = "colorchannelmixer=.39:.77:.19:0:.35:.69:.17:0:.27:.53:.13:0,eq=brightness=-0.03:contrast=1.1:saturation=0.8"
    # 4. Watermark
    watermark = f"drawtext=fontfile={FONT}:text=VOIDLINE:fontsize=22:fontcolor=0x888888@0.6:x=w-110:y=h-30:borderw=1:bordercolor=0x000000@0.5"
    # 5. Chapter card (first frame of first clip in chapter)
    if first_in_chapter and chapter_title:
        safe_title = chapter_title.upper().replace("'", "").replace(":", " -")
        chcard = f"drawtext=fontfile={FONT}:text={safe_title}:fontsize=26:fontcolor=0xE0B854@0.9:x=20:y=h-55:borderw=2:bordercolor=0x000000@0.8:enable='between(t,0,3)'"
        vf = f"{scale_pad},{zoompan},{grade},{chcard},{watermark}"
    else:
        vf = f"{scale_pad},{zoompan},{grade},{watermark}"

    args = [
        "-loop", "1", "-i", asset_path,
        "-t", str(duration_s), "-r", str(FPS),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        out_path
    ]
    return run_ffmpeg(args, f"clip {os.path.basename(out_path)[:30]}", timeout=120)

def make_black_clip(duration_s, out_path):
    args = [
        "-f", "lavfi", "-i", f"color=c=black:size={W}x{H}:r={FPS}",
        "-t", str(duration_s),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        out_path
    ]
    return run_ffmpeg(args, "black_clip")

def stitch_audio(voice_paths):
    """Concatenate all chapter MP3s into a single AAC track."""
    concat_txt = os.path.join(SCRATCH_DIR, "audio_concat.txt")
    with open(concat_txt, "w") as f:
        for vp in voice_paths:
            f.write(f"file '{os.path.abspath(vp)}'\n")
    out_path = os.path.join(SCRATCH_DIR, "master_voice.aac")
    args = [
        "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-af", "alimiter=level_in=1:level_out=0.9:limit=-1dB:attack=5:release=50:asc=1",
        "-c:a", "aac", "-b:a", "192k",
        out_path
    ]
    ok = run_ffmpeg(args, "stitch audio", timeout=60)
    return out_path if ok else None

def concatenate_clips(clip_paths):
    """Concatenate video clips using concat demuxer."""
    concat_txt = os.path.join(SCRATCH_DIR, "video_concat.txt")
    with open(concat_txt, "w") as f:
        for cp in clip_paths:
            f.write(f"file '{os.path.abspath(cp)}'\n")
    out_path = os.path.join(SCRATCH_DIR, "raw_video.mp4")
    args = [
        "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-c", "copy",
        out_path
    ]
    ok = run_ffmpeg(args, "concat video", timeout=60)
    return out_path if ok else None

def mux_final(video_path, audio_path, out_path, total_dur):
    """Mux video + audio, add fade in/out."""
    fade_out_start = max(0, total_dur - 2.5)
    args = [
        "-i", video_path, "-i", audio_path,
        "-map", "0:v", "-map", "1:a",
        "-af", f"afade=in:st=0:d=1.5,afade=out:st={fade_out_start:.2f}:d=2.5",
        "-vf", f"fade=in:st=0:d=1.5,fade=out:st={fade_out_start:.2f}:d=2.5",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        out_path
    ]
    return run_ffmpeg(args, "mux final", timeout=600)

def main():
    print("=== Step 5: ffmpeg Render ===")
    start_total = time.time()

    if os.path.exists(OUTPUT_MP4) and os.path.getsize(OUTPUT_MP4) > 1_000_000:
        size_mb = os.path.getsize(OUTPUT_MP4) / 1024 / 1024
        print(f"  [SKIP] Output already exists: {OUTPUT_MP4} ({size_mb:.1f}MB)")
        return True

    with open(TIMELINE_PATH) as f:
        timeline = json.load(f)

    total_dur = timeline["total_duration_s"]
    print(f"  {len(timeline['entries'])} clips, {timeline['total_duration_hms']}")

    # Step 1: Render per-image clips
    clip_paths = []
    seen_chapters = set()

    for idx, entry in enumerate(timeline["entries"]):
        ch_id = entry["chapter_id"]
        asset = entry.get("asset")
        dur = entry["duration_s"]
        first = ch_id not in seen_chapters
        seen_chapters.add(ch_id)
        title = entry["chapter_title"] if first else ""

        clip_name = f"clip_{idx:03d}_ch{ch_id}.mp4"
        clip_path = os.path.join(SCRATCH_DIR, clip_name)

        if os.path.exists(clip_path) and os.path.getsize(clip_path) > 10_000:
            print(f"  [SKIP] {clip_name}")
        elif asset and os.path.exists(asset):
            ok = make_image_clip(asset, dur, clip_path, title, first)
            if not ok:
                print(f"  WARN: Falling back to black for {clip_name}")
                make_black_clip(dur, clip_path)
        else:
            make_black_clip(dur, clip_path)

        clip_paths.append(clip_path)

    # Step 2: Stitch audio
    print("\n  Stitching audio...")
    voice_paths = [os.path.join(VOICE_DIR, f"ch{i}.mp3") for i in range(6)]
    audio_path = stitch_audio(voice_paths)
    if not audio_path:
        print("  ERROR: Audio stitch failed")
        return False

    # Step 3: Concatenate clips
    print("\n  Concatenating video clips...")
    raw_video = concatenate_clips(clip_paths)
    if not raw_video:
        return False

    # Step 4: Mux
    print("\n  Muxing final output...")
    ok = mux_final(raw_video, audio_path, OUTPUT_MP4, total_dur)
    if not ok:
        return False

    elapsed = time.time() - start_total
    size_mb = os.path.getsize(OUTPUT_MP4) / 1024 / 1024
    print(f"\n=== Render DONE {elapsed/60:.1f}min — {size_mb:.1f}MB ===")
    if elapsed > 20 * 60:
        print("WARN: Exceeded 20min render limit!")
    return True

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
