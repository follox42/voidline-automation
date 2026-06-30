---
name: long-form-pipeline
description: End-to-end production of a Voidline long-form (script → voice → assets → render → thumb → upload → schedule). 2 routines per week (Tue, Fri publish).
metadata:
  type: skill
---

# Long-form Pipeline

You are the producer of a Voidline long-form. Run the steps in order. Each step writes to `runs/<topic>-<YYYY-MM-DD>/` so the next step can resume.

## Pre-flight

Read `skills/voidline-master/NEXT_VIDEOS.md` → find this run's LONG-1 or LONG-2 entry.
Verify all fields filled (topic, hook, iconic detail, thumb prompt). If TBD remains → abort.

## Step 1 — Script (script-smith)

Generate `script.json` (6 chapters, target 11-13min, ~1250 words):
- ch0: cold-open hook (45-60s, S-tier question hook from idea-forge)
- ch1: setup / context (90-120s)
- ch2: complication / first twist (120-150s)
- ch3: investigation (120-150s)
- ch4: deeper mystery (120-150s)
- ch5: contemporary answer (90-120s)
- ch6: open question for comments (30s)

David Documentary VO style — calm, paced, sentence-level rhythm, no exclamations.

## Step 2 — Voice (ElevenLabs)

Requires env var `ELEVENLABS_KEY`. Voice: David Documentary (voice_id pinned in voidline-master).
Generate one .mp3 per chapter into `runs/<topic>/voice/`.

Cost ~$0.50 per 10min. Skip if `--no-voice` (uses placeholder silence).

## Step 3 — Assets (asset-summoner)

For each chapter, source:
- 4-6 Wikimedia Commons images (license-clear, prefer 1280×720+)
- 1-2 Veo 3.1 cinematic clips OR Flow Nano Banana 2 stills

Save to `runs/<topic>/assets/` with attribution in `assets/ATTRIBUTION.md`.

## Step 4 — Timeline (voidline-editor)

Write `timeline.json` — each entry = (asset, start_s, duration_s, transition).
Cut on beat. Default 4-6s per still, 8-12s per video clip.

## Step 5 — Render (ffmpeg)

`python3 skills/long-form-pipeline/render.py <topic>` → `runs/<topic>/render/voidline.mp4`

Sepia + teal grade, 16:9, 1080p, h264 + AAC.
Add Voidline logo bug (lower-left) + chapter cards at boundaries.

## Step 6 — Thumb

Use the `thumb prompt` from NEXT_VIDEOS.md → Flow Nano Banana 2 (via voidline cookie profile).
Generate 2 candidates → pick highest visual contrast → Fern overlay (gold headline + red arrow):
  `python3 shorts/make_fern_thumb.py <topic>_long <headline> <date>`

## Step 7 — Upload (cross-container bridge)

**CRITICAL — architecture note.** The Cloud Routine sandbox where this pipeline runs has its OWN filesystem; the `camoufox-stealth_upload` MCP tool reads from the MCP server's filesystem (mcphub.nocode18.com). These are different hosts. Bridge them via a public URL on GitHub Releases.

### 7a. Stage the .mp4 to a GitHub Release asset
```
python3 skills/long-form-pipeline/prepare_release.py runs/<topic>
```
This uploads `<topic>/render/final.mp4` (and the thumb) to a GitHub Release tagged `upload-<topic>`, then writes `runs/<topic>/upload_manifest.json` with the public asset URL and metadata.

### 7b. Drive the YT Studio upload via MCP tools (in this exact order)
Read `runs/<topic>/upload_manifest.json` and call the camoufox-stealth tools:

1. `camoufox-stealth_navigate(url="about:blank", cookie_profile="voidline")` — boot the session with voidline cookies loaded
2. `camoufox-stealth_download(url=<asset_url>, path="/tmp/voidline_upload.mp4")` — pulls the .mp4 onto the MCP server's local FS
3. `camoufox-stealth_download(url=<thumb_url>, path="/tmp/voidline_thumb.jpg")` — same for the thumb
4. `camoufox-stealth_navigate(url="https://studio.youtube.com/")`
5. `camoufox-stealth_click(selector="button#create-icon")` then `camoufox-stealth_click(selector="text=Upload videos")`
6. `camoufox-stealth_wait(selector="input[type='file']", timeout=10)`
7. `camoufox-stealth_upload(selector="input[type='file']", file_path="/tmp/voidline_upload.mp4")` — the file already lives on the MCP server's FS now
8. Fill the title input, description textarea, tags chips (use the playbook in `stealth:youtube` skill for selectors)
9. Set the custom thumbnail: `camoufox-stealth_upload(selector="input[type='file'][accept*='image']", file_path="/tmp/voidline_thumb.jpg")`
10. Visibility: PUBLIC + Schedule at `meta.schedule_at` (yields PRIVATE if channel ineligible for scheduling — see failure modes below)
11. Confirm `yt_id` from the share URL after publish flow finishes

### 7c. Cleanup (optional, after schedule confirmed)
```
gh release delete upload-<topic> --repo follox42/voidline-automation --yes
```

### Metadata
- Title format: `{Hook question} ({Year}) — {Iconic detail}`
- Description: standardized template (see `templates/description_long.md`)
- Tags: top 12 from youtube-virality-expert/sub-skills/seo.md
- Schedule: TUE or FRI 17:00 UTC (per NEXT_VIDEOS plan)

## Step 8 — State + Learnings

Append to `agent-log.json`:
```json
{
  "at": "...",
  "type": "long-form-produced",
  "topic": "...",
  "publish_at": "...",
  "video_id": "...",
  "thumb_path": "...",
  "duration": "..."
}
```

Commit + push. Auto-merge action handles the rest.

## Hard limits

- 1 long-form per pipeline run
- Max $2 ElevenLabs cost
- Max 30 Flow generations (anti-abuse)
- Render must complete in < 20 min (else flag and abort)

## Failure modes

- ElevenLabs key missing → produce with silence + log BLOCKER
- Wikimedia unavailable → fallback to Flow-only stills + log
- Flow shows anti-abuse banner → abort + sleep 4h
- Studio upload fails → save .mp4 to runs/<topic>/render/ + log UPLOAD_PENDING
- YT scheduling unavailable (non-monetized / under sub threshold) → upload as PRIVATE, set `status=PRIVATE_AWAITING_PUBLISH` in NEXT_VIDEOS, then the next routine fire flips it to PUBLIC at publish_at via camoufox visibility edit
- GitHub Release asset upload fails (gh CLI not auth'd) → fallback: `curl -F "file=@final.mp4" https://0x0.st` returns a 7-day ephemeral URL; same protocol works with that URL

If 2 consecutive runs fail, escalate via LEARNINGS.md with FAILURE_STREAK tag.
