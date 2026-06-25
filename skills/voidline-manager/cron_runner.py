#!/usr/bin/env python3
"""Voidline autonomous loop runner.

Called by 4 cron schedules: pulse / daily-plan / weekly-review / monthly-recal.

Usage:
    python3 cron_runner.py pulse
    python3 cron_runner.py daily-plan
    python3 cron_runner.py weekly-review
    python3 cron_runner.py monthly-recal

Safety rails:
    - Lockfile prevents concurrent runs
    - HALT file disables uploads
    - Dry-run mode via VOIDLINE_DRY_RUN=1
"""
import csv
import fcntl
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# The openclaw dev host runs this from an absolute run dir. In the Cloud
# Routine container the repo is checked out fresh, so fall back to paths
# resolved relative to this file (<repo>/skills/voidline-manager/cron_runner.py).
_HOST_ROOT = Path("/host/home/follox/.openclaw/yt-viral/runs/voidline-20260527-002843")
_HOST_SKILLS = Path("/host/home/follox/.openclaw/yt-viral/.openclaw/skills/voidline-manager")

if _HOST_ROOT.exists():
    ROOT = _HOST_ROOT
    SKILLS = _HOST_SKILLS
    _REPO_MODE = False
else:
    ROOT = Path(__file__).resolve().parents[2]
    SKILLS = Path(__file__).resolve().parent
    _REPO_MODE = True

LOCKFILE = "/tmp/voidline-manager.lock"
HALTFILE = ROOT / "HALT"

DRY_RUN = bool(os.environ.get("VOIDLINE_DRY_RUN"))


def _agent_log_path():
    """Host writes into the remotion public dir; repo/cloud mode writes the
    log at the repo root since there is no remotion checkout."""
    remotion_log = ROOT / "remotion" / "public" / "agent-log.json"
    if remotion_log.parent.exists():
        return remotion_log
    return ROOT / "agent-log.json"


def log_decision(action, detail):
    """Append to agent-log.json + git push."""
    log_path = _agent_log_path()
    if log_path.exists():
        data = json.loads(log_path.read_text())
    else:
        data = {"decisions": []}
    data["decisions"].append({
        "t": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "action": action,
        "detail": detail,
    })
    log_path.write_text(json.dumps(data, indent=2))
    # The remotion auto-push only makes sense on the openclaw host. In repo/cloud
    # mode the routine itself commits + pushes to the feature branch.
    if not DRY_RUN and not _REPO_MODE:
        try:
            subprocess.run(
                ["git", "-C", str(ROOT / "remotion"),
                 "add", "public/agent-log.json"],
                check=False, capture_output=True, timeout=20,
            )
            subprocess.run(
                ["git", "-C", str(ROOT / "remotion"),
                 "-c", "user.email=nolann42400@gmail.com",
                 "-c", "user.name=follox42",
                 "commit", "-q", "-m", f"manager: {action}"],
                check=False, capture_output=True, timeout=20,
            )
            subprocess.run(
                ["git", "-C", str(ROOT / "remotion"),
                 "push", "origin", "main"],
                check=False, capture_output=True, timeout=30,
            )
        except Exception as e:
            print(f"[warn] git push failed: {e}", file=sys.stderr)


def acquire_lock():
    """Block if another runner is active. Returns lock file handle or None."""
    f = open(LOCKFILE, "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except BlockingIOError:
        print("[skip] another runner holds lock", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# PULSE — runs hourly
# ---------------------------------------------------------------------------

def run_pulse():
    """Pull stats, compare to last snapshot, flag thresholds, log."""
    # Run the monitor script
    result = subprocess.run(
        ["python3", str(ROOT / "shorts" / "monitor_voidline.py")],
        capture_output=True, text=True, timeout=120,
    )

    csv_path = ROOT / "shorts" / "stats_log.csv"
    if not csv_path.exists():
        log_decision("PULSE", "first run, no baseline")
        return

    # Read last 2 snapshots
    rows = list(csv.DictReader(open(csv_path)))
    timestamps = sorted({r["ts"] for r in rows})
    if len(timestamps) < 2:
        log_decision("PULSE", "need 2 snapshots to compute delta")
        return

    prev_ts, cur_ts = timestamps[-2], timestamps[-1]
    prev = {r["asset"]: r for r in rows if r["ts"] == prev_ts}
    cur = {r["asset"]: r for r in rows if r["ts"] == cur_ts}

    alerts = []
    for asset, c in cur.items():
        p = prev.get(asset)
        # Absolute-threshold alerts only need the CURRENT view count — they must
        # NOT be gated behind a valid prior snapshot, or a blank baseline (e.g.
        # the anti-scrape blanks of the 06-13 run) silently suppresses them.
        if not c["views"]:
            continue
        try:
            cv = int(c["views"])
        except ValueError:
            continue
        if cv >= 1000 and c["kind"] == "short":
            alerts.append(f"⭐ {asset}: crossed 1000 views!")
        if cv >= 100 and c["kind"] == "long":
            alerts.append(f"⭐ {asset} long-form: crossed 100v!")
        # Delta alert needs BOTH snapshots present and numeric.
        if not p or not p["views"]:
            continue
        try:
            dv = cv - int(p["views"])
        except ValueError:
            continue
        if dv >= 50:
            alerts.append(f"📈 {asset}: +{dv}v (now {cv})")

    summary = f"Δ {prev_ts.split('T')[1][:5]}→{cur_ts.split('T')[1][:5]}"
    if alerts:
        log_decision("PULSE_ALERT", f"{summary}: " + " | ".join(alerts))
        # In a real cloud run, this would also DM Nolann
        print("\n".join(alerts))
    else:
        log_decision("PULSE", f"{summary}: no notable delta")


# ---------------------------------------------------------------------------
# DAILY PLAN — runs every day 08:00 UTC
# ---------------------------------------------------------------------------

def run_daily_plan():
    """Verify today's schedule, prep Reddit seed if long-form publish day."""
    state_path = ROOT / "shorts" / "shorts_state.json"
    state = json.loads(state_path.read_text())
    today = datetime.now(timezone.utc).date()

    notable = []
    for sh in state["shorts"]:
        publish_dt = datetime.fromisoformat(
            sh["publish_at"].replace("Z", "+00:00"))
        if publish_dt.date() == today:
            notable.append(
                f"📅 TODAY {sh['short_id']} ({sh['yt_id']}) at "
                f"{publish_dt.strftime('%H:%M UTC')} — status: {sh['status']}"
            )

    detail = (f"Today {today} — {len(notable)} Shorts publishing | "
              + " | ".join(notable))
    log_decision("DAILY_PLAN", detail)


# ---------------------------------------------------------------------------
# WEEKLY REVIEW — runs Sunday 18:00 UTC
# ---------------------------------------------------------------------------

def run_weekly_review():
    """Best/worst performer + learnings + plan."""
    csv_path = ROOT / "shorts" / "stats_log.csv"
    if not csv_path.exists():
        log_decision("WEEKLY", "no stats history yet")
        return

    rows = list(csv.DictReader(open(csv_path)))
    timestamps = sorted({r["ts"] for r in rows})
    latest_ts = timestamps[-1]
    week_ago = (datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )).isoformat()
    week_ago_ts = next((t for t in timestamps if t >= week_ago), timestamps[0])

    latest = {r["asset"]: r for r in rows if r["ts"] == latest_ts}
    weekago = {r["asset"]: r for r in rows if r["ts"] == week_ago_ts}

    deltas = []
    for asset, c in latest.items():
        if c["kind"] != "short" or not c["views"]:
            continue
        try:
            cv = int(c["views"])
            pv = int(weekago.get(asset, {}).get("views", 0) or 0)
            deltas.append({"asset": asset, "views": cv, "delta": cv - pv})
        except ValueError:
            continue

    deltas.sort(key=lambda d: d["delta"], reverse=True)
    best = deltas[0] if deltas else None
    worst = deltas[-1] if deltas else None

    report = (
        f"Week ending {latest_ts.split('T')[0]}. "
        f"Best: {best['asset'] if best else 'n/a'} (+{best['delta'] if best else 0}v). "
        f"Worst: {worst['asset'] if worst else 'n/a'} (+{worst['delta'] if worst else 0}v). "
    )
    log_decision("WEEKLY_REVIEW", report)

    # Append to LEARNINGS.md
    learnings = SKILLS / "LEARNINGS.md"
    with learnings.open("a") as f:
        f.write(f"\n## {latest_ts.split('T')[0]} — Auto weekly review\n")
        f.write(f"**Observation**: {report}\n")
        f.write("**Auto-action**: manager reviewed. ")
        f.write("Manual interventions logged separately.\n\n")


# ---------------------------------------------------------------------------
# MONTHLY RECAL — 1st of month 09:00 UTC
# ---------------------------------------------------------------------------

def run_monthly_recal():
    state_path = ROOT / "shorts" / "shorts_state.json"
    state = json.loads(state_path.read_text())
    total_shorts = len(state["shorts"])
    publics = sum(1 for s in state["shorts"] if s["status"] == "PUBLIC")
    detail = (
        f"Monthly recal {datetime.now(timezone.utc).strftime('%Y-%m')}. "
        f"Catalogue: {total_shorts} Shorts ({publics} live). "
        f"Next: assess niche cohesion + catalogue depth target (10+ long-forms)."
    )
    log_decision("MONTHLY_RECAL", detail)


# ---------------------------------------------------------------------------

def main():
    if not sys.argv[1:]:
        print("usage: cron_runner.py {pulse|daily-plan|weekly-review|monthly-recal}")
        sys.exit(1)

    if HALTFILE.exists():
        log_decision("HALT_DETECTED", "skipping run — HALT file present")
        return

    lock = acquire_lock()
    if not lock:
        return

    cmd = sys.argv[1]
    handlers = {
        "pulse": run_pulse,
        "daily-plan": run_daily_plan,
        "weekly-review": run_weekly_review,
        "monthly-recal": run_monthly_recal,
    }
    h = handlers.get(cmd)
    if not h:
        print(f"unknown cmd {cmd}")
        sys.exit(1)
    try:
        h()
    finally:
        lock.close()


if __name__ == "__main__":
    main()
