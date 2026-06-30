#!/usr/bin/env python3
"""Generic A/B variant picker for the production routine.

Reads (in priority order):
  1. experiments/*.json with dimension=<D> + verdict=pending → variant_under_test
  2. skills/voidline-manager/KNOWN_GOOD.md → default_<D>: <id>
  3. variants/<D>/<id>.json with `_default: true`

Skips variants present in KNOWN_BAD.md.

Usage:
    python3 pick_variant.py <dimension> [<run_id>]

Where dimension ∈ {titles, voices, thumb_prompts, hooks, caption_styles}.

Stdout: absolute path to chosen variant JSON.
Stderr: structured JSON with picker reasoning + the chosen variant content.

Side-effect (if run_id given):
    Writes/appends runs/<run_id>/variants_used.json with the choice.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VARIANTS_ROOT = REPO / "skills" / "long-form-pipeline" / "variants"
# caption_styles lives outside variants/ for backward compat
CAPTION_STYLES_ROOT = REPO / "skills" / "long-form-pipeline" / "caption_styles"
EXP_ROOT = REPO / "experiments"
KG = REPO / "skills" / "voidline-manager" / "KNOWN_GOOD.md"
KB = REPO / "skills" / "voidline-manager" / "KNOWN_BAD.md"


def variants_dir(dim: str) -> Path:
    if dim == "caption_styles":
        return CAPTION_STYLES_ROOT
    return VARIANTS_ROOT / dim


def list_variants(dim: str) -> dict[str, Path]:
    """{variant_id: path} for all variants of this dimension."""
    d = variants_dir(dim)
    if not d.exists():
        return {}
    return {p.stem: p for p in d.glob("*.json")}


def find_default(dim: str) -> str | None:
    for vid, path in list_variants(dim).items():
        try:
            j = json.loads(path.read_text())
            if j.get("_default") is True or j.get("default") is True:
                return vid
        except Exception:
            continue
    return None


def known_good_default(dim: str) -> str | None:
    if not KG.exists():
        return None
    m = re.search(rf"default_{dim}\s*:\s*([\w_-]+)", KG.read_text())
    return m.group(1) if m else None


def known_bad_set(dim: str) -> set[str]:
    if not KB.exists():
        return set()
    return set(re.findall(rf"{dim}\.([\w_-]+)", KB.read_text()))


def open_experiment_variant(dim: str) -> tuple[str | None, str | None]:
    """Returns (variant_id, experiment_id) for an open experiment on this dim, or (None,None)."""
    if not EXP_ROOT.exists():
        return None, None
    for p in EXP_ROOT.glob("*.json"):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        if d.get("verdict") != "pending":
            continue
        if d.get("dimension") != dim:
            continue
        vut = d.get("variant_under_test")
        if vut:
            return vut, p.stem
    return None, None


def pick(dim: str) -> dict:
    """Returns reasoning + chosen variant path + content."""
    available = list_variants(dim)
    bad = known_bad_set(dim)

    reason_chain = []

    # 1. Open experiment
    exp_vid, exp_id = open_experiment_variant(dim)
    if exp_vid and exp_vid in available and exp_vid not in bad:
        chosen = exp_vid
        reason_chain.append(f"open experiment {exp_id} → {exp_vid}")
    else:
        # 2. KNOWN_GOOD default
        kg_vid = known_good_default(dim)
        if kg_vid and kg_vid in available and kg_vid not in bad:
            chosen = kg_vid
            reason_chain.append(f"KNOWN_GOOD default → {kg_vid}")
        else:
            # 3. _default flag fallback
            df_vid = find_default(dim)
            if df_vid and df_vid in available and df_vid not in bad:
                chosen = df_vid
                reason_chain.append(f"_default flag → {df_vid}")
            elif available:
                # 4. First non-bad available
                chosen = next((v for v in sorted(available) if v not in bad), None)
                if not chosen:
                    raise RuntimeError(f"All variants for {dim} are in KNOWN_BAD")
                reason_chain.append(f"first non-bad available → {chosen}")
            else:
                raise RuntimeError(f"No variants found in {variants_dir(dim)}")

    path = available[chosen]
    content = json.loads(path.read_text())

    return {
        "dimension": dim,
        "chosen": chosen,
        "path": str(path),
        "reason": " | ".join(reason_chain),
        "experiment_id": exp_id if chosen == exp_vid else None,
        "content": content,
        "available": sorted(available),
        "known_bad": sorted(bad),
    }


def tag_run(run_id: str, dim: str, choice: dict):
    """Append the choice to runs/<run_id>/variants_used.json."""
    if not run_id:
        return
    run_dir = REPO / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    tag_path = run_dir / "variants_used.json"

    existing = {}
    if tag_path.exists():
        try:
            existing = json.loads(tag_path.read_text())
        except Exception:
            pass

    existing[dim] = {
        "chosen": choice["chosen"],
        "reason": choice["reason"],
        "experiment_id": choice.get("experiment_id"),
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    tag_path.write_text(json.dumps(existing, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: pick_variant.py <dimension> [<run_id>]")
    dim = sys.argv[1]
    run_id = sys.argv[2] if len(sys.argv) > 2 else None

    choice = pick(dim)
    print(choice["path"])
    if run_id:
        tag_run(run_id, dim, choice)

    info = {k: v for k, v in choice.items() if k != "content"}
    info["content_preview"] = {
        "_id": choice["content"].get("_id"),
        "_description": choice["content"].get("_description", "")[:120],
    }
    print(json.dumps(info, indent=2), file=sys.stderr)
