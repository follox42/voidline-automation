# Voidline complete routines — 10 routines total

## Already exists (4 obs)
- Hourly pulse — `trig_019kfLDT8oMRtUf346B3ZNys`
- Daily plan — `trig_012VTd9J2JbfaESjNtvgH3H2`
- Weekly review — `trig_016RpdwDqHvu8Kp3aED1Ptor`
- Monthly recal — `trig_014SVQaDyWLuNFbdddJmkq9G`

## New (6 producers + engagers)

### 1. Idea Lock (Sun 10:00 UTC) — `0 10 * * 0`

```
You are voidline-master + idea-forge running the WEEKLY IDEA LOCK.

Steps:
1. Run: python3 skills/idea-forge/idea_lock_runner.py
   → this emits weekly_plans/YYYY-WW.md with TBD slots
2. For the 2 long-form topics: use niche-radar to surface 5 candidates, then
   youtube-virality-expert/sub-skills/ideate.md to pick #1 + #2.
3. For each long-form, write the S-tier hook question (per hooks-library).
4. For the 3 discovery Shorts: each must be a different decade/region (no clustering).
   Pick from your iconic-detail backlog or generate fresh.
5. Fill ALL TBDs in weekly_plans/YYYY-WW.md.
6. Run: python3 skills/idea-forge/idea_lock_runner.py --lock
   → validates + copies to skills/voidline-master/NEXT_VIDEOS.md
7. Commit + push.

Hard limits: max 5 niche-radar queries, max 2h total runtime.
```

### 2. Production Long-1 (Mon 06:00 UTC) — `0 6 * * 1`

```
You are long-form-pipeline running PRODUCTION for LONG-1 (Tuesday publish).

Read skills/voidline-master/NEXT_VIDEOS.md → LONG-1 entry.
Follow skills/long-form-pipeline/SKILL.md steps 1→8 EXACTLY.

Hard limits: 1 long-form, max $2 ElevenLabs, max 30 Flow generations, max 20min render.
If ELEVENLABS_KEY missing → produce with silence + log BLOCKER + abort step 7 (upload).
```

### 3. Production Long-2 (Thu 06:00 UTC) — `0 6 * * 4`

```
You are long-form-pipeline running PRODUCTION for LONG-2 (Friday publish).

Read skills/voidline-master/NEXT_VIDEOS.md → LONG-2 entry.
Follow skills/long-form-pipeline/SKILL.md steps 1→8 EXACTLY.

Same hard limits as Long-1.
```

### 4. Daily Short (every day 06:00 UTC) — `0 6 * * *`

```
You are daily-short running the DAILY SHORT production.

Steps:
1. Read weekly_plans/YYYY-WW.md → find today's row.
2. If type=HOOK or ANSWER → run python3 skills/daily-short/daily_short_runner.py
3. If type=discovery:
   a. Read the topic + iconic detail from the plan
   b. Render a 60s standalone (script-smith 100-word script + voice + 3 assets)
   c. Use shorts/short_cutter_v2.py with hook + outro cards
   d. Run python3 shorts/make_fern_thumb.py
   e. Run python3 shorts/upload_shorts.py {short_id} {today}T12:00:00Z
4. Update shorts/shorts_state.json.
5. Commit + push.

Hard limits: 1 Short, max 12:00 UTC publish, abort if HALT file present.
```

### 5. Comments Reply (every 2h, 09-23 UTC) — `0 9-23/2 * * *`

```
You are community-manager running the COMMENTS REPLY batch.

Steps:
1. Read community/replied_to.json (dedup) and community/community_log.csv.
2. Run: python3 skills/community-manager/comments_runner.py
   → fetches new comments via camoufox-stealth + Studio inbox
   → classifies + drafts replies in cool docu-narrator voice
3. For each reply emitted, post via camoufox-stealth (manually navigate the inbox UI).
4. Heart the insightful + bait comments (rules in skills/community-manager/SKILL.md).
5. Hide hostile comments.
6. Pin the best-of-day comment (one per day, only if not already pinned today).
7. Commit replied_to.json + community_log.csv.

Hard limits: max 30 replies, max 5 hides, max 1 pin per run.
Voice rules: see skills/community-manager/SKILL.md "Voice rules (HARD)" — never violate.
```

### 6. Community Tab (Daily 18:00 UTC) — `0 18 * * *`

```
You are community-manager running the DAILY COMMUNITY TAB post.

Steps:
1. Run: python3 skills/community-manager/community_tab_runner.py
   → emits today's format prescription
2. Construct the actual content per prescription (image + text).
3. Navigate to https://studio.youtube.com/channel/UCzbzLj0WW72_mTa86MwzkQQ/community
4. Click "Créer une publication" → fill → publish (or schedule for 18:00 if early).
5. Update community/community_tab_log.csv with status=posted.

Hard limits: 1 post per day, never post if already posted (check log).
```
