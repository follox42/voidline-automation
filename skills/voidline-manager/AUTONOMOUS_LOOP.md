# Voidline Autonomous Loop — 24/7 setup

> The voidline-manager runs continuously in the cloud via scheduled cron
> tasks. This document explains the setup, the triggers, and the
> escalation rules.

## Architecture

```
                  Cloud cron schedule
                         │
            ┌────────────┼────────────┐
            │            │            │
       Hourly pulse  Daily plan  Sunday review
            │            │            │
            └──── voidline-manager ────┘
                         │
                    ┌────┴────┐
                    │         │
            voidline-master   youtube-virality-expert
                    │         │
                    └────┬────┘
                         │
                Persistent journal
                (LEARNINGS.md + stats_log.csv)
                         │
                  Escalation queue
                  (DM Nolann if needed)
```

## The 4 cron triggers

### 1. Hourly pulse (every hour 06:00-23:00 UTC)
```
0 6-23 * * *  voidline-manager pulse
```
**Job**:
- Run `monitor_voidline.py` → fresh stats
- Compare to last hour
- If ANY Short crosses a threshold (50v gain, 1k total, 1 sub) → log + alert
- If ANY long-form crosses 100v → log + alert
- Update `stats_log.csv`

### 2. Daily plan (every day 08:00 UTC)
```
0 8 * * *  voidline-manager daily-plan
```
**Job**:
- Pull yesterday's stats
- Check what's scheduled for today (Shorts auto-publish + long-form publish)
- If a Short is scheduled today: verify it's still ready (file present, schedule valid)
- If today is long-form publish day: prep the Reddit seed draft
- Append daily summary to LEARNINGS.md

### 3. Sunday review (every Sunday 18:00 UTC)
```
0 18 * * 0  voidline-manager weekly-review
```
**Job**:
- Run the full weekly review ritual (best/worst, learnings, plan)
- Generate the report
- Update KNOWN_GOOD.md / KNOWN_BAD.md if any new patterns confirmed
- DM Nolann with the report

### 4. Monthly recal (1st of month, 09:00 UTC)
```
0 9 1 * *  voidline-manager monthly-recal
```
**Job**:
- Audit channel: catalogue depth, niche consistency, thumb style consistency
- Pull subscriber growth curve
- Update the 30-day plan in voidline-master/SKILL.md
- DM Nolann with the recal report

## Escalation triggers (immediate DM to Nolann)

| Trigger | Severity | Action |
|---|---|---|
| Any Short crosses 10k views | 🟢 opportunity | DM "viral candidate" + propose follow-up |
| Any long-form crosses 100v in 24h | 🟢 milestone | DM "algo whitelist warming" |
| Likes/dislikes ratio < 80% | 🟡 risk | DM "bait check needed" |
| YouTube anti-abuse flag (Studio warning) | 🔴 critical | DM immediately, halt all uploads |
| Flow "activité inhabituelle" | 🟡 cooldown | Wait 30min + retry once + DM if persists |
| Voidline cookie expired | 🔴 blocker | DM "need 2FA re-auth" |
| Sub-1k subs after 30 days post-launch | 🟡 strategy | DM "pivot review needed" |
| `shorts_state.json` schedule date mismatch | 🟡 bug | Auto-fix + DM with what was corrected |

## Pre-ship score gate (BEFORE any upload)

Manager calls **`youtube-virality-expert.viral_fit_score(content)`**.

If score < 70 → return to voidline-master for iteration.
Max 5 iterations per asset. If still < 70 after 5 iters → DM Nolann with
the variants + the scores + ask for override decision.

## How to launch

### Option A — Cloud schedule via Anthropic /schedule (recommended)

```bash
/schedule "voidline-manager pulse every hour 06-23 UTC"
/schedule "voidline-manager daily-plan every day at 08:00 UTC"
/schedule "voidline-manager weekly-review every Sunday at 18:00 UTC"
/schedule "voidline-manager monthly-recal on 1st of month at 09:00 UTC"
```

Each becomes a cloud routine. Runs independently of any active session.
Routines persist even when Nolann's laptop is closed.

**Cost estimate**: ~$3-8/month for the 4 routines (Anthropic API
consumption per cron fire × frequency).

### Option B — Server cron (Coolify host)

Set up a cron on the Coolify server that calls a webhook → triggers Claude
Code via headless mode → runs the manager.

Less reliable (depends on local server uptime) but $0 incremental cost.

### Option C — Hybrid (recommended for cost-sensitive)

- Hourly pulse → Coolify cron (cheap, frequent)
- Daily plan → /schedule (reliable)
- Sunday review → /schedule
- Monthly recal → /schedule

## Persistence layer

The manager MUST persist state across runs since each cron fire is a fresh
session with no memory.

State files:
- `runs/voidline-20260527-002843/shorts/shorts_state.json` — pipeline state
- `runs/voidline-20260527-002843/shorts/stats_log.csv` — every snapshot
- `runs/voidline-20260527-002843/remotion/public/agent-log.json` — decisions
- `.openclaw/skills/voidline-manager/LEARNINGS.md` — append-only journal
- `.openclaw/skills/voidline-manager/KNOWN_GOOD.md` — validated patterns
- `.openclaw/skills/voidline-manager/KNOWN_BAD.md` — anti-patterns

On every cron fire, the manager:
1. Reads ALL state files first
2. Pulls fresh data
3. Computes delta
4. Decides + acts
5. Writes back updated state
6. git push the remotion repo (dashboard refresh)

## Safety rails

1. **Hard limit**: max 5 distinct YT Studio actions per hourly pulse
   (anti-abuse on Studio side)
2. **Hard limit**: max 1 Flow generation per pulse (anti-abuse on Flow)
3. **Hard limit**: max 3 git pushes per pulse (rate limit on GitHub)
4. **Lockfile**: only ONE cron job can run at a time (use
   `/tmp/voidline-manager.lock` flock)
5. **Dry-run mode**: set `VOIDLINE_DRY_RUN=1` env var to log actions
   without executing them — for testing
6. **Kill switch**: if `runs/voidline-20260527-002843/HALT` file exists,
   skip all uploads/changes — pulse-only mode

## Next steps

1. ✅ Document architecture (this file)
2. ⏳ Setup the 4 cron schedules via /schedule skill
3. ⏳ Test with `pulse` first (low risk, idempotent)
4. ⏳ Wait 24h for first hourly cycle → debrief
5. ⏳ Enable daily-plan + weekly-review
6. ⏳ Monthly recal at 1 juillet 2026 first fire
