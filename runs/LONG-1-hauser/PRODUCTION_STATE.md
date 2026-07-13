# LONG-1 (Kaspar Hauser) — Production State

> Written 2026-07-13 by the long-form-pipeline routine. This run is PAUSED, not failed.

## Status: BLOCKED_AWAITING_QUOTA_AND_AUTH

| Step | Status | Notes |
|---|---|---|
| 0. Variants | ✅ DONE | `variants_used.json` — hooks manually overridden to `question_first_8s` (plan-locked EXP-HOOK-001 CONTROL arm per weekly_plans/2026-W29.md; LONG-2/D.B. Cooper carries the variant). Title=numbers_iconic_contradiction, voice=daniel_authoritative — both VARIANT arms per plan. |
| 1. Script | ✅ DONE | `script.json` — 7 chapters (ch0–ch6), 8,941 voice chars ≈ 11:24, kinetic events annotated, description + 12 SEO tags + timestamps written. Corrected the plan's inverted DNA-result detail (see `_fact_note_vs_plan`). |
| 2. Voice | ⛔ BLOCKED | ElevenLabs Creator quota **120,957 / 121,849 used** (892 chars left vs 8,941 needed). `can_extend=false`. **Resets 2026-07-30 ~20:41 UTC** (unix 1785444075). Identical to LONG-2 — shared account, no alternative key. |
| 3. Assets | ✅ DONE | 18 curated Wikimedia stills (manifest + attribution committed; binaries gitignored — refetch via manifest `source` URLs). 28 fetched, 10 junk/duplicate matches pruned after visual review. |
| 4. Timeline | ⏸ DEFERRED | Depends on real voice durations (chapter end_secs come from mp3 lengths). |
| 5. Render | ⏸ DEFERRED | Same dependency. No silent render: would break EXP-VOICE-001 daniel arm and be thrown away anyway (same reasoning as LONG-2). |
| 6. Thumb | ⛔ BLOCKED | Flow needs `cookie_profile=voidline` — dead since 2026-07-02, reconfirmed dead 2026-07-13 via `stealth_auth_check` (`auth_valid=false / status=dead`). Prompt + overlay spec saved in `thumb/thumb_config.json`. KNOWN_BAD forbids archival-photo fallback thumbs. |
| 7. Upload | ⛔ BLOCKED | Same dead cookie. |
| 8. State | ✅ THIS FILE | + LEARNINGS + agent-log + experiments pending_runs (all 3 tagged). |

## Publish slot

- Planned: **Tue 2026-07-14 17:00 UTC** (`script.json.publish_at`) — **will slip** unless BOTH blockers clear before then. Realistic earliest: after quota reset **2026-07-30**, and only once the owner re-logs the voidline cookie. Update `publish_at` at resume.

## Owner actions needed (both owner-only, identical to LONG-2)

1. **Interactive re-login to the `voidline` cookie profile** (blocks upload + Flow thumb; open since 2026-07-02, day 15+).
2. **ElevenLabs quota**: wait for the 2026-07-30 reset, or top up/upgrade (NOT authorized for the routine — new paid spend).

## Resume protocol (any later routine session)

```bash
# 1. Voice (checks quota itself, aborts if still short):
python3 skills/long-form-pipeline/generate_voice.py runs/LONG-1-hauser
# 2. Re-download curated stills (binaries are gitignored):
#    rerun fetch_wikimedia_assets.py runs/LONG-1-hauser (queries are in script.json
#    chapters[i].wikimedia_queries AND runs/LONG-1-hauser/wikimedia_queries.json),
#    then re-apply the curation (manifest.json is the curated truth — 18 kept).
# 3. Update chapter start_sec/end_sec from actual mp3 durations (ffprobe),
#    then write timeline.json.
# 4. python3 skills/long-form-pipeline/render.py runs/LONG-1-hauser
#    python3 skills/long-form-pipeline/render_v2.py runs/LONG-1-hauser
# 5. Thumb: asset_manager.py flow-gen with thumb/thumb_config.json prompt
#    (needs live voidline cookie), then make_fern_thumb overlay.
# 6. Upload per SKILL.md Step 7 (needs live voidline cookie).
# 7. On publish: move experiments/*.json pending_runs[LONG-1-hauser] → videos_tagged
#    with the real yt_id.
```

## Experiment arms locked for this run (do not re-pick)

- EXP-HOOK-001 → **control** `question_first_8s` (plan-lock override; LONG-2 carries the variant)
- EXP-TITLE-001 → **variant** `numbers_iconic_contradiction`
- EXP-VOICE-001 → **variant** `daniel_authoritative` (onwK4e9ZLuTAKqWW03F9, eleven_multilingual_v2, stability 0.45 / similarity 0.9 / style 0.3 — read from script.json `_voice_settings`)

## Note on the two W28 backlog long-forms

LONG-2 (SS Ourang Medan) remains PAUSED at the same two blockers (`runs/LONG-2/PRODUCTION_STATE.md`). Both it and this run resume together once cookie + quota clear. Producing this LONG-1 does not consume any quota, so it does not affect LONG-2's resume path.
