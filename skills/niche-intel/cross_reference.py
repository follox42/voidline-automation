#!/usr/bin/env python3
"""Cross-reference niche scan vs our state → emit monthly actions JSON.

Reads:
  - niche_intel/<channel>/scans/YYYY-MM.json (all top-3)
  - niche_intel/<channel>/comments/YYYY-MM.json (all top-3)
  - niche_intel/<channel>/community/YYYY-MM.json (all top-3)
  - skills/voidline-manager/LEARNINGS.md
  - skills/voidline-manager/KNOWN_GOOD.md
  - skills/voidline-manager/KNOWN_BAD.md
  - progress/weekly_curve.csv

Writes:
  - monthly_intel/YYYY-MM-actions.json
  - monthly_intel/YYYY-MM.md (human-readable)

Designed as a scaffold — the agent in the routine fills in the actual
diff narrative. This runner ensures the file structure is consistent and
the auto-action hooks fire correctly.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INTEL = REPO / "monthly_intel"
NICHE = REPO / "niche_intel"
INTEL.mkdir(exist_ok=True)


def yyyy_mm() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def emit_scaffold():
    """Create the empty actions.json + report.md for this month. Agent populates."""
    month = yyyy_mm()
    actions_file = INTEL / f"{month}-actions.json"
    report_file = INTEL / f"{month}.md"

    if actions_file.exists():
        print(f"[niche-intel] {actions_file.name} exists — skip")
    else:
        actions_file.write_text(json.dumps({
            "month": month,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "channels_scanned": [],
            "tests": [],
            "adoptions": [],
            "avoidances": [],
            "content_gaps": [],
            "experiments_to_open": [],
            "blindspots": []
        }, indent=2))
        print(f"[niche-intel] scaffolded {actions_file.name}")

    if report_file.exists():
        print(f"[niche-intel] {report_file.name} exists — skip")
        return
    report_file.write_text(f"""# Niche Intel — {month}

## Channels scanned
*(agent fills — top-3 with their last_scan_date)*

## Per-channel summary
*(for each channel: cadence, format evolution, voice signature, community tab pattern)*

## Cross-reference vs our state
*(agent narrative — what's diff, what's same, what to test)*

## Action plan
See `{actions_file.name}` for machine-readable structure.

### Tests to launch
*(agent lists — derived from competitor patterns we lack data on)*

### Adoptions
*(patterns confirmed across 2+ channels)*

### Avoidances
*(patterns hurting at least one channel)*

### Content gaps
*(viewer asks recurring across channels we haven't covered)*

### Blindspots
*(stuff we couldn't measure this scan)*

---

**Auto-applied immediately** : tests opened in experiments/, adoptions in KNOWN_GOOD.md, avoidances in KNOWN_BAD.md, content_gaps in Idea Lock priority queue.
""")
    print(f"[niche-intel] scaffolded {report_file.name}")


def apply_actions():
    """Read actions.json and apply auto-actions (open experiments, update KNOWN_*)."""
    month = yyyy_mm()
    actions_file = INTEL / f"{month}-actions.json"
    if not actions_file.exists():
        sys.exit("[niche-intel] no actions file for this month")
    data = json.loads(actions_file.read_text())

    # 1. Open experiments (respect 3-cap)
    sys.path.insert(0, str(REPO / "skills" / "weekly-intel"))
    from experiment_tracker import open_experiments, EXP, MAX_OPEN  # noqa
    for exp in data.get("experiments_to_open", []):
        if len(open_experiments()) >= MAX_OPEN:
            print(f"[niche-intel] 3-cap hit, skipping experiment {exp.get('hypothesis')[:40]}")
            break
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
        eid = f"EXP-NICHE-{ts}"
        exp.setdefault("id", eid)
        exp.setdefault("created", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        exp.setdefault("verdict", "pending")
        exp.setdefault("source", "niche-intel")
        (EXP / f"{eid}.json").write_text(json.dumps(exp, indent=2))
        print(f"[niche-intel] opened {eid}")

    # 2. Append adoptions to KNOWN_GOOD.md
    kg = REPO / "skills" / "voidline-manager" / "KNOWN_GOOD.md"
    if data.get("adoptions"):
        with open(kg, "a") as f:
            f.write(f"\n## Niche adoptions — {month}\n\n")
            for a in data["adoptions"]:
                f.write(f"- **{a['what']}** — {a['why']}\n")

    # 3. Append avoidances to KNOWN_BAD.md
    kb = REPO / "skills" / "voidline-manager" / "KNOWN_BAD.md"
    if data.get("avoidances"):
        with open(kb, "a") as f:
            f.write(f"\n## Niche avoidances — {month}\n\n")
            for a in data["avoidances"]:
                f.write(f"- **{a['what']}** — {a['why']}\n")

    print(f"[niche-intel] applied {len(data.get('experiments_to_open', []))} exp + {len(data.get('adoptions', []))} adoptions + {len(data.get('avoidances', []))} avoidances")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scaffold"
    if cmd == "scaffold":
        emit_scaffold()
    elif cmd == "apply":
        apply_actions()
    else:
        sys.exit(f"unknown: {cmd}")
