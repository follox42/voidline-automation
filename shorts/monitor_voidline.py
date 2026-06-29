#!/usr/bin/env python3
"""Quick public-stats poll for Voidline channel. Outputs a single line per asset
and appends a snapshot row to stats_log.csv. Flags notable deltas vs last row.
"""
import csv
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
STATE = ROOT / "shorts_state.json"
CSV_LOG = ROOT / "stats_log.csv"

LONGFORMS = [
    ("sB8VXu2OHtY", "v1_long_MaryCeleste"),
    ("pM-u_8ONjI0", "v2_long_Dyatlov"),
    ("FacPhS3hNjU", "v3_long_Tunguska"),
]


# A desktop UA + language + consent cookie makes YouTube serve the full watch/shorts
# page instead of a stripped interstitial. Without these the count fields are absent.
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# YouTube serves the view count in several shapes depending on watch vs shorts and
# logged-in vs out. Try them in order of specificity. (The old single-regex
# `"viewCount":"(\d+)"` only matched the authenticated watch shape and silently
# returned blanks for everything else — that was the cause of the blind pulses.)
_VIEW_PATTERNS = (
    r'"viewCount":"(\d+)"',                                       # authed watch (videoDetails)
    r'videoViewCountRenderer".{0,80}?simpleText":"([\d,]+) views?',  # logged-out watch
    r'"views":\{"simpleText":"([\d,]+) views?"',                  # shorts reel
    r'"accessibilityText":"([\d,]+) views?"',                    # shorts fallback
)


def _extract_views(html: str):
    for pat in _VIEW_PATTERNS:
        m = re.search(pat, html)
        if m:
            return int(m.group(1).replace(",", ""))
    return None


def fetch_stats(video_id: str, is_short: bool):
    url = f"https://www.youtube.com/shorts/{video_id}" if is_short else f"https://www.youtube.com/watch?v={video_id}"
    try:
        out = subprocess.run(
            ["curl", "-sL", "--max-time", "12",
             "-H", f"User-Agent: {_UA}",
             "-H", "Accept-Language: en-US,en;q=0.9",
             "-H", "Cookie: CONSENT=YES+1; SOCS=CAI",
             url],
            capture_output=True, text=True, timeout=15,
        ).stdout
    except Exception:
        return None, None
    v = _extract_views(out)
    l = re.search(r'"likeCount":"(\d+)"', out)
    return (v, int(l.group(1)) if l else None)


def main():
    state = json.loads(STATE.read_text())
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    rows = []
    print(f"\n=== {now} ===")
    print(f"{'asset':<28} {'views':>7} {'likes':>6}")
    for vid_id, name in LONGFORMS:
        v, l = fetch_stats(vid_id, is_short=False)
        print(f"  {name:<26} {(v if v is not None else '—'):>7} {(l if l is not None else '—'):>6}")
        rows.append({"ts": now, "asset": name, "yt_id": vid_id, "kind": "long", "views": v, "likes": l})
    for sh in state["shorts"]:
        v, l = fetch_stats(sh["yt_id"], is_short=True)
        status = sh["status"]
        marker = "" if status == "PUBLIC" else f"[{status}]"
        print(f"  {sh['short_id']:<18}{marker:<10} {(v if v is not None else '—'):>7} {(l if l is not None else '—'):>6}")
        rows.append({"ts": now, "asset": sh["short_id"], "yt_id": sh["yt_id"], "kind": "short", "views": v, "likes": l})

    # Append to CSV log
    new_file = not CSV_LOG.exists()
    with CSV_LOG.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ts", "asset", "yt_id", "kind", "views", "likes"])
        if new_file:
            w.writeheader()
        w.writerows(rows)

    # Show delta vs previous snapshot if available
    if not new_file:
        all_rows = list(csv.DictReader(CSV_LOG.open()))
        # Get the most recent prior snapshot (group by ts)
        ts_list = sorted({r["ts"] for r in all_rows})
        if len(ts_list) >= 2:
            prev_ts, cur_ts = ts_list[-2], ts_list[-1]
            prev = {r["asset"]: r for r in all_rows if r["ts"] == prev_ts}
            cur = {r["asset"]: r for r in all_rows if r["ts"] == cur_ts}
            print(f"\nΔ since {prev_ts.split('T')[1][:5]}:")
            for asset, c in cur.items():
                p = prev.get(asset)
                if not p:
                    continue
                try:
                    dv = int(c["views"]) - int(p["views"])
                except (ValueError, TypeError):
                    dv = "?"
                if dv != 0 and dv != "?":
                    print(f"  {asset}: +{dv}v")


if __name__ == "__main__":
    main()
