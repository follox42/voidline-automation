# Voidline LEARNINGS journal

Append-only. Each entry: date, observation, learning, action.

---

## 2026-05-27 — Modal/Remotion render failed
**Observation**: 2h+ render on Modal, Remotion Linux has no HW accel.
**Learning**: Cloud video-render services don't justify their cost/latency
for this scale. ffmpeg local pipeline is faster + cheaper + more reliable.
**Action**: Built `ffmpeg_renderer.py` direct pipeline. All v1/v2/v3 used it.

## 2026-05-31 — v1 long-form goes PUBLIC, ~0 organic views
**Observation**: After 4 days, 2 views, 3 impressions, 0% CTR.
**Learning**: New channels under 1k subs get minimum impression test pool
for long-form. The algo is brutal.
**Action**: Pivoted to Shorts-first strategy.

## 2026-06-01 — Discovery: Shorts schedule UI is HIDDEN, not gone
**Observation**: 3 radios (PRIVATE/UNLISTED/PUBLIC) visible at visibility
step, no "Programmer" radio. Confused this with the trust-tier limitation
for new channels.
**Learning**: For Shorts, the schedule option is behind a separate
`#second-container-expand-button` chevron-down button. Clicking unhides
the `ytcp-visibility-scheduler` widget with the date picker.
**Action**: Built `schedule_shorts.py` using this discovery. 8 Shorts
scheduled successfully on 2026-06-01.

## 2026-06-02 — v1 TWIST Short hits 274v in 48h
**Observation**: First Short to break 200v. Hook = "Captain Morehouse
boards an empty ship in the North Atlantic. December 5, 1872."
**Learning**: Even pure-narrative hooks can do OK if the iconic detail is
strong. But the algo curve plateaued at 274 — never crossed to viral.
**Action**: Note: pure narrative may hit a ceiling around 300v. Need
question hooks to push higher.

## 2026-06-03 — v2 HOOK Short stagnates at 4v
**Observation**: "9 Soviet Hikers Cut Their Tent and Ran Barefoot"
narrative hook — 4 views.
**Learning**: NARRATIVE + ALL CAPS in the first 3s tanks retention.
Viewers skip immediately.
**Action**: All future Short HOOKs must be QUESTIONS or CONTRADICTIONS,
never narrative.

## 2026-06-04 — v2 long-form thumbnail audit
**Observation**: 24 impressions / 0 clicks (0% CTR) with photo archive
sepia thumb featuring "9 GONE" + Dyatlov memorial.
**Learning**: Photo archive thumbnails read "boring history class" and
do not convert on YouTube doc niche. The visual quality is just too low
compared to the AI-generated thumbs that LEMMiNO/Fern use.
**Action**: Pivoted v2 + v3 thumbs to AI cinematic via Google Flow Nano
Banana 2.

## 2026-06-04 — Discovery: Google Flow Nano Banana 2 is the way
**Observation**: Used the `google-flow` skill (replacement of deprecated
`meta-flow-gen`). Nano Banana 2 generates 2 cinematic images per submit,
free tier ~30/mo.
**Learning**: The `voidline` cookie profile already auth'd Flow (same
Google account as YouTube). Image extraction via canvas → toDataURL works
flawlessly. Cost = 0.
**Action**: Updated `voidline-master/SKILL.md` with the full pipeline.

## 2026-06-04 — Flow anti-abuse triggers on rapid actions
**Observation**: Tried to chain v2 then v3 generation back-to-back. Flow
flagged "activité inhabituelle" and failed both v3 attempts.
**Learning**: Flow detects automation patterns. Pacing required: ≥4s
between clicks, ≥6s before submit, ≥90s between generations.
**Action**: Updated `voidline-master/SKILL.md` anti-detect section.

## 2026-06-05 — v2 TWIST Short = first real signal
**Observation**: "Every Dyatlov Pass Theory Failed for 62 Years" question
hook — 298 views + 1 subscriber gained + 67% retention + 48.5% stayed-to-watch.
**Learning**: QUESTION/CONTRADICTION hooks dramatically outperform
narrative hooks for our niche. The +1 sub from a single Short is the first
proof that the format converts to channel growth.
**Action**: All v3 batch re-rendered with question hooks (cutter v2).

## 2026-06-07 — v3 ANSWER publishes 5 days EARLY
**Observation**: Scheduled for 2026-06-12, was live with 106v on 2026-06-07.
**Learning**: schedule_shorts.py had a "day_not_found" error on one of the
v3 schedules, likely Studio defaulted to an earlier date silently. ALWAYS
verify schedule by reading the publish date back from Studio after setting.
**Action**: Need to add a post-condition check in schedule_shorts.py.

## 2026-06-07 — Cutter v2 ships
**Observation**: v3 batch re-rendered with hook card (frame 0-1.5s black +
massive gold question) + outro debate card ("WHAT'S YOUR THEORY? COMMENT
↓") + 1.5-2s caption pacing.
**Learning**: This is the validated formula based on the user's analysis
of v1 TWIST's plateau (57.3% stayed-to-watch needed to reach 70%+).
**Action**: All future Shorts MUST use cutter v2. Cutter v1 is deprecated.

## 2026-06-07 — Weekly review #1
**Observation**: 7 Shorts live, 861 vues total (+107% en 7j), +1 sub confirmé. Long-forms toujours dead.
**Learnings**:
1. Le pivot Shorts marche — Shorts génèrent ~430v/sem maintenant
2. Plafond Short ≈ 300v sans engagement comments — il faut driver comments via outro debate card (cutter v2 le fait)
3. Long-forms restent dépendantes d'un seed externe (Reddit) qu'on n'a JAMAIS testé — c'est le levier #1 à pull
4. Le sub-rate 0.33% sur v2 TWIST = tracking confirmé que les Shorts convertissent même à petite échelle
**Action**: 
- Tester Reddit seed sur v3 Tunguska le 8 juin (premier post organique de l'histoire de la chaîne)
- Re-render v2 HOOK avec question hook (delete + re-upload)
- Produire 2 Shorts bonus sur v1 Mary Celeste (hooks question) pour percer le plafond 279v


## 2026-06-13 — Mcphub aggregator unlock + voidline-automation repo shipped
**Observation**: User flagged that .mcp.json should use mcphub (not direct camoufox URL).
Located mcphub at `https://mcphub.nocode18.com/mcp` + auth token in
`~/.openclaw-mcphub-token` (oc_14b8...). Mcphub exposes **453 tools** including
camoufox-stealth (53), github (32), google-flow, plane, obsidian, openmemory, etc.
Tool naming convention via mcphub: `<server>-<tool>` (e.g. `camoufox-stealth_navigate`
instead of bare `stealth_navigate`).
**Learning**:
1. Mcphub is the right MCP entry point for Cloud Routines — single URL, single auth,
   all servers behind it
2. Direct MCP URLs (mcp-stealth.nocode18.com) work locally but bypass the aggregator
3. Cloud Routine `.mcp.json` MUST use mcphub URL + bearer token in env var
4. Existing scripts using bare tool names (`stealth_navigate`) work UNCHANGED if
   mcp_stealth.py auto-translates via _translate_tool_name()
**Action**: 
- Shipped voidline-automation repo (https://github.com/follox42/voidline-automation)
  with mcphub-aware mcp_stealth.py + ROUTINE_PROMPTS.md ready for claude.ai/code/routines
- 4 Cloud Routines ready to instantiate (hourly pulse / daily / weekly / monthly)
- Verified: stealth_status call via mcphub works (returns the running session info)

## 2026-06-13 — Daily-plan drift catch + cron_runner cloud-fix
**Observation**: First Cloud Routine daily-plan run found two issues.
1. **State drift**: 5 Shorts (v2_twist, v2_answer, v3_hook, v3_twist, v3_answer,
   covering 06-05 → 06-12) were still marked `SCHEDULED` in shorts_state.json
   despite their scheduled times being in the past. Verified all 5 PUBLIC via
   YouTube oEmbed (HTTP 200) and cross-checked the live `voidline` Studio session
   (sitting on 5e8ELVo5ARg `period-since_publish` analytics). Reconciled →
   status=PUBLIC + actual_published_at.
2. **cron_runner.py was hardcoded** to the openclaw host path
   (`/host/home/follox/.openclaw/...`), which does not exist in the Cloud Routine
   container, so step 2 crashed with FileNotFoundError. Patched ROOT/SKILLS to
   auto-detect: host path if present, else resolve relative to the repo. agent-log
   now falls back to `<repo>/agent-log.json`; the remotion auto-push is skipped in
   repo mode (the routine pushes to the feature branch itself).
**Learning**:
- Scheduled Shorts auto-publish silently — the state file is NOT updated by
  YouTube, so daily reconciliation is mandatory (this is the KNOWN_BAD
  "Trusting that the schedule was applied without verifying" pattern, but on the
  *publish* side: trusting the state reflects reality without reading back).
- oEmbed 200/401 is a clean, session-safe public/scheduled probe — cheaper than
  scraping Studio for routine status checks.
**Action**:
- PIPELINE DRY: nothing scheduled past 06-12. Next Short slots (Sun 06-14,
  Mon 06-15) are empty vs the 5/wk cadence. Need to produce + schedule the next
  batch (v4 topic) before the rhythm breaks — flagged in agent-log DRIFT_FLAG.
- Tomorrow (Sun 06-14, 17:00 UTC) is a long-form + Reddit-seed day per cadence;
  verify whether a long-form is actually queued and draft the r/UnresolvedMysteries
  seed then.

## 2026-06-13 14:02 — First cloud pulse: runner had host-path rot + scraper is flaky
**Observation**: First HOURLY PULSE in the Cloud Routine container crashed —
`cron_runner.py` hardcoded `ROOT`/`SKILLS` to `/host/home/follox/.openclaw/...`
and logged to a `remotion/public/agent-log.json` + pushed to a separate repo's
`main`. None of that exists in the fresh cloud checkout (`/host` absent). After
fixing, the pulse ran but `monitor_voidline.py`'s curl scraper returned blank
views for 10/12 assets — only v2_hook (4v) and v3_answer (106v) parsed. The
blanks are YouTube serving a consent/anti-scrape page to unauthenticated curl
in the container. Separately: v3_answer is flat at 106v, unchanged since
2026-06-07 (~6 days no organic growth).
**Learning**:
1. Scripts migrated from the local OpenClaw machine carry absolute `/host/...`
   paths that silently break in the cloud. `monitor_voidline.py` was already
   `Path(__file__)`-relative and survived; `cron_runner.py` (and
   `upload_shorts.py`, still has the hardcoded agent-log path) were not.
2. Anonymous curl to youtube.com is unreliable for stats in the cloud — most
   responses lack `"viewCount"`. Pulse stat coverage will stay sparse until the
   monitor pulls via the camoufox-stealth MCP (cookie_profile=voidline) or yt-dlp.
3. agent-log.json now lives at repo root and is committed by the routine itself,
   not pushed from inside cron_runner.py.
**Action**:
- Made `cron_runner.py` cloud-aware: paths derived from `__file__`, decision
  journal at repo-root `agent-log.json`, removed the dead separate-repo push.
- TODO (not this pulse, keeps within Studio HTTP limits): port
  `monitor_voidline.py` to fetch via camoufox-stealth, and fix the hardcoded
  agent-log path in `upload_shorts.py`.
- No PULSE_ALERT this run (baseline snapshot only); next pulse will have a delta.

## 2026-06-13 — Strategic pivot: pure organic growth (no Reddit seed)
**Observation**: After v3 HOOK 0v + algorithmic suppression confirmed via Studio
analytics (notification not delivered, all traffic sources "insufficient data"),
user decided NOT to pull the Reddit external seed lever. Path forward = pure
organic growth.
**Learning**: 
1. Pure organic for doc-niche cold-start = 3-6 months to first breakout typically.
   We're at J+17 — still very early.
2. The 9-Shorts-in-12-days burst was the trigger for the suppression. Burst mode
   is now OFFICIALLY in KNOWN_BAD for cold-start channels.
3. New durable cadence: 1 long/week + 2 Shorts/week (HOOK + ANSWER, skip TWIST).
   Total 3 uploads/week max during cold-start phase.
4. v3 long-form 0v is now expected behavior under suppression — no panic, just
   wait for cooldown.
**Action**:
- 7-14 day total upload cooldown (J+3 today, target lift J+10 to J+14)
- v4 Roanoke 1590 production during cooldown — polish to max, ship ~20 juin
- Pre-ship gate via youtube-virality-expert score ≥ 75 (hook + thumb + first 5s)
- If v4 long-form still 0v at J+7 post-publish → suppression persistent, downscale
  to v5 minimal (no Shorts batch at all, just long-form)
- DELETE Reddit Tunguska seed from active TODOs


## 2026-06-13 — Strategy re-pivot: full speed, cooldown lifted by user decision
**Observation**: User judgment call — cooldown lifted, resume Shorts production
and full operations.
**Action**:
- All 4 routines to be activated (Hourly Pulse + Daily Plan + Weekly Review + Monthly Recal)
- Shorts production resumes immediately (v1 Mary Celeste bonus Shorts + v4 Roanoke pipeline)
- Pre-ship gate (youtube-virality-expert score ≥75) STILL mandatory — quality bar stays
- Monitor v3 long-form + Shorts views daily — if still 0v at J+10, re-evaluate

## 2026-06-13 — v4 Roanoke production started, Flow blocker hit
**Observation**: Wrote v4 Roanoke script.json (6 chapters, 11:55, 1258 words,
CROATOAN-as-address angle). Tried to generate the AI thumb via Google Flow
Nano Banana 2 — the submit button stays disabled even with a 668-char prompt
properly inserted (verified via DOM inspection). No quota message visible.
**Learning**: Flow UI has changed since 2026-06-04 — model selector pattern
(crop_16_9 + x2 + arrow_forward Créer) is no longer the same. New UI has
"add_2 Créer" button and an Agent mode, but the submit pipeline for image
gen needs re-investigation. Possibly: (1) free tier exhausted for the
month, (2) anti-abuse soft-block from 2026-06-04 burst, or (3) UI
redesign requires new selector path.
**Action**:
- Script + shorts plan + thumb prompt template all committed to repo at
  runs/v4-roanoke/ for resumption
- Next time: open Flow in a fresh session (cookies refresh) and inspect
  the new submit flow
- Backup path: use the v3 Tunguska AI base (forest flattened) as a
  PLACEHOLDER thumb for v4 + iterate after — better to ship with a
  decent base than wait indefinitely

## 2026-06-26 20:08 — Pulse is BLIND: scraper fully dead + impersonate_fetch can't bypass FR consent
**Observation**: First pulse since 2026-06-13 (13-day gap). `monitor_voidline.py`'s
anonymous `curl` now returns the **consent.youtube.com wall** for 100% of assets
(0/13 viewCount parsed, down from 2/13 on 06-13) — verified: a raw curl of the
v3_answer short returns a 1.17MB page with `CONSENT`/`base href=consent.youtube.com`
and no `"viewCount"`. The pulse therefore logged `PULSE: no notable delta`, which is
a **FALSE all-clear** — there is simply no data to compute a delta from. Tested the
06-13 TODO fix path (camoufox-stealth `impersonate_fetch` + `cookie_profile=voidline`):
it ALSO redirects to `consent.youtube.com/m?...&gl=FR` with **`cookies_sent: 0`** —
the profile cookies are not applied to a bare fetch, so impersonate_fetch alone does
NOT solve the consent gate. The ONLY path that worked was driving the live
authenticated Studio browser session (navigate + evaluate on
studio.youtube.com/.../videos): that loaded fully logged-in as Voidline.
**Learning**:
1. The hourly pulse has been a no-op watchdog since at least 06-13 — it cannot detect
   any spike because it has zero view data. Anonymous curl to youtube.com is now
   permanently dead in the cloud container (EU/FR consent enforcement).
2. `impersonate_fetch` + `cookie_profile` is NOT a drop-in fix — the profile cookies
   aren't attached to the fetch (`cookies_sent: 0`) and YouTube serves the FR consent
   gate. The viable monitor port is to drive the persistent authenticated camoufox
   session (the `default` session sits logged into Studio) via navigate→evaluate, OR
   read counts directly off the Studio /videos content list.
3. Long-form Tunguska is flat at **107 views** (was 106 on 06-07) — confirmed dead,
   no spike during the 13-day blind window. Long-forms remain suppressed/dead.
**Action**:
- Logged PULSE_BLIND + DRIFT in agent-log. NO PULSE_ALERT is trustworthy until the
  monitor is ported off curl.
- TODO (next daily-plan or a dedicated fix PR, not this hourly pulse — Studio action
  budget hit): rewrite `monitor_voidline.py` to pull view counts via the authenticated
  camoufox Studio session (navigate to /channel/<id>/videos/{short,upload} then
  evaluate the row cells), NOT curl and NOT impersonate_fetch.

## 2026-06-26 20:08 — State drift: untracked 11th Short live in Studio
**Observation**: Studio `/videos/short` lists **11 Shorts**; `shorts_state.json` tracks
only **10**. The extra row is **"9 Barrels Empty. The Mary Celeste Vapor Theory
#shorts"** — this is the planned v1 Mary Celeste bonus #2 (per the 06-07 weekly plan:
"Produire 2 Shorts bonus sur v1 Mary Celeste"). It rendered with `href: null` (no
`/video/<id>/edit` link, unlike all 10 tracked rows), suggesting it is a DRAFT /
processing / scheduled item rather than a published video. Its yt_id was not captured
(Studio action budget reached).
**Learning**: A Short was produced + uploaded during the 13-day unmonitored window and
never written back to state — same class of drift as the 06-13 RECONCILE (state does
not reflect reality). The pulse is not the right place to reconcile (read-only, action
budget); flag for daily-plan.
**Action**:
- Flagged in agent-log as DRIFT for the next daily-plan to reconcile: capture the
  yt_id + actual status of "9 Barrels Empty" and add it to shorts_state.json (likely
  short_id `v1_bonus_vapor`).
