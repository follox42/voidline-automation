#!/usr/bin/env python3
"""Community Tab — posts ONE community-tab item per day (18:00 UTC).

Rotation:
  Mon — behind-scenes (LONG-1 thumb tease)
  Tue — long-form drop card
  Wed — theory poll on LONG-1
  Thu — iconic detail crop
  Fri — long-form drop card
  Sat — tomorrow tease for SUN short
  Sun — reader pick of the week
"""
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STATE_DIR = REPO / "community"
STATE_DIR.mkdir(exist_ok=True)
LOG = STATE_DIR / "community_tab_log.csv"

sys.path.insert(0, str(REPO))

ROTATION = ["behind-scenes", "long-drop", "theory-poll", "detail-crop", "long-drop", "tease-tomorrow", "reader-pick"]


def today_format() -> str:
    wd = datetime.now(timezone.utc).weekday()  # 0 = Mon
    return ROTATION[wd]


def already_posted_today() -> bool:
    if not LOG.exists():
        return False
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return today in LOG.read_text()


def run():
    if already_posted_today():
        print("[community-tab] already posted today — skip")
        return

    fmt = today_format()
    print(f"[community-tab] today's format: {fmt}")

    # Each format would have its own templater. For now, the agent driving this
    # routine session is expected to produce the actual content (image + text)
    # by reading NEXT_VIDEOS.md + recent assets, then posting via camoufox.
    print(f"""[community-tab] PRESCRIPTION for agent:
1. Format = {fmt}
2. Read skills/voidline-master/NEXT_VIDEOS.md to get this week's topics.
3. Construct content per format:
   - behind-scenes: post a single thumb candidate with one-line tease
   - long-drop: image of today's long-form thumb + title + 1-sentence promise
   - theory-poll: 4 options on this week's open question (use the long-form's ch6 question)
   - detail-crop: zoomed crop of past video's iconic asset + 1-line caption
   - tease-tomorrow: "tomorrow we move 700 years earlier" style tease
   - reader-pick: best comment from past 7d (already hearted/pinned) reposted with thanks
4. Navigate to https://studio.youtube.com/channel/UCzbzLj0WW72_mTa86MwzkQQ/community
5. Click "Créer une publication" → choose format → fill → publish
6. Append to community/community_tab_log.csv: date,format,content_summary
""")

    # Append intent (actual post is done by the agent)
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a") as f:
        w = csv.writer(f)
        if LOG.stat().st_size == 0:
            w.writerow(["date", "format", "status"])
        w.writerow([datetime.now(timezone.utc).strftime("%Y-%m-%d"), fmt, "prescribed"])


if __name__ == "__main__":
    run()
