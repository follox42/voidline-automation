#!/usr/bin/env python3
"""
Step 4 — Timeline builder.
Usage: python3 skills/long-form-pipeline/build_timeline.py <run_dir>

Reads script.json (chapter boundaries), assets/manifest.json (per-chapter
stills) and voice/ch*.mp3 (actual durations via ffprobe), and writes
timeline.json: a flat list of {chapter_id, asset, start_s, duration_s,
zoom_dir, pan_dir, transition} segments covering each chapter's full voice
duration by cycling through that chapter's available stills (~14s/segment,
alternating Ken Burns directions so repeats don't look identical).
"""
import json
import os
import subprocess
import sys

RUN_DIR = sys.argv[1] if len(sys.argv) > 1 else "runs/v4-roanoke"
SCRIPT_PATH = os.path.join(RUN_DIR, "script.json")
MANIFEST_PATH = os.path.join(RUN_DIR, "assets", "manifest.json")
VOICE_DIR = os.path.join(RUN_DIR, "voice")
TARGET_SEGMENT_S = 14.0
ZOOM_DIRS = ["in", "out"]
PAN_DIRS = ["left", "right", "up", "down", "center"]


def ffprobe_duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        text=True,
    )
    return float(out.strip())


def main():
    with open(SCRIPT_PATH) as f:
        script = json.load(f)
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    assets_by_chapter = {}
    for a in manifest:
        assets_by_chapter.setdefault(a["chapter_id"], []).append(a["path"])

    timeline = []
    cursor = 0.0
    for ch in script["chapters"]:
        chapter_id = ch["chapter_id"]
        voice_path = os.path.join(VOICE_DIR, f"ch{chapter_id}.mp3")
        if not os.path.exists(voice_path):
            print(f"WARN: no voice for ch{chapter_id}, skipping")
            continue
        duration = ffprobe_duration(voice_path)
        assets = assets_by_chapter.get(chapter_id, [])
        if not assets:
            print(f"WARN: no assets for ch{chapter_id}")
            continue

        n_segments = max(1, round(duration / TARGET_SEGMENT_S))
        seg_len = duration / n_segments

        for i in range(n_segments):
            asset = assets[i % len(assets)]
            zoom = ZOOM_DIRS[i % len(ZOOM_DIRS)]
            pan = PAN_DIRS[i % len(PAN_DIRS)]
            timeline.append({
                "chapter_id": chapter_id,
                "asset": asset,
                "start_s": round(cursor, 3),
                "duration_s": round(seg_len, 3),
                "zoom_dir": zoom,
                "pan_dir": pan,
                "transition": "crossfade",
                "chapter_boundary": i == 0,
            })
            cursor += seg_len

    out_path = os.path.join(RUN_DIR, "timeline.json")
    with open(out_path, "w") as f:
        json.dump({"segments": timeline, "total_duration_s": round(cursor, 3)}, f, indent=2)

    print(f"=== Timeline built: {len(timeline)} segments, {cursor:.1f}s total ===")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
