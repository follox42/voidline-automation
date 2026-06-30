#!/usr/bin/env python3
"""Progress curve — append weekly metrics + compute ETA milestones.

Usage:
    python3 progress_curve.py append <json_payload>
    python3 progress_curve.py eta  # print ETA milestones from current trajectory
"""
import csv
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROG = REPO / "progress"
PROG.mkdir(exist_ok=True)
CSV = PROG / "weekly_curve.csv"

COLS = [
    "week", "total_subs", "subs_gained", "total_views", "videos_pub",
    "best_ctr", "median_retention", "hours_watched", "shorts_views_total"
]


def iso_week(d: datetime) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def cmd_append(payload: dict):
    payload.setdefault("week", iso_week(datetime.now(timezone.utc)))
    new = not CSV.exists() or CSV.stat().st_size == 0
    with open(CSV, "a") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        if new:
            w.writeheader()
        w.writerow({k: payload.get(k, "") for k in COLS})
    print(f"[progress] appended {payload['week']}")


def cmd_eta():
    if not CSV.exists():
        print("[progress] no data yet")
        return
    rows = list(csv.DictReader(open(CSV)))
    if len(rows) < 2:
        print("[progress] need >= 2 weeks of data for ETA")
        return
    recent = rows[-4:] if len(rows) >= 4 else rows
    avg_subs_gain = sum(int(r["subs_gained"] or 0) for r in recent) / len(recent)
    avg_hours = sum(float(r["hours_watched"] or 0) for r in recent) / len(recent)
    cur_subs = int(rows[-1]["total_subs"] or 0)
    cur_hours_cum = sum(float(r["hours_watched"] or 0) for r in rows)

    milestones = []
    for target_subs in (100, 500, 1000):
        if cur_subs >= target_subs:
            continue
        if avg_subs_gain <= 0:
            milestones.append({"goal": f"{target_subs} subs", "eta_weeks": "∞"})
        else:
            milestones.append({"goal": f"{target_subs} subs", "eta_weeks": round((target_subs - cur_subs) / avg_subs_gain, 1)})

    for target_hours in (100, 500, 1000):
        if cur_hours_cum >= target_hours:
            continue
        if avg_hours <= 0:
            milestones.append({"goal": f"{target_hours} watch-hours", "eta_weeks": "∞"})
        else:
            milestones.append({"goal": f"{target_hours} watch-hours", "eta_weeks": round((target_hours - cur_hours_cum) / avg_hours, 1)})

    print(json.dumps({
        "current_subs": cur_subs,
        "cumulative_hours": round(cur_hours_cum, 1),
        "4wk_avg_subs_gain": round(avg_subs_gain, 1),
        "4wk_avg_hours_per_week": round(avg_hours, 1),
        "milestones": milestones,
    }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: append <json> | eta")
    if sys.argv[1] == "append":
        cmd_append(json.loads(sys.argv[2]))
    elif sys.argv[1] == "eta":
        cmd_eta()
