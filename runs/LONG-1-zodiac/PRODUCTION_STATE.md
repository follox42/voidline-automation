# LONG-1 (The Zodiac Killer — the investigation) — Production State

> Written 2026-07-20 by the long-form-pipeline PRODUCTION routine. This run is PAUSED, not failed.
> LONG-1 for week 2026-W30 (planned Tue 2026-07-21 17:00 UTC publish).

## Status: BLOCKED_AWAITING_QUOTA_AND_AUTH

| Step | Status | Notes |
|---|---|---|
| 0. Variants | ✅ DONE | `variants_used.json` — arm-set per `weekly_plans/2026-W30.md`: hook=**variant** `contradiction_punch`, title=**control** `iconic_question_year`, voice=**control** `david_documentary`. This is the opposite arm-set to LONG-2 (Flight 19), and the one still short a real sample per the plan's arm-set note (line 76-83 of NEXT_VIDEOS.md). |
| 1. Script | ✅ DONE | `script.json` — 7 chapters (ch0–ch6), **8,303 voice chars ≈ 11:00–11:30** at David Documentary pace (est 10:38 @13 cps; real pace lands in the 11–13 min plan window). Press/police-procedural angle per content-gap framing; **no murder-scene reenactment**. Kinetic events + music cues + per-chapter Wikimedia queries annotated. Description + 14 SEO tags written; per-chapter timestamps deferred to render (need real mp3 durations). See `_fact_note_vs_plan` — the plan's "single fingerprint cleared him in 1971" is corrected in-script (overstated; nothing formally cleared Allen). |
| 2. Voice | ⛔ BLOCKED | ElevenLabs Creator quota **121,849 / 121,849 used** (0 chars left vs 8,303 needed), live-confirmed this session via `check_subscription`. `can_extend=false`. **Resets ~2026-07-30 20:41 UTC** (unix 1785444075). Shared account with LONG-2/Hauser backlog — no alternative key. |
| 3. Assets | ⏸ DEFERRED | Per-chapter `wikimedia_queries` embedded in `script.json` — one `fetch_wikimedia_assets.py` pass away at resume. Binaries intentionally not fetched now (gitignored; refetched via manifest at render — same convention as LONG-1-hauser). |
| 4. Timeline | ⏸ DEFERRED | `start_sec`/`end_sec` in script are estimates; real chapter ends come from mp3 durations (ffprobe) once voice exists. |
| 5. Render | ⏸ DEFERRED | Same dependency. No silent render: would waste ffmpeg budget and break EXP-VOICE-001 david arm (thrown away at resume anyway). |
| 6. Thumb | ⛔ BLOCKED | Flow needs `cookie_profile=voidline` — dead since 2026-07-02, `camoufox-stealth_status` → `Not connected` this session (day 18). Prompt + overlay spec saved in `thumb/thumb_config.json`. KNOWN_BAD forbids archival-photo fallback thumbs. |
| 7. Upload | ⛔ BLOCKED | Same dead cookie / connector. An unattended routine session also never takes the Studio click-to-publish step regardless (settled draft-only policy, `skills/community-manager/SKILL.md`, reconfirmed every run). |
| 8. State | ✅ THIS FILE | + LEARNINGS + agent-log + experiments pending_runs (all 3 tagged). |

## Publish slot

- Planned: **Tue 2026-07-21 17:00 UTC** (`script.json.publish_at`) — **will slip** unless both blockers clear before then. Realistic earliest: after quota reset **2026-07-30**, and only once the owner re-logs the voidline cookie. Update `publish_at` at resume.

## Owner actions needed (both owner-only, identical to the Hauser / Ourang backlog)

1. **Interactive re-login to the `voidline` cookie profile** (blocks upload + Flow thumb; open since 2026-07-02, day 18) and **restart the camoufox-stealth MCP connector** (`Not connected`, ~11th consecutive session).
2. **ElevenLabs quota**: wait for the 2026-07-30 reset (NOT authorized to top up / upgrade — new paid spend).

## Resume protocol (any later routine session, once unblocked)

```bash
# 1. Voice (checks quota itself, aborts if still short):
python3 skills/long-form-pipeline/generate_voice.py runs/LONG-1-zodiac
# 2. Assets: fetch_wikimedia_assets.py runs/LONG-1-zodiac (queries in script.json chapters[i].wikimedia_queries),
#    curate to a committed manifest.
# 3. Update chapter start_sec/end_sec from actual mp3 durations (ffprobe) -> timeline.json.
#    Regenerate the description chapter-timestamp block from timeline.json.
# 4. python3 skills/long-form-pipeline/render.py runs/LONG-1-zodiac  (then render_v2.py)
# 5. Thumb: asset_manager.py flow-gen with thumb/thumb_config.json prompt (needs live voidline cookie),
#    then make_fern_thumb overlay ("ONE FINGERPRINT LET HIM WALK").
# 6. Upload per SKILL.md Step 7 (needs live voidline cookie) — human-attended session for the publish click.
# 7. On publish: move experiments/*.json pending_runs[LONG-1-zodiac] -> videos_tagged with the real yt_id.
```

## Experiment arms locked for this run (do not re-pick)

- EXP-HOOK-001  → **variant** `contradiction_punch` ("THEY HAD A SUSPECT. ONE FINGERPRINT LET HIM WALK.")
- EXP-TITLE-001 → **control** `iconic_question_year` ("The Zodiac Killer Investigation (1969–2020): What Did The Police Miss?")
- EXP-VOICE-001 → **control** `david_documentary` (ppLqTilh7rH7fbUVlXsf; eleven_v3 if Creator unlocks it, else eleven_multilingual_v2; stability 0.5 / similarity 0.85 / style 0.2 — read from script.json `_voice_settings`)

## Note on the backlog

Kaspar Hauser (`runs/LONG-1-hauser`), SS Ourang Medan (`runs/LONG-2`), and D.B. Cooper remain PAUSED at the same two owner-only blockers, all waiting on the same cookie + quota clear. This run adds Zodiac to that queue. Producing this script consumes **no** ElevenLabs quota and no Flow generations, so it does not affect any other run's resume path — it only ensures the highest-priority monthly content gap (Zodiac) finally has real committed assets instead of lapsing a third cycle.
