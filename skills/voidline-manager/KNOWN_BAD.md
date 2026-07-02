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

- ❌ **Assuming Studio's schedule timezone without checking**
  → Directly verified 2026-07-02 (v5-flannan): the account's Studio timezone is
    `(GMT+0000) Heure locale` — no offset needed, "17:00" set = 17:00 UTC. The
    previously-assumed "Paris UTC+2" was never confirmed and is now contradicted by
    direct observation — always check the "Fuseau horaire" selector's current value
    before assuming an offset, don't hardcode one.
- ❌ **Trusting the schedule time field's on-screen value without reading back the
  actual saved schedule**
  → v5-flannan: setting the time input to "17:00" displayed correctly and survived
    navigating through the wizard, but the post-schedule confirmation dialog still
    showed "00:00" — the value silently reverted before submit. Always reopen the
    video after scheduling and read `input.value` directly to confirm, same as the
    existing day-not-found rule below.

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

## Niche avoidances — 2026-07

- **Treating comment-reply silence as evidence that active community replies don't matter** — All 3 top channels (11M, 5M, 8.9M+ subs) run a near-zero comment-reply engagement model and still thrive — but that's survivorship data from channels that were never small, not proof the tactic is neutral for a cold-start channel. Don't use this scan to justify dropping our own active-reply strategy (skills/community-manager/SKILL.md) — see blindspots below.
