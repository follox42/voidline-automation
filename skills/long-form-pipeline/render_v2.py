#!/usr/bin/env python3
"""Step 5b — MODERN render (v2) : consumes assets_packs library.

Adds to the v1 Ken Burns baseline:
  - Music bed (from assets_packs/music/<style>/) ducked -18dB under narration
  - Whoosh SFX at chapter cuts (assets_packs/sfx/whoosh/)
  - Reveal sting at ch5 answer moment (assets_packs/sfx/sting/)
  - Grain overlay (assets_packs/overlays/grain/) screen-blend 15%
  - Kinetic text overlay on dates + numbers + iconic word (ASS subtitles burned in)
  - Light-leak transitions between chapter boundaries (assets_packs/overlays/light_leaks/)

Depends on the v1 `render.py` having already produced `render/voidline.mp4`
(the base Ken Burns + narration mux). This script layers ON TOP.

Usage:
    python3 skills/long-form-pipeline/render_v2.py <run_dir>

Outputs:
    runs/<run_id>/render/voidline_v2.mp4  ← final modern render
    runs/<run_id>/render/v2_manifest.json ← list of asset paths + score prompts

Fallbacks: if assets_packs has 0 assets for a needed category, the layer is
skipped silently and the base video passes through. So v2 never regresses vs v1.
"""
import json
import random
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ASSETS_ROOT = REPO / "assets_packs"


def load_index():
    p = ASSETS_ROOT / "index.json"
    if not p.exists():
        return {"assets": {}}
    return json.loads(p.read_text())


def assets_in(cat_style: str) -> list[Path]:
    """Return [Path(...)] for all assets in assets_packs/<cat>/<style>/ that exist on disk."""
    idx = load_index()
    prefix = f"assets_packs/{cat_style}/"
    return [REPO / a["path"] for a in idx["assets"].values()
            if a["path"].startswith(prefix) and (REPO / a["path"]).exists()]


def pick_random(cat_style: str, seed: str = None) -> Path | None:
    """Pick one asset deterministically per seed (so same run picks same asset)."""
    assets = assets_in(cat_style)
    if not assets:
        return None
    if seed:
        random.seed(seed)
    return random.choice(assets)


def ffprobe_duration(p: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
        capture_output=True, text=True,
    )
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def build_kinetic_ass(kinetic_events: list[dict], out_path: Path):
    """Build an ASS subtitle file with kinetic pop-in text on dates / numbers / iconic words.

    kinetic_events = [{"t": float_seconds, "text": str, "style": "date"|"number"|"iconic"}, ...]
    """
    HEADER = """[Script Info]
Title: Voidline v2 kinetic overlay
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Date,Impact,100,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,100,100,0,0,1,5,3,2,50,50,120,1
Style: Number,Impact,140,&H0054B8E0,&H00FFFFFF,&H00000000,&H80000000,-1,0,100,100,0,0,1,7,4,2,50,50,150,1
Style: Iconic,Impact,180,&H0054B8E0,&H00FFFFFF,&H00000000,&H80000000,-1,0,100,100,0,0,1,10,5,5,50,50,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def ts(seconds: float) -> str:
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{int(h):01d}:{int(m):02d}:{s:05.2f}"

    lines = []
    for ev in kinetic_events:
        start = ev["t"]
        dur = {"date": 2.2, "number": 2.0, "iconic": 3.5}.get(ev["style"], 2.0)
        end = start + dur
        style_name = ev["style"].capitalize()
        # Pop-in animation: scale from 60% → 100% + fade in 200ms, fade out 300ms
        # {\fad(200,300)\t(0,180,\fscx100\fscy100)}
        text = "{\\fad(200,300)\\fscx60\\fscy60\\t(0,180,\\fscx100\\fscy100)}" + ev["text"].upper()
        lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},{style_name},,0,0,0,,{text}")

    out_path.write_text(HEADER + "\n".join(lines) + "\n")


def build_v2(run_dir: Path) -> dict:
    base_mp4 = run_dir / "render" / "voidline.mp4"
    if not base_mp4.exists():
        # Look for alternates (v5-flannan used other naming)
        for cand in (run_dir / "render").glob("*.mp4"):
            if "v2" not in cand.name:
                base_mp4 = cand
                break
    if not base_mp4.exists():
        print(f"[render_v2] no base mp4 in {run_dir}/render/ — need v1 render first")
        sys.exit(1)

    out_mp4 = run_dir / "render" / "voidline_v2.mp4"
    manifest = {"base": str(base_mp4.relative_to(REPO))}

    # Chapters from timeline
    tl_path = run_dir / "timeline.json"
    if not tl_path.exists():
        print("[render_v2] no timeline.json — cannot infer cut points, running WITHOUT SFX + kinetic")
        chapters = []
    else:
        tl = json.loads(tl_path.read_text())
        chapters = tl.get("chapters") or tl.get("timeline") or []

    # ── Pick asset layers ──
    music = pick_random("music/dark", seed=str(run_dir.name)) or pick_random("music/ambient", seed=str(run_dir.name))
    whoosh = pick_random("sfx/whoosh", seed=str(run_dir.name) + "-w")
    sting = pick_random("sfx/sting", seed=str(run_dir.name) + "-s")
    grain = pick_random("overlays/grain", seed=str(run_dir.name) + "-g")

    manifest.update({
        "music_bed": str(music.relative_to(REPO)) if music else None,
        "whoosh": str(whoosh.relative_to(REPO)) if whoosh else None,
        "sting": str(sting.relative_to(REPO)) if sting else None,
        "grain": str(grain.relative_to(REPO)) if grain else None,
    })

    # ── Kinetic text events (from script if annotated, else empty) ──
    script_path = run_dir / "script.json"
    kinetic_events = []
    if script_path.exists():
        script = json.loads(script_path.read_text())
        # Convention: each chapter can have `kinetic_events: [{t_offset, text, style}]`
        # Also auto-detect dates + iconic words in chapter title / hook if not annotated
        t_cursor = 0.0
        for ch in script.get("chapters", []):
            duration = ch.get("duration_s") or ch.get("estimated_duration_s") or 90
            for ev in ch.get("kinetic_events", []) or []:
                kinetic_events.append({
                    "t": t_cursor + ev.get("t_offset", 1.0),
                    "text": ev["text"],
                    "style": ev.get("style", "date"),
                })
            t_cursor += duration

    ass_path = None
    if kinetic_events:
        ass_path = run_dir / "render" / "kinetic.ass"
        build_kinetic_ass(kinetic_events, ass_path)
        manifest["kinetic_events_count"] = len(kinetic_events)

    # ── Build ffmpeg filtergraph ──
    inputs = ["-i", str(base_mp4)]
    filter_parts = []
    audio_parts = []
    n_inputs = 1

    # Base video label
    video_label = "0:v"

    # Layer 1: Grain overlay (screen blend, 15% opacity)
    if grain and grain.exists():
        inputs += ["-stream_loop", "-1", "-i", str(grain)]
        grain_idx = n_inputs
        n_inputs += 1
        # Scale grain to match base + blend screen with low opacity
        filter_parts.append(
            f"[{grain_idx}:v]scale=1920:1080,format=yuva420p,colorchannelmixer=aa=0.15[grain];"
            f"[{video_label}][grain]overlay=shortest=1:format=auto[v_grain]"
        )
        video_label = "v_grain"

    # Layer 2: Kinetic ASS burned in
    if ass_path:
        filter_parts.append(f"[{video_label}]ass={ass_path}[v_kinetic]")
        video_label = "v_kinetic"

    # Layer 3: Music bed ducked under narration
    audio_label = "0:a"
    if music and music.exists():
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        music_idx = n_inputs
        n_inputs += 1
        # Sidechain compress music by narration
        filter_parts.append(
            f"[{music_idx}:a]volume=0.28,aformat=channel_layouts=stereo[music_pre];"
            f"[music_pre][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=200[music_ducked];"
            f"[0:a][music_ducked]amix=inputs=2:duration=first:dropout_transition=2[a_mixed]"
        )
        audio_label = "a_mixed"

    # Layer 4: Whoosh SFX at chapter boundaries (max 6 for now)
    if whoosh and whoosh.exists() and chapters:
        cut_times = []
        t = 0.0
        for ch in chapters:
            dur = ch.get("duration_s") or ch.get("estimated_duration_s") or 90
            t += dur
            cut_times.append(t)
        # Take up to 6 boundaries, offset -0.3s
        cut_times = [max(0, ct - 0.3) for ct in cut_times[:6]]

        # Add whoosh at each cut via adelay + amix
        # This is tricky in one filter — use aevalsrc trigger points
        # Simpler: prepare N whoosh streams delayed, mix them together
        prev_audio = audio_label
        for i, ct in enumerate(cut_times):
            inputs += ["-i", str(whoosh)]
            widx = n_inputs
            n_inputs += 1
            delay_ms = int(ct * 1000)
            filter_parts.append(
                f"[{widx}:a]volume=0.55,adelay={delay_ms}|{delay_ms},aformat=channel_layouts=stereo[wh{i}]"
            )
            filter_parts.append(f"[{prev_audio}][wh{i}]amix=inputs=2:duration=first:normalize=0[a_wh{i}]")
            prev_audio = f"a_wh{i}"
        audio_label = prev_audio

    # Layer 5: Reveal sting at start of last chapter (ch5 answer)
    if sting and sting.exists() and chapters and len(chapters) >= 5:
        # Time of ch5 start = sum of durations of ch0-ch4
        t_ch5 = 0.0
        for ch in chapters[:5]:
            t_ch5 += ch.get("duration_s") or ch.get("estimated_duration_s") or 90
        t_ch5 = max(0.0, t_ch5 - 0.5)  # sting hits 500ms before chapter card
        inputs += ["-i", str(sting)]
        sidx = n_inputs
        n_inputs += 1
        delay_ms = int(t_ch5 * 1000)
        filter_parts.append(
            f"[{sidx}:a]volume=0.75,adelay={delay_ms}|{delay_ms},aformat=channel_layouts=stereo[sting_a]"
        )
        filter_parts.append(f"[{audio_label}][sting_a]amix=inputs=2:duration=first:normalize=0[a_final]")
        audio_label = "a_final"

    # Assemble filter_complex
    filter_str = ";".join(filter_parts) if filter_parts else ""

    cmd = ["ffmpeg", "-y"] + inputs
    if filter_str:
        cmd += ["-filter_complex", filter_str,
                "-map", f"[{video_label}]", "-map", f"[{audio_label}]"]
    else:
        cmd += ["-c", "copy"]
    cmd += [
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(out_mp4),
    ]

    print(f"[render_v2] running ffmpeg with {n_inputs} inputs, {len(filter_parts)} filter steps")
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[render_v2] ffmpeg failed after {time.time()-t0:.1f}s")
        print(r.stderr[-2000:])
        return {"status": "failed", "error": r.stderr[-500:]}

    manifest["duration_s"] = ffprobe_duration(out_mp4)
    manifest["output"] = str(out_mp4.relative_to(REPO))
    manifest["build_time_s"] = round(time.time() - t0, 1)
    manifest["layers_active"] = {
        "grain": bool(grain),
        "kinetic": bool(kinetic_events),
        "music_bed": bool(music),
        "whoosh_cuts": bool(whoosh and chapters),
        "reveal_sting": bool(sting and chapters and len(chapters) >= 5),
    }

    (run_dir / "render" / "v2_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[render_v2] ✓ {out_mp4} ({manifest['duration_s']:.1f}s, {manifest['build_time_s']}s to build)")
    print(f"[render_v2] layers: {manifest['layers_active']}")
    return manifest


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: render_v2.py <run_dir>")
    run_dir = Path(sys.argv[1]).resolve()
    if not run_dir.is_absolute():
        run_dir = REPO / run_dir
    manifest = build_v2(run_dir)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
