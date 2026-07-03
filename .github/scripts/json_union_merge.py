#!/usr/bin/env python3
"""Custom git merge driver: JSON union.

Merges two JSON files that both append to a top-level array (e.g. agent-log.json's
`decisions`, replied_to.json's `posts`). Deduplicates by a stable key when present.

Usage (called by git per .gitattributes when a conflict is detected):
    json_union_merge.py <base> <ours> <theirs> <marker_size>

Git then reads the output back from <ours>.
"""
import json
import sys
from pathlib import Path


ARRAY_FIELDS_BY_FILE = {
    "agent-log.json": ("decisions", "t"),          # (array_field, dedup_key)
    "replied_to.json": ("posts", "comment_id"),
}


def load(path: str):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return None


def dedup_union(base_arr: list, ours_arr: list, theirs_arr: list, key: str) -> list:
    """Preserve order, drop dupes by key.
    - Start from `ours`, append any new entries from `theirs` in their original order.
    """
    seen = set()
    out = []
    for entry in ours_arr + theirs_arr:
        k = entry.get(key) if isinstance(entry, dict) else None
        if k is None:
            out.append(entry)
            continue
        if k in seen:
            continue
        seen.add(k)
        out.append(entry)
    return out


def main():
    if len(sys.argv) < 4:
        sys.exit("usage: json_union_merge.py <base> <ours> <theirs> [marker_size]")
    base_path, ours_path, theirs_path = sys.argv[1], sys.argv[2], sys.argv[3]

    ours = load(ours_path)
    theirs = load(theirs_path)

    if ours is None or theirs is None:
        # Can't parse — fall back to git's default (which will produce conflict markers)
        sys.exit(1)

    # Detect the file kind by name — check the working tree filename via ours_path.
    # Git passes tmp files, so we look at %P (the pathname) if available in env.
    # Simpler: try each known schema.
    filename = Path(ours_path).name
    handled = False
    for fname, (arr_field, dedup_key) in ARRAY_FIELDS_BY_FILE.items():
        if fname in filename or (isinstance(ours, dict) and arr_field in ours and isinstance(theirs, dict) and arr_field in theirs):
            base = load(base_path) or {}
            ours[arr_field] = dedup_union(base.get(arr_field, []) if isinstance(base, dict) else [],
                                           ours[arr_field],
                                           theirs[arr_field],
                                           dedup_key)
            handled = True
            break

    if not handled:
        # Generic JSON: merge top-level keys, prefer ours on collision
        if isinstance(ours, dict) and isinstance(theirs, dict):
            for k, v in theirs.items():
                if k not in ours:
                    ours[k] = v
                elif isinstance(ours[k], list) and isinstance(v, list):
                    ours[k] = dedup_union([], ours[k], v, "id")

    Path(ours_path).write_text(json.dumps(ours, indent=2, ensure_ascii=False) + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
