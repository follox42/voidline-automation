#!/usr/bin/env python3
"""Experiment tracker — opens/closes hypothesis tests.

Hard cap: 3 open experiments at any time.

Usage:
    python3 experiment_tracker.py status               # list open + closed
    python3 experiment_tracker.py open <id> <json>     # create new (errors if 3 open)
    python3 experiment_tracker.py check                # iterate all open, write verdicts
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments"
EXP.mkdir(exist_ok=True)
MAX_OPEN = 3
MIN_AGE_DAYS = 14
MIN_IMPRESSIONS = 200


def open_experiments() -> list[Path]:
    return [p for p in EXP.glob("*.json") if json.loads(p.read_text()).get("verdict") == "pending"]


def cmd_status():
    opens = open_experiments()
    closed = sorted([p for p in EXP.glob("*.json") if json.loads(p.read_text()).get("verdict") != "pending"])
    print(f"OPEN ({len(opens)}/{MAX_OPEN}):")
    for p in opens:
        d = json.loads(p.read_text())
        print(f"  {d['id']}: {d['hypothesis']} (since {d['created']})")
    print(f"\nCLOSED ({len(closed)}):")
    for p in closed[-5:]:
        d = json.loads(p.read_text())
        print(f"  {d['id']}: {d['verdict']} — {d['hypothesis']}")


def cmd_open(exp_id: str, payload: dict):
    opens = open_experiments()
    if len(opens) >= MAX_OPEN:
        print(f"REFUSED — {len(opens)} experiments already open (cap {MAX_OPEN})")
        sys.exit(1)
    payload.setdefault("id", exp_id)
    payload.setdefault("created", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    payload.setdefault("verdict", "pending")
    payload.setdefault("result_7d", None)
    payload.setdefault("result_30d", None)
    (EXP / f"{exp_id}.json").write_text(json.dumps(payload, indent=2))
    print(f"OPENED {exp_id}")


def cmd_check():
    """For each open experiment, assess if enough data accumulated → write verdict."""
    today = datetime.now(timezone.utc).date()
    closed = 0
    for p in open_experiments():
        d = json.loads(p.read_text())
        created = datetime.fromisoformat(d["created"]).date()
        age_days = (today - created).days
        if age_days < MIN_AGE_DAYS:
            print(f"[experiment] {d['id']} — only {age_days}d old (need {MIN_AGE_DAYS})")
            continue
        # The agent driving this routine session is expected to populate
        # `result_30d` (or `result_7d`) before calling --check. Verdict logic:
        result = d.get("result_30d") or d.get("result_7d")
        if result is None or result.get("metric_value") is None:
            print(f"[experiment] {d['id']} — no result yet, agent must populate")
            continue
        baseline = result.get("baseline_value", 0)
        observed = result["metric_value"]
        threshold = result.get("threshold_pct", 10)  # default: 10% delta to flip
        delta_pct = (observed - baseline) / max(abs(baseline), 1e-6) * 100
        if delta_pct >= threshold:
            d["verdict"] = "confirmed"
        elif delta_pct <= -threshold:
            d["verdict"] = "refuted"
        else:
            d["verdict"] = "inconclusive"
        d["closed_at"] = today.isoformat()
        p.write_text(json.dumps(d, indent=2))
        print(f"[experiment] {d['id']} → {d['verdict']} (delta {delta_pct:+.1f}%)")
        closed += 1
    print(f"[experiment] closed {closed} of {len(open_experiments())+closed}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        cmd_status()
    elif sys.argv[1] == "status":
        cmd_status()
    elif sys.argv[1] == "open":
        if len(sys.argv) < 4:
            sys.exit("usage: open <id> <json_payload>")
        cmd_open(sys.argv[2], json.loads(sys.argv[3]))
    elif sys.argv[1] == "check":
        cmd_check()
    else:
        sys.exit(f"unknown cmd: {sys.argv[1]}")
