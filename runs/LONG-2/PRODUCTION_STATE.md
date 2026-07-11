# LONG-2 (SS Ourang Medan) — Production State

> Written 2026-07-11 by the long-form-pipeline routine. This run is PAUSED, not failed.

## Status: BLOCKED_AWAITING_QUOTA_AND_AUTH

| Step | Status | Notes |
|---|---|---|
| 0. Variants | ✅ DONE | `variants_used.json` — hooks manually overridden to `question_first_8s` (plan-locked EXP-HOOK-001 CONTROL arm) |
| 1. Script | ✅ DONE | `script.json` — 7 chapters, 8,854 voice chars ≈ 11:30, kinetic events annotated |
| 2. Voice | ⛔ BLOCKED | ElevenLabs Creator quota 120,957 / 121,849 used; 892 chars left vs 8,854 needed. `can_extend=false`. **Resets 2026-07-30 ~20:41 UTC.** |
| 3. Assets | ✅ DONE | 17 curated Wikimedia stills (manifest committed; binaries gitignored — refetch via manifest `source` URLs or rerun fetcher). Pack topped up: +9 music/dark, +10 sfx/whoosh (mp3, committed). |
| 4. Timeline | ⏸ DEFERRED | Depends on real voice durations (chapter end_secs come from mp3 lengths) |
| 5. Render | ⏸ DEFERRED | Same dependency. No silent render: would break EXP-VOICE-001 daniel arm and be thrown away anyway |
| 6. Thumb | ⛔ BLOCKED | Flow needs `cookie_profile=voidline` — dead since 2026-07-02, reconfirmed dead 2026-07-11 (day 13). Prompt + overlay spec saved in `thumb/thumb_config.json`. KNOWN_BAD forbids archival-photo fallback thumbs. |
| 7. Upload | ⛔ BLOCKED | Same dead cookie. `stealth_auth_check`: `auth_valid=false / status=dead`. |
| 8. State | ✅ THIS FILE | + LEARNINGS + agent-log + experiments pending_runs |

## Publish slot

- Planned: **Fri 2026-07-10 17:00 UTC — MISSED** (production never ran before this session; cookie dead anyway).
- Rescheduled target in `script.json.publish_at`: **Tue 2026-07-14 17:00 UTC** — will slip again unless BOTH blockers clear before then. Realistic earliest: after quota reset **2026-07-30** unless the owner tops up quota sooner.

## Owner actions needed (both are owner-only)

1. **Interactive re-login to the `voidline` cookie profile** (blocks upload + Flow thumb + all Studio automation; open since 2026-07-02).
2. **ElevenLabs quota**: wait for the 2026-07-30 reset, or top up/upgrade (NOT authorized for the routine — new paid spend).

## Resume protocol (any later routine session)

```bash
# 1. Voice (checks quota itself, aborts if still short):
python3 skills/long-form-pipeline/generate_voice.py runs/LONG-2
# 2. Re-download curated stills (binaries are gitignored):
#    either rerun the fetcher (same queries, then re-curate) or re-download
#    exactly the curated set from assets/manifest.json "source" URLs.
# 3. Update chapter start_sec/end_sec from actual mp3 durations (ffprobe),
#    then write timeline.json (per-chapter slides from assets/manifest.json;
#    build_timeline.py works but check its hardcoded CHAPTER_TITLES first).
# 4. python3 skills/long-form-pipeline/render.py runs/LONG-2
#    python3 skills/long-form-pipeline/render_v2.py runs/LONG-2
# 5. Thumb: asset_manager.py flow-gen with thumb/thumb_config.json prompt
#    (needs live voidline cookie), then make_fern_thumb overlay.
# 6. Upload per SKILL.md Step 7 (needs live voidline cookie).
# 7. On publish: move experiments/*.json pending_runs[LONG-2] → videos_tagged
#    with the real yt_id.
```

## Experiment arms locked for this run (do not re-pick)

- EXP-HOOK-001 → **control** `question_first_8s`
- EXP-TITLE-001 → **variant** `numbers_iconic_contradiction` ("28 Men Died Smiling in 1947. The Ship Was a Ghost.")
- EXP-VOICE-001 → **variant** `daniel_authoritative` (onwK4e9ZLuTAKqWW03F9, eleven_multilingual_v2, stability 0.45 / similarity 0.9 / style 0.3 — generate_voice.py now reads these from script.json `_voice_settings`)
