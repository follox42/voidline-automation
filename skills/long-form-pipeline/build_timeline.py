#!/usr/bin/env python3
"""
Step 4 — Timeline Builder
Usage: python3 skills/long-form-pipeline/build_timeline.py <run_dir>
"""
import os, sys, json, glob

RUN_DIR = sys.argv[1] if len(sys.argv) > 1 else "runs/v4-roanoke"
ASSETS_DIR = os.path.join(RUN_DIR, "assets/images")
VOICE_DIR = os.path.join(RUN_DIR, "voice")

# Voice durations (from Step 2)
VOICE_DURATIONS = {
    0: 46.158367,
    1: 85.707755,
    2: 107.31102,
    3: 90.226939,
    4: 115.017143,
    5: 106.292245,
}

CHAPTER_TITLES = {
    0: "A Colony Gone",
    1: "The 1587 Expedition",
    2: "Three Missing Years",
    3: "CROATOAN: The Only Clue",
    4: "400 Years of Theories",
    5: "What Archaeology Found",
}

def get_chapter_assets(ch_id):
    """Get all downloaded assets for a chapter, sorted."""
    pattern = os.path.join(ASSETS_DIR, f"ch{ch_id}_*.jpg")
    pattern2 = os.path.join(ASSETS_DIR, f"ch{ch_id}_*.png")
    files = sorted(glob.glob(pattern) + glob.glob(pattern2))
    return files

def build_timeline():
    entries = []
    current_t = 0.0
    total_duration = sum(VOICE_DURATIONS.values())

    for ch_id in range(6):
        ch_dur = VOICE_DURATIONS[ch_id]
        voice_path = os.path.join(VOICE_DIR, f"ch{ch_id}.mp3")
        assets = get_chapter_assets(ch_id)

        if not assets:
            # Use a simple black placeholder
            entries.append({
                "chapter_id": ch_id,
                "chapter_title": CHAPTER_TITLES[ch_id],
                "asset": None,
                "voice": voice_path,
                "start_s": round(current_t, 3),
                "duration_s": round(ch_dur, 3),
                "transition": "fade",
                "effect": "still",
            })
            current_t += ch_dur
            continue

        # Deduplicate assets (same image fetched twice sometimes)
        seen_sizes = set()
        unique_assets = []
        for a in assets:
            sz = os.path.getsize(a)
            if sz not in seen_sizes:
                seen_sizes.add(sz)
                unique_assets.append(a)
        assets = unique_assets

        # Distribute duration across assets
        dur_per_asset = ch_dur / len(assets)
        for i, asset_path in enumerate(assets):
            effect = "ken_burns" if dur_per_asset > 8 else "still"
            transition = "fade" if i == 0 else "dissolve"
            entries.append({
                "chapter_id": ch_id,
                "chapter_title": CHAPTER_TITLES[ch_id],
                "asset": asset_path,
                "voice": voice_path if i == 0 else None,
                "start_s": round(current_t, 3),
                "duration_s": round(dur_per_asset, 3),
                "transition": transition,
                "effect": effect,
            })
            current_t += dur_per_asset

    timeline = {
        "run_id": "v4-roanoke",
        "total_duration_s": round(total_duration, 3),
        "total_duration_hms": f"{int(total_duration//3600):02d}:{int((total_duration%3600)//60):02d}:{total_duration%60:05.2f}",
        "chapter_count": 6,
        "entries": entries,
    }

    out_path = os.path.join(RUN_DIR, "timeline.json")
    with open(out_path, "w") as f:
        json.dump(timeline, f, indent=2)
    print(f"Timeline: {len(entries)} entries, {timeline['total_duration_hms']}")
    print(f"Written: {out_path}")
    return timeline

if __name__ == "__main__":
    t = build_timeline()
    for e in t["entries"]:
        asset_name = os.path.basename(e["asset"]) if e["asset"] else "(black)"
        print(f"  {e['start_s']:.1f}s ch{e['chapter_id']} [{e['chapter_title']}] {asset_name} {e['duration_s']:.1f}s {e['effect']}")
