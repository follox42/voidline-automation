#!/usr/bin/env python3
"""Weekly Intel v2 orchestrator — drives the 7-phase loop.

This script doesn't scrape itself — it emits the structure files + scaffolding,
and the agent in the routine session fills in the data by driving camoufox-stealth.

Usage:
    python3 weekly_runner.py init      # phase 1-2 scaffolds (snapshot dir, dirs)
    python3 weekly_runner.py finalize  # phase 5-7 (curve, self-eval, report)
"""
import csv
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROG = REPO / "progress"
SNAPSHOTS = PROG / "snapshots"
WA = REPO / "weekly_actions"
VF = REPO / "viewer_feedback"
SE = REPO / "self_eval"
REPORTS = REPO / "seeds" / "weekly-reports"
for d in (SNAPSHOTS, WA, VF, SE, REPORTS):
    d.mkdir(parents=True, exist_ok=True)


def iso_week(d: datetime) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def init():
    week = iso_week(datetime.now(timezone.utc))
    snap = SNAPSHOTS / f"{week}.json"
    if not snap.exists():
        snap.write_text(json.dumps({
            "week": week,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "videos": [],
            "channel_aggregates": {}
        }, indent=2))
    actions = WA / f"{week}.md"
    if not actions.exists():
        actions.write_text(f"# Weekly Actions — {week}\n\n> Auto-applied by next week's Production routines.\n\n## Auto-applicable\n\n*(none yet)*\n\n## Structural (also auto since user opted full-auto)\n\n*(none yet)*\n")
    feedback = VF / f"{week}.json"
    if not feedback.exists():
        feedback.write_text(json.dumps({
            "week": week,
            "requests": [],
            "critiques": [],
            "feature_asks": [],
            "praise": []
        }, indent=2))
    print(f"[weekly] scaffolded {week}")


def finalize():
    week = iso_week(datetime.now(timezone.utc))
    snap_path = SNAPSHOTS / f"{week}.json"
    if not snap_path.exists():
        sys.exit("[weekly] no snapshot — run init first")
    snap = json.loads(snap_path.read_text())

    # Phase 5 — curve append
    agg = snap.get("channel_aggregates", {})
    if agg:
        from progress_curve import cmd_append
        cmd_append({
            "total_subs": agg.get("total_subs", ""),
            "subs_gained": agg.get("subs_gained_this_week", ""),
            "total_views": agg.get("views_this_week", ""),
            "videos_pub": agg.get("videos_published_this_week", ""),
            "best_ctr": agg.get("best_ctr_this_week", ""),
            "median_retention": agg.get("median_retention_this_week", ""),
            "hours_watched": agg.get("hours_watched_this_week", ""),
            "shorts_views_total": agg.get("shorts_views_total", ""),
        })

    # Phase 7 — self-eval scaffold (agent fills the body)
    se_path = SE / f"{week}.md"
    if not se_path.exists():
        se_path.write_text(f"""# Self-eval — {week}

> Meta-review. Agent fills in.

## LEARNINGS quality this week
- [ ] All entries backed by ≥ 200 impressions?
- [ ] Any low-confidence claims flagged?

## Experiments status
- [ ] All open experiments still measuring the right thing?
- [ ] Verdicts written for any that hit 14d + 200 impressions?

## Failure modes recurrence
- [ ] Any error hit 2+ times this week → escalate

## Calibration notes
*(agent narrative)*
""")

    # 2-page report scaffold
    report_path = REPORTS / f"{today_str()}.md"
    if not report_path.exists():
        report_path.write_text(f"""# Weekly report — {today_str()} ({week})

## Performance summary (last 30d)
*(agent fills)*

## Best / worst this week
*(agent fills)*

## Experiments status
*(agent fills — link to experiment_tracker status output)*

## CTR / retention diagnostics
*(agent fills — link to weekly_actions/{week}.md)*

## Trajectory
*(agent fills — link to progress_curve eta output)*

## Viewer feedback
*(agent fills — link to viewer_feedback/{week}.json)*

## Meta self-eval
*(agent fills — link to self_eval/{week}.md)*

---

**Auto-actions queued for next week** : see weekly_actions/{week}.md
**Topic queue updated** : viewer_feedback/{week}.json consumed at next Idea Lock
""")

    print(f"[weekly] finalized {week} → {report_path.relative_to(REPO)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "init"
    if cmd == "init":
        init()
    elif cmd == "finalize":
        finalize()
    else:
        sys.exit(f"unknown: {cmd}")
