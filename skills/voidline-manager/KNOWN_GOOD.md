# Voidline KNOWN-GOOD library

Validated patterns. Use these by default.

---

## Hooks (S-tier)

- **Contradiction**: "Every Dyatlov Pass Theory Failed for 62 Years" (299v + 1 sub)
- **Forensic question**: "What Exploded the Sky?" (Tunguska, awaiting publish)
- **Inverted scale**: "1000× Hiroshima. No Crater." (great thumb hook)
- **Time-locked mystery**: "112 Years. We Finally Know What Hit Us."

## Thumbnail recipe

- Base: Google Flow Nano Banana 2 cinematic photo
- Prompt template: `VOIDLINE_THUMB_AI_PROMPT.md`
- Overlay: `shorts/make_fern_thumb.py`
- Headline: gold #E0B854, Impact, 130-150pt, 9-12px stroke, TOP-LEFT
- Date: white Impact, 80-95pt, 5px stroke, below headline
- Arrow: red #D9343F polygon with 6px black border, pointing at iconic detail
- Brightness: 0.92-1.00 (never crush below 0.85)
- NO vignette in PIL (the AI image has cinematic vignette built in)

## Cutter v2 settings (locked)

```json
{
  "hook_duration_s": 1.5,
  "outro_duration_s": 4.0,
  "hook_question": "<MAX 3 LINES question>",
  "outro_question": "WHAT'S YOUR\\nTHEORY?",
  "outro_cta": "COMMENT ↓",
  "mask_until_s": 45  // only if source has baked-in 3-questions overlay
}
```

Caption cadence in body: 1.5-2s per caption. Never longer than 3s.

## YouTube Studio automation

- Auth: `voidline` cookie profile (camoufox stealth-mcp)
- File upload: in-browser fetch from `raw.githubusercontent.com/follox42/voidline-remotion-preview/main/public/` + DataTransfer File trick
- Title input: 1st `[contenteditable=true]` in upload dialog
- Description: 2nd `[contenteditable=true]`
- Not-for-kids radio: `name="VIDEO_MADE_FOR_KIDS_NOT_MFK"`
- 3 × Suivant to reach Visibility
- Schedule (Shorts): `#second-container-expand-button` → date dropdown → time input → "OK" inside popup → "Enregistrer" outside
- Pacing: ≥3s between distinct UI actions; ≥6s for upload submits

## Google Flow Nano Banana 2

- URL: `https://labs.google/fx/fr/tools/flow`
- Cookie profile: `voidline`
- Default model = Nano Banana 2 (image), aspect = `crop_16_9`, count = `x2`
- Prompt input = `[contenteditable=true]`
- Submit = Enter key (cleaner than clicking "arrow_forward Créer")
- Image extraction: canvas.toDataURL("image/jpeg", 0.92) → base64 → save
- Pacing: ≥4s click-to-type, ≥6s before submit, ≥90s between generations

## Cadence

- Long-form: 1 / week (Sundays 17:00 UTC) — until 10+ catalogue
- Shorts: 5 / week (Mon/Wed/Fri/Sun + 1 spare)
- Reddit seed: Sunday 17h UTC, same day as long-form publish

## Posting times (UTC, validated)

- Long-form publish: Sunday 17:00 (peak EU/US overlap)
- Short publish: 12:00 (lunch break for EU + morning US)
- Reddit post: Sunday 17:00 (right after long-form so the post is "fresh")

## Brand colors (locked)

```
GOLD_WARM     = "#E0B854"   // headlines
GOLD_BRIGHT   = "#FFD700"   // accents only, NEVER for headlines
RED_ACCENT    = "#D9343F"   // dates, factual subtitles, arrows
WHITE         = "#FFFFFF"   // body captions
SEPIA_TEAL_GRADE = "brightness 0.92, saturation 0.85, contrast 1.10"
```

## File structure (every run)

```
runs/<run_id>/
├── script.json                  # chapter-by-chapter content
├── timeline.json                 # ffmpeg shot definitions
├── render/voidline_<vN>.mp4      # final long-form
├── shorts/
│   ├── shorts_state.json         # state truth
│   ├── short_<id>.mp4            # rendered Shorts
│   ├── short_cutter_v2.py        # the cutter
│   ├── make_fern_thumb.py        # thumb generator
│   ├── make_v1style_thumb.py     # alt thumb template
│   ├── schedule_shorts.py        # auto-schedule
│   ├── upload_shorts.py          # batch upload
│   └── monitor_voidline.py       # stats poll
├── flow_thumbs/                  # AI-generated thumb bases
└── assets/
    └── thumbnails/               # final thumbs (active + alt variants)
```

## 2026-06-27 — Long-form breakout formula (validated on Tunguska, 111v pure organic)
- **Topic must sit in a high-traffic adjacency lane.** Tunguska broke out because
  95.6% of its traffic was algorithmic (Browse 50.5% + Suggested 45.1%) and its
  #1 suggested source was "The Willamette Meteorite" (70.8%). Cosmic/impact/
  sky-disaster topics inherit audience from large meteorite channels. Pick v4+
  long-form topics that have an obvious big-channel neighbour to be suggested next to.
- **Retention, not CTR, is the unlock.** 55% avg-view-duration (7:14 / 13:12) is
  what kept the algo feeding impressions (1.7k+). CTR was only 3.2%. Optimise the
  edit/pacing for watch-time first, thumbnail CTR second.
- **No external seed needed.** Pure organic broke through at ~J+19. External
  sites = "insufficient data" — Reddit was never pulled. Patience + quality works.
- ❌ Anti-pattern: pure "unexplained mystery" topics with no high-traffic adjacent
  lane (Mary Celeste 19v, Dyatlov 2v) stall in the minimum test pool.

## 2026-06-13 — Recovery cadence (post-suppression)
- ✅ 7-14 day total upload silence to let cooldown lift
- ✅ Long-form ship Sunday 17:00 UTC (peak EU/US)
- ✅ Shorts: HOOK Monday + ANSWER Wednesday (max 2 per release)
- ✅ Pre-ship gate: youtube-virality-expert score ≥ 75 mandatory
- ✅ Catalogue depth target: 10+ long-forms before expecting algo whitelist
