#!/usr/bin/env python3
"""Build a portrait (1080x1920) Ken-Burns base render for a discovery Short.

Reads runs/<run_id>/assets/manifest.json (ch0 images) and assembles a silent
1080x1920 h264/AAC mp4 with a slow zoom-in pan per image, crossfaded, at
runs/<run_id>/render/base.mp4. This is the "source" short_cutter_v2.py then
cuts hook/caption/outro cards onto.

No narration track: caller decides silent vs. real VO upstream (this script
only lays down images + silent audio of the right duration). To add real VO
later, mux runs/<run_id>/voice/*.mp3 over this render's video track.

Usage: python3 build_discovery_base.py <run_id> [total_duration_s]
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def build(run_id: str, total_s: float = 46.0):
    run_dir = REPO / "runs" / run_id
    manifest = json.loads((run_dir / "assets" / "manifest.json").read_text())
    images = [REPO / a["path"] for a in manifest["ch0"]]
    if not images:
        print("[build_discovery_base] no images in manifest ch0 — abort")
        sys.exit(1)

    out_dir = run_dir / "render"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "base.mp4"

    n = len(images)
    per_img = total_s / n
    fps = 30
    frames = int(per_img * fps)

    inputs = []
    for img in images:
        inputs += ["-loop", "1", "-t", f"{per_img:.3f}", "-i", str(img)]

    # Each image: cover-crop to 1080x1920, then slow zoom-in (1.0 -> 1.12) via zoompan.
    # zoompan's internal frame counter is per-input (0-indexed each loop), so
    # 'frames' below is safe per-clip and does not compound across concatenated
    # inputs (the earlier zoompan-explosion bug came from reusing a running/global
    # zoom expression across a single long input instead of one zoompan per clip).
    filter_parts = []
    labels = []
    for i in range(n):
        zoom_step = 0.12 / max(frames, 1)
        filt = (
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"zoompan=z='min(zoom+{zoom_step:.6f},1.12)':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps},"
            f"format=yuv420p[v{i}]"
        )
        filter_parts.append(filt)
        labels.append(f"[v{i}]")

    # Crossfade-concat consecutive clips (0.6s overlap each)
    xfade_dur = 0.6
    if n == 1:
        concat_filter = f"{labels[0]}copy[vout]"
    else:
        concat_filter = ""
        prev = labels[0]
        offset = per_img - xfade_dur
        for i in range(1, n):
            out_lbl = f"[x{i}]" if i < n - 1 else "[vout]"
            concat_filter += f"{prev}{labels[i]}xfade=transition=fade:duration={xfade_dur}:offset={offset:.3f}{out_lbl};"
            prev = out_lbl
            offset += per_img - xfade_dur
        concat_filter = concat_filter.rstrip(";")

    filter_complex = ";".join(filter_parts) + ";" + concat_filter

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-f", "lavfi", "-t", f"{total_s:.3f}", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", f"{n}:a",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
        "-movflags", "+faststart", "-r", str(fps),
        "-t", f"{total_s:.3f}",
        str(out_path),
    ]
    print(" ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("=== STDERR ===")
        print(r.stderr[-3000:])
        sys.exit(1)
    sz = out_path.stat().st_size / 1024 / 1024
    print(f"OK -> {out_path} ({sz:.1f} MB, {total_s:.1f}s)")


if __name__ == "__main__":
    run_id = sys.argv[1]
    total_s = float(sys.argv[2]) if len(sys.argv) > 2 else 46.0
    build(run_id, total_s)
