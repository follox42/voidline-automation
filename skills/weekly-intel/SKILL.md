---
name: weekly-intel
description: 7-phase weekly self-analysis loop. Runs Sunday 10:00 UTC, feeds Idea Lock at 14:00.
metadata:
  type: skill
---

# Weekly Intel v2 — closed-loop self-analysis

## Phases (run in order)

### Phase 1 — Performance snapshot (30 days)
For every video published in the last 30 days, pull from YT Studio via camoufox-stealth (voidline cookie):
- impressions, CTR, AVD, retention curve (15s / 30s / 60s / mid / end)
- traffic sources (Home / Suggested / Search / External / Browse / Shorts feed)
- subs gained per video
- view duration distribution

Write to `progress/snapshots/YYYY-WW.json`. Append metrics summary to `progress/weekly_curve.csv`.

### Phase 2 — Best/Worst diagnostic (deepen)
- Best performer: hook decomp, thumb scoring (face/text/contrast), retention checkpoints
- Worst performer: same lens
- Compare hook archetype, thumb style, title pattern, day-of-publish

### Phase 3 — Experiment tracker
Read `experiments/*.json`. For each open experiment:
- Has enough data accumulated? (>= 14d after launch, >= 200 impressions)
- Compute result vs baseline
- Write verdict: `confirmed` → promote learning to `KNOWN_GOOD.md`; `refuted` → `KNOWN_BAD.md`; `inconclusive` → keep open
- Set `result_7d` / `result_30d` fields

Cap: max 3 experiments open at any time. Refuse to open a 4th.

### Phase 4 — CTR/Retention diagnostic + auto-actions
For each video this week, compute deltas vs channel median.
Write `weekly_actions/YYYY-WW.md` with concrete next-week actions:

- **Auto-applicable** (Production routine consumes + applies):
  - audio levels duck/boost
  - timestamps add to description
  - tag updates (top 12 from seo)
  - thumb re-render if CTR < median - 1pt (uses make_fern_thumb with alternative palette)
  - description re-write if drop-off in first 15s

- **Structural fixes** (also auto-applied since user said "tout auto"):
  - voice change for next video (if 3+ critique on voice in viewer_feedback)
  - duration cut/extend (if retention dies at consistent timestamp)
  - format pivot (if 3 consecutive videos under-perform)

### Phase 5 — Progress curve
Append to `progress/weekly_curve.csv`:
```
week, total_subs, subs_gained, total_views, videos_pub, best_ctr, median_retention, hours_watched
```

Write section "Trajectoire" in the weekly report:
- subs growth slope (4-week moving avg)
- retention trend
- best metrics ever
- **ETA milestones** : 100 subs → X weeks, 1k subs → Y weeks, 1k watch-hours (monetization) → Z weeks

### Phase 6 — Viewer feedback mining
For each video this week, via camoufox-stealth on Studio comments tab:
- top 30 comments by likes
- classify into: REQUEST (asking for a topic), CRITIQUE (negative), FEATURE_ASK (UX ask), THEORY (engage), PRAISE (heart-only)

Write `viewer_feedback/YYYY-WW.json` structured for downstream consumption:
```json
{
  "requests": [{"topic":"...", "count":N, "likes_total":N, "ranked": 1}],
  "critiques": [{"issue":"...", "count":N, "severity":"low|mid|high"}],
  "feature_asks": [{"ask":"...", "count":N}]
}
```

Idea Lock (14:00 same day) reads `requests` → priority topic queue.
Production routines read `critiques` → auto-apply fixes per Phase 4 rules.

### Phase 7 — Self-evaluation (meta-review)
Iterate LEARNINGS.md entries created this week:
- Were they based on >= 200 impressions? If not, flag as low-confidence.
- Are open experiments still measuring the right thing?
- Did any failure mode recur this week (e.g. Flow anti-abuse hit 2+) → escalate.

Write `self_eval/YYYY-WW.md` — 1-page meta-review. Confidence calibration.

## Output files (per weekly run)

- `progress/snapshots/YYYY-WW.json` (raw data)
- `progress/weekly_curve.csv` (append row)
- `experiments/*.json` (updated verdicts)
- `weekly_actions/YYYY-WW.md` (next-week action plan)
- `viewer_feedback/YYYY-WW.json` (structured feedback)
- `self_eval/YYYY-WW.md` (meta-review)
- `seeds/weekly-reports/YYYY-MM-DD.md` (human-readable 2-page summary)

## Hard limits per run
- max 30 Studio analytics calls
- max 200 comment fetches
- max 2h total runtime
- max 3 open experiments
