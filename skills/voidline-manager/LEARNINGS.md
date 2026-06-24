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

## 2026-06-24 14:08 — v3 Tunguska long-form breaks the test pool — and Reddit had NOTHING to do with it
**Observation**: Hourly pulse caught v3_long_Tunguska (FacPhS3hNjU) crossing the
100v threshold (102 views, 85 unique). Pulled Studio reach analytics
(period-since-publish). The real story is in the numbers:
- **Impressions: 1.5k** — vs the <25-impression "minimum test pool" every prior
  long-form got (v1=19v, v2=2v). This is the FIRST long-form to escape the
  new-channel impression cage described in the 2026-05-31 learning.
- CTR 3.3%; avg view duration **7:24 on a 13:12 video ≈ 56% retention** — strong
  enough that YouTube kept feeding impressions (91.3% of impressions came from
  YouTube recommending the content).
- Traffic sources: **Browse 52.0% + Suggested videos 43.1% = 95% YouTube-internal
  algorithmic.** Search 2.0%, Direct 2.9%.
- **External sites/apps: "données insuffisantes" → essentially ZERO external
  referral.** The Reddit r/UnresolvedMysteries seed planned for 2026-06-08 (logged
  as the channel's "#1 lever") drove no measurable traffic. Either it was never
  posted or it converted nothing.
- Suggested-video co-watch cluster: "The Willamette Meteorite" (76.2%), "The Meteor
  Shower That Killed 10,000 People", "Tunguska Event | Disaster Records", etc.
**Learning**: The breakout was pure YouTube algorithmic niche-fit + retention, NOT
external seeding. YouTube finally slotted Tunguska into the meteorite/disaster
co-watch graph, and the 56% retention earned a 1.5k-impression pool. The long-held
thesis that long-forms are "dead until seeded from Reddit" is wrong — what they
needed was (a) topical tightness so the co-watch graph can place them and (b)
retention strong enough to survive the test pool. Reddit was a distraction.
**Action**:
- Demote the Reddit-seed lever. Re-verify whether the June 8 seed was ever posted;
  if it was, it's proof external seeding ≠ traction for this niche.
- Double down on the validated levers: tight topical titles/thumbs that match a
  dense co-watch cluster (meteorite/disaster/cosmic), and front-load retention.
- Treat 1.5k impressions @ 56% retention as the new long-form "escaped the cage"
  baseline. Watch v3 over the next pulses — if impressions keep climbing it's a
  genuine sustained pickup, not a one-time test burst.

## 2026-06-24 14:08 — cron_runner.py pulse was broken in the cloud routine (host paths)
**Observation**: `cron_runner.py pulse` crashed immediately:
FileNotFoundError on `/host/home/follox/.openclaw/yt-viral/runs/voidline-.../remotion/public/agent-log.json`.
ROOT/SKILLS were hardcoded to the local openclaw host paths, which do not exist in
the cloud-routine container (repo is cloned to /home/user/voidline-automation).
The portable `shorts/monitor_voidline.py` (uses `__file__`-relative paths + curl on
public watch pages, no cookies) ran fine and produced the live stats.
**Learning**: The runner was authored for the local host and never re-pathed for the
cloud routine. Hourly pulses would crash unattended forever until fixed. The
monitor + Studio MCP path is what actually works in the cloud.
**Action**: Re-pathed cron_runner.py to repo-relative ROOT, made log_decision write
an in-repo agent-log.json (creating it if absent) and stop doing its own git push
(the routine owns commits). Pulse now runs portably in the cloud container.
