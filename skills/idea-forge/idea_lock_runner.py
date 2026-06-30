#!/usr/bin/env python3
"""Idea Lock — runs every Sunday 10:00 UTC.

Locks the week's content lineup:
  - 2 long-forms (Tuesday + Friday)
  - 7 Shorts (1/day): 4 from the long-forms (HOOK + ANSWER each) + 3 discovery shorts

Writes plan to: weekly_plans/YYYY-WW.md
Updates: skills/voidline-master/NEXT_VIDEOS.md (always reflects the active week)

The agent driving this routine session is expected to fill in the JSON skeleton
emitted by this script with curated topics — this runner just emits the structure
and validates it after the agent writes back.
"""
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLANS = REPO / "weekly_plans"
PLANS.mkdir(exist_ok=True)


def iso_week(d: datetime) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def emit_skeleton():
    now = datetime.now(timezone.utc)
    # Monday of next week
    next_mon = now + timedelta(days=(7 - now.weekday()))
    plan_file = PLANS / f"{iso_week(next_mon)}.md"
    if plan_file.exists():
        print(f"[idea-lock] plan already exists: {plan_file.name}")
        return plan_file

    long_dates = [
        (next_mon + timedelta(days=1)).strftime("%Y-%m-%d"),   # Tuesday
        (next_mon + timedelta(days=4)).strftime("%Y-%m-%d"),   # Friday
    ]
    short_dates = [(next_mon + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    skeleton = f"""# Voidline plan — {iso_week(next_mon)}

> Auto-locked on {now.strftime("%Y-%m-%d %H:%M UTC")}. Agent must fill in the TBD entries.

## Long-forms (2)

### LONG-1 — Tuesday {long_dates[0]}
- topic: TBD
- iconic detail: TBD
- hook question: TBD (S-tier: contradiction / forensic detail / inverted scale / time-locked)
- target duration: 11-13 min
- sources to fetch: Wikimedia + 5 Veo 3.1 clips
- thumb prompt: TBD (Nano Banana 2)

### LONG-2 — Friday {long_dates[1]}
- topic: TBD
- iconic detail: TBD
- hook question: TBD
- target duration: 11-13 min
- sources: Wikimedia + 5 Veo 3.1 clips
- thumb prompt: TBD

## Shorts (7 — 1/day at 12:00 UTC)

| Day | Date | Type | Source | Hook question | Iconic detail |
|---|---|---|---|---|---|
| Mon | {short_dates[0]} | discovery | NEW | TBD | TBD |
| Tue | {short_dates[1]} | HOOK | LONG-1 | TBD | TBD |
| Wed | {short_dates[2]} | ANSWER | LONG-1 | TBD | TBD |
| Thu | {short_dates[3]} | discovery | NEW | TBD | TBD |
| Fri | {short_dates[4]} | HOOK | LONG-2 | TBD | TBD |
| Sat | {short_dates[5]} | ANSWER | LONG-2 | TBD | TBD |
| Sun | {short_dates[6]} | discovery | NEW | TBD | TBD |

## Community-tab schedule

- Mon 18:00 UTC — behind-scenes single image (LONG-1 thumb tease)
- Tue 18:00 UTC — long-form drop card
- Wed 18:00 UTC — theory poll on LONG-1
- Thu 18:00 UTC — iconic detail crop
- Fri 18:00 UTC — long-form drop card
- Sat 18:00 UTC — tomorrow tease for SUN short
- Sun 18:00 UTC — reader pick of the week

## Validation gates

Before this plan locks (agent action):
- [ ] All TBDs filled
- [ ] Hook questions pass S-tier check (use youtube-virality-expert/sub-skills/hook.md)
- [ ] Topics not duplicates of last 3 published long-forms
- [ ] 3 discovery Shorts each have a different decade/region (no clustering)

When all checks pass, agent runs:
  python3 skills/idea-forge/idea_lock_runner.py --lock
"""

    plan_file.write_text(skeleton)
    print(f"[idea-lock] skeleton emitted: {plan_file.name}")
    return plan_file


def lock_plan():
    """Validate the latest week plan file and copy active topics to NEXT_VIDEOS.md."""
    plans = sorted(PLANS.glob("*.md"))
    if not plans:
        print("[idea-lock] no plan files")
        return
    latest = plans[-1]
    content = latest.read_text()
    if "TBD" in content:
        print(f"[idea-lock] FAIL — TBDs remain in {latest.name}")
        sys.exit(1)
    nxt = REPO / "skills/voidline-master/NEXT_VIDEOS.md"
    nxt.write_text(f"# Active week — {latest.name}\n\nSee: {latest.relative_to(REPO)}\n\n---\n\n{content}")
    print(f"[idea-lock] LOCKED → {nxt.relative_to(REPO)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--lock":
        lock_plan()
    else:
        emit_skeleton()
