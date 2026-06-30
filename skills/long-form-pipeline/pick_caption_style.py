#!/usr/bin/env python3
"""Pick the caption style for the next video — autonomous decision.

Logic:
  1. If KNOWN_GOOD.md promotes a style → use it.
  2. Else if any open experiment has `metric` containing "caption" or "retention"
     and `style_under_test` field → use the variant being tested.
  3. Else → fallback `voidline_core.json`.

Used by Production routines before calling generate_captions.py.

Usage:
    python3 pick_caption_style.py
    → prints absolute path to the chosen style JSON
"""
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STYLES = REPO / "skills" / "long-form-pipeline" / "caption_styles"
EXP = REPO / "experiments"
KG = REPO / "skills" / "voidline-manager" / "KNOWN_GOOD.md"
KB = REPO / "skills" / "voidline-manager" / "KNOWN_BAD.md"
DEFAULT = "voidline_core"


def list_available() -> list[str]:
    return sorted(p.stem for p in STYLES.glob("*.json"))


def known_bad_styles() -> set[str]:
    if not KB.exists():
        return set()
    text = KB.read_text()
    return set(re.findall(r"caption_style:\s*([\w_-]+)", text))


def known_good_promoted() -> str | None:
    """If KNOWN_GOOD.md promoted a style, return its name."""
    if not KG.exists():
        return None
    text = KG.read_text()
    # Look for a line like: "caption_style_default: voidline_bold"
    m = re.search(r"caption_style_default:\s*([\w_-]+)", text)
    return m.group(1) if m else None


def open_experiment_style() -> str | None:
    """If an open experiment specifies a style_under_test, return it."""
    if not EXP.exists():
        return None
    for p in EXP.glob("*.json"):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        if d.get("verdict") != "pending":
            continue
        sut = d.get("style_under_test")
        if sut:
            return sut
    return None


def pick() -> Path:
    available = list_available()
    bad = known_bad_styles()

    promoted = known_good_promoted()
    if promoted and promoted in available and promoted not in bad:
        return STYLES / f"{promoted}.json"

    sut = open_experiment_style()
    if sut and sut in available and sut not in bad:
        return STYLES / f"{sut}.json"

    return STYLES / f"{DEFAULT}.json"


if __name__ == "__main__":
    chosen = pick()
    print(str(chosen))
    # also emit human context to stderr so the agent driving the routine sees it
    info = {
        "chosen": chosen.stem,
        "available": list_available(),
        "promoted_in_KNOWN_GOOD": known_good_promoted(),
        "open_experiment_style": open_experiment_style(),
        "known_bad": sorted(known_bad_styles()),
    }
    print(json.dumps(info, indent=2), file=sys.stderr)
