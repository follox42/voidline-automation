#!/usr/bin/env python3
"""
Step 4 — Build timeline.json
Maps assets to chapter timings from script.json.
Usage: python3 skills/long-form-pipeline/build_timeline.py <run_dir>
"""
import os, sys, json
from pathlib import Path

RUN_DIR = sys.argv[1] if len(sys.argv) > 1 else "runs/v4-roanoke"
SCRIPT_PATH = os.path.join(RUN_DIR, "script.json")
ASSETS_MANIFEST = os.path.join(RUN_DIR, "assets", "manifest.json")
VOICE_MANIFEST = os.path.join(RUN_DIR, "voice", "manifest.json")
TIMELINE_PATH = os.path.join(RUN_DIR, "timeline.json")

CHAPTER_TITLES = [
    "A Colony Gone",
    "The 1587 Expedition",
    "Three Missing Years",
    "CROATOAN: The Only Clue",
    "400 Years of Theories",
    "What Archaeology Found",
]


def main():
    with open(SCRIPT_PATH) as f:
        script = json.load(f)
    with open(ASSETS_MANIFEST) as f:
        assets = json.load(f)
    with open(VOICE_MANIFEST) as f:
        voice = json.load(f)

    chapters = script["chapters"]
    timeline_entries = []

    for ch in chapters:
        ch_id = ch["chapter_id"]
        start_s = ch["start_sec"]
        end_s = ch["end_sec"]
        duration = end_s - start_s
        ch_title = CHAPTER_TITLES[ch_id] if ch_id < len(CHAPTER_TITLES) else f"Chapter {ch_id}"

        ch_assets = assets.get(f"ch{ch_id}", [])
        voice_file = os.path.join(RUN_DIR, "voice", f"ch{ch_id}.mp3")
        v_entry = next((v for v in voice["chapters"] if v["chapter_id"] == ch_id), None)

        if not ch_assets:
            # Fallback: black frame for the full chapter duration
            timeline_entries.append({
                "chapter_id": ch_id,
                "title": ch_title,
                "start_s": start_s,
                "end_s": end_s,
                "voice_path": voice_file,
                "slides": [{"asset": None, "start_s": start_s, "duration_s": duration, "transition": "none"}],
            })
            continue

        # Distribute chapter duration across available images
        n_imgs = len(ch_assets)
        # Each image gets equal time, min 3s max 15s
        img_dur = duration / n_imgs
        img_dur = max(3.0, min(15.0, img_dur))

        # If images don't fill the chapter, cycle through them
        slides = []
        t = start_s
        img_idx = 0
        while t < end_s - 0.5:
            remaining = end_s - t
            actual_dur = min(img_dur, remaining)
            asset = ch_assets[img_idx % n_imgs]
            slides.append({
                "asset": asset["path"],
                "start_s": round(t, 2),
                "duration_s": round(actual_dur, 2),
                "transition": "dissolve" if img_idx > 0 else "none",
            })
            t += actual_dur
            img_idx += 1

        timeline_entries.append({
            "chapter_id": ch_id,
            "title": ch_title,
            "start_s": start_s,
            "end_s": end_s,
            "voice_path": voice_file,
            "slides": slides,
        })

        print(f"  ch{ch_id} '{ch_title}': {n_imgs} assets, {len(slides)} slides, {duration:.1f}s")

    # Write timeline
    out = {
        "run_id": "v4-roanoke",
        "total_duration_s": 715.0,
        "chapters": timeline_entries,
    }
    with open(TIMELINE_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nTimeline written to {TIMELINE_PATH}")


if __name__ == "__main__":
    print("=== Step 4: Build Timeline ===")
    main()
