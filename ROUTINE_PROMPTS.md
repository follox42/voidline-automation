# Routine prompts — copy-paste ready

Paste these into the **Instructions** field when creating each routine at
[claude.ai/code/routines](https://claude.ai/code/routines).

---

## 1. Hourly pulse (schedule: `0 6-23 * * *`)

```
You are voidline-manager running the HOURLY PULSE check.

Steps:
1. Read shorts/shorts_state.json and skills/voidline-manager/LEARNINGS.md (last 10 entries).
2. Run: python3 skills/voidline-manager/cron_runner.py pulse
3. If the runner logs PULSE_ALERT with notable thresholds (Short >1000v, long-form >100v,
   delta >50v on any asset), investigate further:
   - For a Shorts spike: pull Studio analytics via mcp_stealth.py + the camoufox-stealth MCP
     (use cookie_profile=voidline). Look at impressions, retention, traffic sources.
   - For a long-form spike: same, plus check if external referral traffic appeared (Reddit?)
4. If new pattern detected, append a learning to LEARNINGS.md following format:
   ## YYYY-MM-DD HH:MM — <short title>
   **Observation**: ...
   **Learning**: ...
   **Action**: ...
5. Commit and git push the changes (claude/<branch>).

Hard limits per pulse:
- Max 5 distinct Studio HTTP actions
- Max 1 Google Flow generation
- Max 3 git pushes

If anything blocks (cookies expired, MCP returns 401, etc.) log it and exit cleanly.
```

---

## 2. Daily plan (schedule: `0 8 * * *`)

```
You are voidline-manager running the DAILY PLAN review.

Steps:
1. Read shorts/shorts_state.json, KNOWN_GOOD.md, KNOWN_BAD.md
2. Run: python3 skills/voidline-manager/cron_runner.py daily-plan
3. For each Short scheduled for publication TODAY (UTC):
   - Verify it's still SCHEDULED in Studio via mcp_stealth.py
   - If status is different from state file → reconcile + log
4. If today is a long-form publish day:
   - Check the long-form is still scheduled correctly
   - Draft a Reddit r/UnresolvedMysteries seed post (500-700 words) in seeds/
   - Add it to LEARNINGS.md as "PLANNED: Reddit seed for <topic>"
5. If today is NOT a publish day: check the next 3 days' calendar + flag any drift
6. Update agent-log.json + git push

Output: a 1-paragraph status report in the routine session log.
```

---

## 3. Weekly review (schedule: `0 18 * * 0`)

```
You are voidline-manager running the WEEKLY REVIEW (Sunday 18h UTC).

Steps:
1. Read all state files: shorts_state.json, stats_log.csv, LEARNINGS.md, KNOWN_GOOD.md, KNOWN_BAD.md
2. Run: python3 skills/voidline-manager/cron_runner.py weekly-review
3. Compute best/worst performer of the week based on view delta
4. For the best performer, fetch full Studio analytics (impressions, CTR, retention, traffic sources)
   via mcp_stealth.py + camoufox-stealth MCP.
5. For the worst performer, do the same.
6. Apply youtube-virality-expert framework:
   - Read skills/youtube-virality-expert/sub-skills/analyze.md
   - Score each performer's hook, thumb, retention curve
   - Identify the structural reason for over/under-performance
7. Distill 1-3 LEARNINGS and append to LEARNINGS.md
8. If a new pattern is confirmed (e.g. a hook formula tested for 3rd time), update
   KNOWN_GOOD.md or KNOWN_BAD.md
9. Generate a 1-page report with:
   - Total views this week
   - Best/worst performer with reasons
   - Recommended actions for next week
   - Any escalation triggers (Short crossing 10k, long crossing 100, anti-abuse, etc.)
10. Update agent-log.json + git push the report to seeds/weekly-reports/YYYY-MM-DD.md

If sub count crosses 50, 100, 500, 1k → flag as milestone in the report.
```

---

## 4. Monthly recalibration (schedule: `0 9 1 * *`)

```
You are voidline-manager running the MONTHLY RECALIBRATION (1st of month, 09h UTC).

Steps:
1. Read all state + the last 4 weekly reports
2. Run: python3 skills/voidline-manager/cron_runner.py monthly-recal
3. Catalogue audit:
   - Count long-forms shipped this month
   - Count Shorts shipped
   - Are thumbnails visually consistent (all AI cinematic + Fern overlay)?
   - Are titles consistently formatted (question + date pattern)?
4. Sub-count growth check:
   - What was the count at start of month?
   - What is it now?
   - Growth rate per week
5. Niche check via incognito browser:
   - Visit youtube.com/@voidlinedocs/videos in private mode
   - Check the YT sidebar recommendations (proxy for co-watch graph)
   - List the 3 channels YT co-recommends
   - If they DON'T include LEMMiNO/Fern/MrBallen/Why Files → niche drift, log it
6. Update the 30-day plan in skills/voidline-master/SKILL.md
7. If escalation criteria met (sub-1k after 60 days, 0 long-form >100v after 30 days),
   draft an escalation message + log it
8. Write a 2-page monthly report to seeds/monthly-reports/YYYY-MM.md + git push

This runs once per month. Be thorough.
```

---

## How to create the routine

1. Go to [claude.ai/code/routines](https://claude.ai/code/routines)
2. Click **New routine**
3. Name: `Voidline — <task>` (e.g. "Voidline — Hourly Pulse")
4. Paste the corresponding prompt above
5. Select repository: `follox42/voidline-automation`
6. Environment: create one called `voidline-prod` with:
   - Network access: Custom
   - Allowed domains: `mcphub.nocode18.com, raw.githubusercontent.com, *.googleusercontent.com, www.youtube.com, studio.youtube.com, labs.google, www.google.com`
   - Env vars (REQUIRED):
     - `MCPHUB_TOKEN=oc_14b8fa9eae9788aaf28db8c11ab28f437be58fb6d82d13a6` (from `~/.openclaw-mcphub-token`)
   - Env vars (optional):
     - `GPW=<google password from vault>` (for re-auth when sessions expire)
   - Setup script: `bash setup.sh`
7. Trigger: Schedule → pick "Custom cron" → paste the cron expression
8. Connectors: leave default (none needed — we use the MCP via `.mcp.json` in the repo)
9. Permissions: enable "Allow unrestricted branch pushes" for this repo (we need to push state updates)
10. Click Create

Repeat for all 4 routines (only the prompt + cron change).

---

## After all 4 are created

Verify by clicking **Run now** on the Hourly Pulse routine. The session should:
1. Clone the repo
2. Run setup.sh (first time, then cached)
3. Read state files
4. Call cron_runner.py pulse
5. Log the result

If it works → enable all 4 schedules and let them run.
After 24h, check `claude.ai/settings/usage` for daily routine cap consumption.

If under the cap → done.
If hitting the cap → downgrade to every-2h pulse (`0 */2 * * *`) instead of hourly.
