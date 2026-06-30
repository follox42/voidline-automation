#!/usr/bin/env python3
"""Daily Short — produces and schedules ONE Short for today (12:00 UTC publish).

Pipeline:
  1. Read weekly_plans/YYYY-WW.md → find today's Short row.
  2. Based on Type:
     - HOOK / ANSWER → cut from a published long-form (uses shorts/short_cutter_v2.py)
     - discovery → render from a fresh script using existing assets
  3. Generate thumb (Flow Nano Banana 2 + Fern overlay).
  4. Upload via shorts/upload_shorts.py.
  5. Schedule via shorts/schedule_shorts.py for today 12:00 UTC.
  6. Update shorts/shorts_state.json.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLANS = REPO / "weekly_plans"
SHORTS = REPO / "shorts"
STATE = SHORTS / "shorts_state.json"


def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def find_today_row() -> dict | None:
    plans = sorted(PLANS.glob("*.md"))
    if not plans:
        return None
    txt = plans[-1].read_text()
    today = today_iso()
    for line in txt.splitlines():
        m = re.match(r"\|\s*\w+\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(\w+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if m and m.group(1) == today:
            return {
                "date": today,
                "type": m.group(2).lower(),
                "source": m.group(3).strip(),
                "hook_question": m.group(4).strip(),
                "iconic_detail": m.group(5).strip(),
            }
    return None


def run():
    dry = os.environ.get("VOIDLINE_DRY_RUN", "0") == "1"
    halt_file = REPO / "HALT"
    if halt_file.exists():
        print("[daily-short] HALT — abort")
        return

    row = find_today_row()
    if not row:
        print(f"[daily-short] no row for {today_iso()} in latest plan — skip")
        return
    print(f"[daily-short] today's row: {row}")

    state = json.loads(STATE.read_text()) if STATE.exists() else {"shorts": []}
    short_id = f"short_{today_iso()}_{row['type']}"
    if any(s.get("id") == short_id for s in state.get("shorts", [])):
        print(f"[daily-short] {short_id} already produced — skip")
        return

    out_mp4 = SHORTS / f"{short_id}.mp4"

    if row["type"] in ("hook", "answer"):
        # Cut from a published long-form
        source_run = REPO / "runs" / row["source"]
        if not source_run.exists():
            print(f"[daily-short] FAIL — source run dir not found: {source_run}")
            sys.exit(1)
        config = {
            "source": str(source_run / "render" / "voidline.mp4"),
            "start_s": 0 if row["type"] == "hook" else 600,
            "duration_s": 60,
            "out": str(out_mp4),
            "header_text": row["source"].upper(),
            "hook_duration_s": 1.5,
            "outro_duration_s": 4.0,
            "hook_question": row["hook_question"],
            "outro_question": "WHAT'S YOUR\\NTHEORY?",
            "outro_cta": "COMMENT ↓",
            "mask_until_s": 45 if row["type"] == "hook" else 0,
            "captions": [],
        }
        cfg_file = SHORTS / f"{short_id}.json"
        cfg_file.write_text(json.dumps(config, indent=2))
        if dry:
            print(f"[DRY] would run cutter v2 with {cfg_file}")
        else:
            r = subprocess.run([sys.executable, str(SHORTS / "short_cutter_v2.py"), str(cfg_file)],
                                capture_output=True, text=True)
            print(r.stdout[-500:], r.stderr[-500:])
            if r.returncode != 0:
                print("[daily-short] FAIL — cutter v2 returned non-zero")
                sys.exit(1)
    else:
        # Discovery short — needs a fresh 60s render
        print(f"[daily-short] DISCOVERY type — agent must produce manually, then re-run with --resume")
        return

    # Thumb
    if dry:
        print(f"[DRY] would gen thumb for {short_id}")
    else:
        r = subprocess.run([sys.executable, str(SHORTS / "make_fern_thumb.py"), short_id,
                            row["hook_question"], row["iconic_detail"]],
                           capture_output=True, text=True)
        print(r.stdout[-500:], r.stderr[-500:])

    # Upload + schedule
    publish_at = f"{today_iso()}T12:00:00Z"
    if dry:
        print(f"[DRY] would upload + schedule {short_id} for {publish_at}")
    else:
        r = subprocess.run([sys.executable, str(SHORTS / "upload_shorts.py"), short_id, publish_at],
                           capture_output=True, text=True)
        print(r.stdout[-500:], r.stderr[-500:])
        if r.returncode != 0:
            print("[daily-short] FAIL — upload returned non-zero")
            sys.exit(1)

    # Update state
    state.setdefault("shorts", []).append({
        "id": short_id,
        "date": today_iso(),
        "type": row["type"],
        "publish_at": publish_at,
        "hook_question": row["hook_question"],
        "status": "scheduled",
    })
    STATE.write_text(json.dumps(state, indent=2))
    print(f"[daily-short] DONE — {short_id} scheduled for {publish_at}")


if __name__ == "__main__":
    run()
