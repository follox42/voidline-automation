# Voidline KNOWN-BAD library

Validated anti-patterns. NEVER do these.

---

## Visual

- ❌ **Photo archive thumbnails** (sepia Wikimedia historical photos)
  → Confirmed 0% CTR / 24 impressions on v2 long-form. Reads as
    "boring history class".

- ❌ **Centered text on thumbnails**
  → Covers the iconic visual. Use top-left or top-band only.

- ❌ **Pure #FFD700 gold for headlines**
  → Too bright, reads as spam. Use #E0B854 warm gold.

- ❌ **Heavy PIL vignette on AI base images**
  → The AI base already has cinematic vignette. Adding more = Instagram
    filter from 2014.

- ❌ **Brightness <0.85**
  → Crushes image energy. AI base needs 0.92-1.00.

- ❌ **Multi-element thumbs** (face + object + text + arrow + ...)
  → Splits attention. Pick ONE dominant element.

## Hooks

- ❌ **Pure narrative hooks** ("In November 1872, the Mary Celeste...")
  → Viewers skip. v2 HOOK = 4 views with this style.

- ❌ **Date dumps** ("December 5, 1872, at 14:00 UTC, in the North Atlantic...")
  → Too slow. Date should appear visually, not be the spoken hook.

- ❌ **"Today we're going to talk about..."**
  → Wastes the 1.5s scroll-stop window.

- ❌ **Long cold-opens >15s before the question lands**
  → Audience drops by 50% before the hook fires.

## Automation

- ❌ **Studio actions under 3s apart**
  → Triggers YouTube anti-abuse, breaks the dialog state.

- ❌ **Flow generations under 90s apart**
  → Triggers "activité inhabituelle", entire batch fails.

- ❌ **Using Read/Write/Edit/Glob/Grep on the Obsidian vault**
  → MCP guard blocks it. Always use vault_read_note / vault_write_note.

- ❌ **MCP host file paths for camoufox uploads**
  → Container can't see them. Use the in-browser fetch + DataTransfer trick.

- ❌ **Remotion render on Linux**
  → No hardware acceleration → 2h+ render. ffmpeg-only.

## Strategy

- ❌ **Investing in long-form before Shorts have crossed virality threshold**
  → Long-forms get 0v until the algo trusts the channel. Need ~10k Short
    views (within a week of long-form publish) to drag the long-form.

- ❌ **Cadence <1 video / week**
  → Algo can't categorize the channel. Need consistent rhythm.

- ❌ **Mixing topics outside niche**
  → Confuses the co-watch graph. Stick to historical mysteries.

- ❌ **Zero external traffic seed**
  → The channel becomes a black hole. Need Reddit/Discord/X push for
    initial trust signal.

- ❌ **Editing/replacing the video file of an existing YouTube Short**
  → YouTube DOES NOT allow this. Must delete + re-upload + re-schedule.

- ❌ **Reading individual JPG frames as the only visual signal for v2 editor**
  → Use `video-gemini` MCP for actual video understanding.

## Scheduling

- ❌ **Trusting that the schedule was applied without verifying**
  → `schedule_shorts.py` had "day_not_found" silent failures. v3 ANSWER
    published 5 days early.
  → Always read back the publish date from Studio after setting.

- ❌ **Setting time in non-UTC without conversion**
  → Studio uses user's local timezone (Paris UTC+2). What you set as
    "12:00" is 10:00 UTC.

## Communication

- ❌ **Posting YT link in body of Reddit post**
  → Auto-flagged as spam. Always put link in FIRST COMMENT.

- ❌ **Spamming "like and subscribe"**
  → Kills retention metric. The doc niche doesn't tolerate it.

- ❌ **Bait-and-switch titles**
  → Tanks satisfaction metric → algo blacklists the channel.

## 2026-06-13 — Burst mode for cold-start
- ❌ 5+ Shorts in 1 week on a sub-1k channel
- ❌ More than 3 uploads per 7-day window without external trust signal
- ❌ Camoufox upload pattern repeated daily (fingerprint detection)
- ❌ Re-using the same browser session for >10 Studio actions per day

## 2026-06-13 — Recovery actions that don't work
- ❌ Swapping the thumbnail mid-suppression — algo has already de-prioritized
- ❌ Title/description edits — same as above
- ❌ Delete + re-upload — the channel-level flag persists

## 2026-06-14 — Expecting a Short to cross ~300v without comment velocity
- ❌ Confirmed 3× now: v2_twist 297, v1_twist 279, prior v1_twist plateau 274 —
  all went flat, none ever crossed ~300. A strong single hook gets you TO the
  ceiling, not through it. The only untested lever to break it is comment
  velocity (cutter v2 outro debate card) — run that experiment before assuming
  any creative change will push past 300.

## 2026-06-14 — Out-creating an open suppression window
- ❌ Publishing *better* creative into a live suppression window to "rescue" reach.
  Natural experiment (v3 Tunguska, same topic/thumb/cutter): answer pub 06-07 =
  106v; hook pub 06-08 (an S-tier forensic-Q hook + S-tier inverted-scale thumb)
  = 0v; twist pub 06-10 = 26v. View order is the INVERSE of hook quality →
  publish-timing-vs-suppression dominates the creative entirely. The window has a
  sharp ~24h cutoff. When it's open: HALT uploads, do not try to out-create it.
