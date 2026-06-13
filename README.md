# voidline-automation

> Autonomous channel management for [@voidlinedocs](https://www.youtube.com/@voidlinedocs).
> Designed to run as Claude Code [Cloud Routines](https://code.claude.com/docs/en/routines).

## What runs here

Four cron-scheduled routines, each calling `skills/voidline-manager/cron_runner.py`
with a different argument:

| Routine | Schedule (UTC) | Command | What it does |
|---|---|---|---|
| **Hourly pulse** | `0 * * * *` (06-23 hourly) | `pulse` | Fresh YT stats → flag deltas >50v / new sub / Short >1000v / long >100v |
| **Daily plan** | `0 8 * * *` | `daily-plan` | Verify today's scheduled publishes + prep Reddit seed if long-form day |
| **Weekly review** | `0 18 * * 0` | `weekly-review` | Best/worst performer + auto-append learnings + plan next 7 days |
| **Monthly recal** | `0 9 1 * *` | `monthly-recal` | Catalogue audit + niche check + 30-day plan update |

## File map

```
voidline-automation/
├── README.md                       # this file
├── setup.sh                        # Setup Script for the Cloud Routine env
├── .mcp.json                       # Declare camoufox MCP at project scope
├── mcp_stealth.py                  # Direct HTTP client to camoufox-stealth MCP
├── VOIDLINE_THUMB_AI_PROMPT.md     # AI prompt template (Nano Banana 2 + Fern)
├── shorts/
│   ├── shorts_state.json           # Pipeline state truth
│   ├── monitor_voidline.py         # Public stats poll → stats_log.csv
│   ├── schedule_shorts.py          # Auto-schedule via #second-container-expand-button
│   ├── publish_ripe_shorts.py      # Alt: flip Private→Public on date
│   ├── upload_shorts.py            # Batch upload Shorts as PRIVATE
│   ├── short_cutter_v2.py          # The cutter (hook card + outro debate)
│   ├── make_fern_thumb.py          # Fern-template thumb generator
│   └── make_v1style_thumb.py       # Alt thumb template
└── skills/
    ├── voidline-master/            # Channel-specific operator
    ├── youtube-virality-expert/    # Algo + viral judge (channel-agnostic)
    │   ├── SKILL.md
    │   ├── sub-skills/             # 13 imported workflows (hook/thumb/script/...)
    │   ├── references/             # 6 knowledge guides
    │   └── execution/              # YouTube Data API v3 scripts
    └── voidline-manager/           # Orchestrator
        ├── SKILL.md
        ├── LEARNINGS.md            # Append-only learning journal
        ├── KNOWN_GOOD.md           # Validated patterns library
        ├── KNOWN_BAD.md            # Anti-patterns to never repeat
        ├── AUTONOMOUS_LOOP.md      # Cron triggers + safety rails
        └── cron_runner.py          # The script the routines execute
```

## Environment requirements (for Cloud Routines)

The routine environment must have:

### Allowed domains (Custom network access)

- `mcphub.nocode18.com` — **mcphub MCP aggregator** (REQUIRED) — proxies camoufox-stealth, google-flow, plane, obsidian, etc.
- `raw.githubusercontent.com` — for assets fetched into Studio upload via DataTransfer
- `*.googleusercontent.com` — Google Flow CDN for AI image gen results
- `studio.youtube.com` — public scrape if needed
- `www.youtube.com` — public stats scraping
- `labs.google` — Google Flow URL

### Environment variables

REQUIRED:
- `MCPHUB_TOKEN` — bearer token for mcphub. Get from `~/.openclaw-mcphub-token`.

Optional but recommended:
- `GPW` — Google account password (for re-auth when sessions expire) → store in vault
- `YT_API_KEY` — YouTube Data API v3 key (if using `skills/youtube-virality-expert/execution/*.py`)

### Setup script

See `setup.sh` — installs Python deps (Pillow, requests) + ffmpeg. Result is cached.

## Triggering a routine manually (API trigger)

After creating a routine with both Schedule + API triggers:

```bash
curl -X POST https://api.anthropic.com/v1/claude_code/routines/trig_xxx/fire \
  -H "Authorization: Bearer <token>" \
  -H "anthropic-beta: experimental-cc-routine-2026-04-01" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{"text": "Run a custom check"}'
```

## Routine prompt template

Use this as the routine's saved prompt:

```text
You are voidline-manager. Run `python3 skills/voidline-manager/cron_runner.py <TASK>`
where <TASK> is one of: pulse | daily-plan | weekly-review | monthly-recal.

Before running:
1. Read `skills/voidline-manager/SKILL.md`, `KNOWN_GOOD.md`, `KNOWN_BAD.md`, `LEARNINGS.md`
2. Read `shorts/shorts_state.json` for current pipeline state
3. Run the cron_runner.py with the appropriate task
4. If pulse detects an alert (Short crosses 1000v, long-form crosses 100v, etc.),
   investigate via mcp_stealth.py (call camoufox-stealth MCP for Studio details)
5. If new learnings emerge, append to LEARNINGS.md following the format
6. git push the changes back to this repo (the routine has push permission via claude/* branches)

Always log decisions via cron_runner.py — it writes to agent-log.json + git pushes
to the voidline-remotion-preview repo (which the dashboard reads).

If anything blocks (cookie expired, MCP down, etc.) — log + DM Nolann via the
configured channel (Slack/Discord connector if available). Don't silently fail.
```

## Safety rails (built into cron_runner.py)

- **Lockfile** `/tmp/voidline-manager.lock` prevents concurrent runs
- **HALT file** at `shorts/HALT` skips all uploads
- **DRY_RUN env var** `VOIDLINE_DRY_RUN=1` logs without executing
- **Hard limits**: max 5 Studio actions per pulse, max 1 Flow gen per pulse, max 3 git pushes per pulse

## State persistence

State files are written to git on every cron fire:
- `shorts/shorts_state.json` — pipeline truth
- `shorts/stats_log.csv` — every snapshot row
- `skills/voidline-manager/LEARNINGS.md` — append-only

The remotion-preview repo also gets `public/agent-log.json` updates via the
`cron_runner.py` git push.

## Bootstrap on first run

The first routine run will:
1. Clone this repo (Cloud Routine default)
2. Run setup.sh (cached after first time)
3. Initialize empty `stats_log.csv` if missing
4. Run the cron command (pulse / daily-plan / etc.)

## License

Internal — Voidline channel operator only.

`skills/youtube-virality-expert/sub-skills/` and `references/` are derived from
[AgriciDaniel/claude-youtube](https://github.com/AgriciDaniel/claude-youtube) (MIT).
