---
name: niche-intel
description: Monthly deep scan of top-3 niche competitors. Per-channel video/comment/tone analysis. Emits structured actions.json consumed by Idea Lock.
metadata:
  type: skill
---

# Niche Intel v2 — monthly deep recon

## Phases (run in order, 1st of month 09:00 UTC)

### Phase 1 — Self-audit (existing)
Run `cron_runner.py monthly-recal` — catalogue audit, sub-count growth, niche drift check.

### Phase 2 — Competitor radar
`competitor_radar.py` detects top-3 channels in our co-watch graph via incognito browser:
- Open youtube.com/@voidlinedocs/videos in incognito
- Read the YT sidebar recommendations on each video
- Aggregate channel mentions
- Output: `niche_intel/competitors.json` (top-3 with channel_id + URL + scan_date)

Default top-3 candidates (override if niche drifts):
- LEMMiNO (UCRcgy6GzDeccI7dkbbBna3Q)
- Fern (UCODHrzPMGbNv67e84WDZhQQ) — corrected 2026-07: prior ID resolved to Digital Trends, not Fern
- MrBallen (UCtPrkXdtCM5DACLufB9jbsA)

### Phase 3 — Per-channel deep scan
For each of the top-3 channels, `channel_deep_scan.py` collects (via camoufox-stealth):

- Last 8 videos:
  - title, thumb URL, duration, publish date, views, likes, comments count
- Cadence pattern: gap between videos (median, std)
- 90-day evolution: avg duration trend, palette trend on thumbs
- Title patterns: % questions, % dates, avg length

Pacing: ≥45s between channels, ≥10s between video clicks. Randomize order.

Output: `niche_intel/<channel>/scans/YYYY-MM.json`

### Phase 4 — Comments intelligence
For each channel's last 4 videos:
- Top 20 comments by likes
- 30 replies BY THE CHANNEL (their voice/tone sample)

`tone_analyzer.py` analyzes channel replies:
- Avg sentence length
- "we" vs "I" ratio
- Emoji usage rate
- Reply rate (replies / total comments visible)
- Question-back rate (replies that ask viewer something)
- Pin/heart visible pattern

Plus extract **recurring viewer asks** (theory / topic / format requests) — these are content gaps for us.

Output: `niche_intel/<channel>/comments/YYYY-MM.json`

### Phase 5 — Community tab scan
For each channel's community tab:
- Posts in last 30 days
- Format mix (poll / image / text / video)
- Engagement per format (likes, votes if poll)
- Cadence

Output: `niche_intel/<channel>/community/YYYY-MM.json`

### Phase 6 — Cross-reference + actions
`cross_reference.py` diffs all collected data vs our LEARNINGS / KNOWN_GOOD / KNOWN_BAD / progress curve.

Outputs `monthly_intel/YYYY-MM-actions.json`:
```json
{
  "tests": [
    {"id":"T-2607-01", "what":"16min long-form test", "why":"LEMMiNO pivot 11→18 last 90d", "month":"juillet"}
  ],
  "adoptions": [
    {"what":"thumb palette gold+red high contrast", "why":"top 3 channels use this combo on >60% thumbs"}
  ],
  "avoidances": [
    {"what":"emojis in replies", "why":"matches our existing voice rule"}
  ],
  "content_gaps": [
    {"hook":"Did they ever find the bodies?", "frequency":"3 channels / 8 videos", "priority":"high"}
  ],
  "experiments_to_open": [
    {"hypothesis":"16min long-form > 12min on retention", "baseline":"current 44% median"}
  ],
  "blindspots": [
    "No data on Why Files Shorts/Long ratio (skipped if not in top-3)"
  ]
}
```

Plus `monthly_intel/YYYY-MM.md` — human-readable 2-page report.

## Auto-action wiring (user opted full-auto)

Since all actions are auto:
- `experiments_to_open` → immediately invokes `experiment_tracker.py open` (respecting 3-cap)
- `tests` → fed to next Idea Lock as priority topics
- `adoptions` → applied to KNOWN_GOOD.md
- `avoidances` → applied to KNOWN_BAD.md
- `content_gaps` → top of Idea Lock priority queue (above viewer_feedback requests for the month)

## Hard limits per run

- Top-3 channels (not 5) — keeps runtime under 2h
- Pacing: ≥45s between channel switches
- Max 30 Studio/YT page navigations per channel
- If anti-abuse banner → save partial state + abort

## Long-term memory

`niche_intel/<channel>/scans/*.json` accumulates over months. After 6 months:
- Trends per channel (cadence, duration, palette)
- Patterns confirmed on 3+ channels → safe to adopt
- Patterns unique to 1 channel → risky, validate first
