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

# Allow importing mcp_stealth from the repo root (one level up from shorts/).
_REPO_ROOT = ROOT.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# The anonymous-curl scraper (fetch_stats_curl) is served an anti-scrape /
# consent page in the cloud container, so viewCount is usually absent. When the
# camoufox-stealth MCP is reachable (MCPHUB_TOKEN set) we fetch through the
# authenticated `voidline` browser session instead, which returns the real
# numbers. Body parsing happens here, so only the integers cross the wire.
try:
    import mcp_stealth  # noqa: E402
    _STEALTH_OK = bool(__import__("os").environ.get("MCPHUB_TOKEN"))
except Exception:
    mcp_stealth = None
    _STEALTH_OK = False

_STEALTH_INIT = False


def _stealth_session():
    """Return a live stealth session name, or None if unavailable."""
    global _STEALTH_INIT
    if not _STEALTH_OK or mcp_stealth is None:
        return None
    if not _STEALTH_INIT:
        try:
            mcp_stealth.initialize()
            _STEALTH_INIT = True
        except Exception:
            return None
    return "default"


def fetch_stats_stealth(video_id: str):
    """Fetch viewCount/likeCount via the authenticated stealth session."""
    sess = _stealth_session()
    if not sess:
        return None, None
    try:
        r = mcp_stealth.call("stealth_impersonate_fetch", {
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "from_session": sess, "impersonate": "firefox135",
            "max_body_chars": 0, "timeout": 30,
        })
        content = r["result"]["content"][0]["text"]
        body = json.loads(content).get("body", "")
    except Exception:
        return None, None
    v = re.search(r'"viewCount":"(\d+)"', body)
    l = re.search(r'"likeCount":"(\d+)"', body)
    return (int(v.group(1)) if v else None, int(l.group(1)) if l else None)

LONGFORMS = [
    ("sB8VXu2OHtY", "v1_long_MaryCeleste"),
    ("pM-u_8ONjI0", "v2_long_Dyatlov"),
    ("FacPhS3hNjU", "v3_long_Tunguska"),
]


def fetch_stats_curl(video_id: str, is_short: bool):
    url = f"https://www.youtube.com/shorts/{video_id}" if is_short else f"https://www.youtube.com/watch?v={video_id}"
    try:
        out = subprocess.run(
            ["curl", "-sL", "--max-time", "8", url],
            capture_output=True, text=True, timeout=12,
        ).stdout
    except Exception:
        return None, None
    v = re.search(r'"viewCount":"(\d+)"', out)
    l = re.search(r'"likeCount":"(\d+)"', out)
    return (int(v.group(1)) if v else None, int(l.group(1)) if l else None)


def fetch_stats(video_id: str, is_short: bool):
    """Prefer the authenticated stealth session; fall back to anonymous curl."""
    v, l = fetch_stats_stealth(video_id)
    if v is not None:
        return v, l
    return fetch_stats_curl(video_id, is_short)


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
